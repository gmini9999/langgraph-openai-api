# 09. 인증

## 개요

`langgraph-openai-api`의 API Key 기반 Bearer 토큰 인증 방식을 정의합니다.
OpenAI API와 동일한 인증 형식을 사용하여 기존 클라이언트와의 호환성을 보장합니다.

---

## 인증 방식

### Bearer 토큰

모든 API 요청에 `Authorization` 헤더를 포함해야 합니다.

```
Authorization: Bearer <api-key>
```

#### curl 예시

```bash
curl -X POST http://localhost:8000/v1/responses \
  -H "Authorization: Bearer sk-my-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "main-chat", "input": "안녕하세요"}'
```

#### OpenAI SDK 예시

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-my-secret-key",
    base_url="http://localhost:8000/v1",
)

response = client.responses.create(
    model="main-chat",
    input="안녕하세요",
)
```

---

## API Key 설정

### 환경변수

```bash
# .env
OPENLANG_API_KEY=sk-my-secret-api-key
```

| 환경변수 | 설명 | 비고 |
|---------|------|------|
| `OPENLANG_API_KEY` | API 인증 키 | 프로덕션 필수 |

### 다중 API Key

다중 키가 필요한 경우 콤마로 구분합니다.

```bash
OPENLANG_API_KEY=sk-key-1,sk-key-2,sk-key-3
```

---

## FastAPI 미들웨어 구현

### 인증 Dependency

```python
# server/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


def get_api_keys() -> set[str]:
    """설정된 API 키 목록을 반환합니다."""
    keys = os.environ.get("OPENLANG_API_KEY", "")
    return {k.strip() for k in keys.split(",") if k.strip()}


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Bearer 토큰을 검증합니다."""
    api_keys = get_api_keys()

    if not api_keys:
        # API 키가 설정되지 않은 경우 (개발 모드)
        return credentials.credentials

    if credentials.credentials not in api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "message": "Incorrect API key provided.",
                    "type": "authentication_error",
                    "param": None,
                    "code": "invalid_api_key",
                }
            },
        )

    return credentials.credentials
```

### 라우터에 적용

```python
# routers/responses.py

from fastapi import APIRouter, Depends
from ..server.dependencies import verify_api_key

router = APIRouter(dependencies=[Depends(verify_api_key)])

@router.post("/v1/responses")
async def create_response(request: CreateResponseRequest):
    ...
```

---

## 개발 모드

개발 환경에서는 인증을 비활성화할 수 있습니다.

### 설정

```bash
# .env
OPENLANG_DEV=true
```

### 동작

| 모드 | `OPENLANG_DEV` | `OPENLANG_API_KEY` | 인증 동작 |
|------|---------------|-------------------|----------|
| 프로덕션 | `false` | 설정됨 | 인증 필수 |
| 개발 | `true` | 미설정 | 인증 비활성화 |
| 개발 + 키 | `true` | 설정됨 | 인증 비활성화 (키 무시) |
| 프로덕션 + 키 없음 | `false` | 미설정 | 서버 시작 실패 |

### 개발 모드 구현

```python
# server/dependencies.py

import os

def is_dev_mode() -> bool:
    return os.environ.get("OPENLANG_DEV", "false").lower() == "true"


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    if is_dev_mode():
        return credentials.credentials  # 개발 모드: 검증 스킵

    # ... 프로덕션 검증 ...
```

### CLI에서 개발 모드

```bash
# openlang dev 는 자동으로 OPENLANG_DEV=true
openlang dev

# 프로덕션 서빙
openlang serve  # OPENLANG_API_KEY 필수
```

---

## 에러 응답

### 인증 실패 (401)

```json
{
  "error": {
    "message": "Incorrect API key provided: sk-my-k****key.",
    "type": "authentication_error",
    "param": null,
    "code": "invalid_api_key"
  }
}
```

### API 키 누락 (401)

```json
{
  "error": {
    "message": "You didn't provide an API key.",
    "type": "authentication_error",
    "param": null,
    "code": "missing_api_key"
  }
}
```

---

## 보안 권장사항

| 항목 | 권장사항 |
|------|---------|
| 키 길이 | 최소 32자 이상의 랜덤 문자열 |
| 키 형식 | `sk-` 접두사 + 랜덤 문자열 (OpenAI 관례) |
| 환경변수 | `.env` 파일 사용, `.gitignore`에 등록 |
| 키 로테이션 | 정기적으로 키 변경 |
| HTTPS | 프로덕션에서 반드시 HTTPS 사용 |
| 로깅 | API 키를 로그에 출력하지 않음 (마스킹 처리) |

### API Key 생성 예시

```bash
# Python으로 키 생성
python -c "import secrets; print(f'sk-{secrets.token_urlsafe(32)}')"

# openssl로 키 생성
echo "sk-$(openssl rand -base64 32 | tr -d '=/+')"
```

---

## 관련 문서

- [03. 설정](./03-configuration.md) - 환경변수 설정
- [05. API 명세](./05-api-specification.md) - 에러 응답 형식
- [11. 배포](./11-deployment.md) - 프로덕션 보안 체크리스트
- [Appendix A. 환경변수](./appendix/A-environment-variables.md) - 인증 관련 환경변수
