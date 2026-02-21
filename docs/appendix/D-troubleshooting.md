# Appendix D. 트러블슈팅

## 개요

`langgraph-openai-api` 사용 중 발생할 수 있는 일반적인 문제와 해결 방법을 정리합니다.

---

## 서버 시작 문제

### langgraph.json을 찾을 수 없음

**증상:**
```
Error: langgraph.json not found in current directory
Exit code: 2
```

**원인:** 현재 디렉토리에 `langgraph.json`이 없음

**해결:**
```bash
# 현재 디렉토리 확인
ls langgraph.json

# 경로 지정
openlang dev --config /path/to/langgraph.json
```

---

### 그래프 모듈 import 실패

**증상:**
```
Error: Failed to import graph module: ./src/agents/main_chat/graph.py
ImportError: No module named 'langchain_openai'
Exit code: 3
```

**원인:** 그래프가 의존하는 패키지가 설치되지 않음

**해결:**
```bash
# 의존성 설치
pip install -e .

# 또는 개별 패키지 설치
pip install langchain-openai
```

---

### 그래프 변수를 찾을 수 없음

**증상:**
```
Error: Variable 'graph' not found in module ./graph.py
Exit code: 3
```

**원인:** `langgraph.json`에서 지정한 변수명이 모듈에 존재하지 않음

**해결:**
1. `langgraph.json`의 경로 확인: `"my-graph": "./graph.py:graph"`
2. `graph.py`에 `graph` 변수가 정의되어 있는지 확인:
   ```python
   graph = builder.compile()  # 이 변수가 존재해야 함
   ```

---

### API 키 미설정 (serve 모드)

**증상:**
```
Error: OPENLANG_API_KEY is required in production mode
Exit code: 4
```

**원인:** `openlang serve`에서 `OPENLANG_API_KEY` 환경변수가 없음

**해결:**
```bash
# 환경변수 설정
export OPENLANG_API_KEY=sk-your-api-key

# 또는 .env 파일에 추가
echo "OPENLANG_API_KEY=sk-your-api-key" >> .env
```

---

## API 호출 문제

### 401 Unauthorized

**증상:**
```json
{
  "error": {
    "message": "Incorrect API key provided.",
    "type": "authentication_error",
    "code": "invalid_api_key"
  }
}
```

**원인:** 잘못된 API 키

**해결:**
```bash
# API 키 확인
echo $OPENLANG_API_KEY

# 요청에 올바른 키 사용
curl -H "Authorization: Bearer sk-correct-key" http://localhost:8000/v1/models

# 개발 모드 사용 (인증 비활성화)
openlang dev
```

---

### 404 model_not_found

**증상:**
```json
{
  "error": {
    "message": "The model 'my-model' does not exist",
    "type": "invalid_request_error",
    "code": "model_not_found"
  }
}
```

**원인:** 요청한 `model`이 `langgraph.json`에 등록되지 않음

**해결:**
```bash
# 등록된 모델 확인
curl http://localhost:8000/v1/models

# langgraph.json의 graphs 필드 확인
cat langgraph.json | python -m json.tool
```

---

### 스트리밍이 한 번에 전송됨

**증상:** `stream: true`로 요청했지만 응답이 한 번에 도착

**원인:**
1. 리버스 프록시(Nginx 등)의 버퍼링이 활성화됨
2. 미들웨어가 응답을 버퍼링함

**해결:**

Nginx 설정 추가:
```nginx
proxy_buffering off;
proxy_cache off;
chunked_transfer_encoding off;
```

또는 직접 서버에 연결하여 테스트:
```bash
curl -N http://localhost:8000/v1/responses \
  -H "Content-Type: application/json" \
  -d '{"model": "main-chat", "input": "hello", "stream": true}'
```

---

### 500 Internal Server Error

**증상:**
```json
{
  "error": {
    "message": "Internal server error",
    "type": "server_error"
  }
}
```

**원인:** 그래프 실행 중 예외 발생

**해결:**
1. 서버 로그 확인:
   ```bash
   openlang dev --log-level debug
   ```
2. 그래프를 독립적으로 테스트:
   ```python
   from graph import graph
   result = graph.invoke({"messages": [HumanMessage(content="test")]})
   ```
3. LLM API 키 확인:
   ```bash
   echo $OPENAI_API_KEY
   ```

---

## OpenAI SDK 호환 문제

### base_url 설정 오류

**증상:**
```
openai.NotFoundError: Error code: 404
```

**원인:** `base_url`에 `/v1`이 누락되었거나 중복됨

**해결:**
```python
# 올바른 설정
client = OpenAI(
    api_key="...",
    base_url="http://localhost:8000/v1",  # /v1 포함
)

# 잘못된 설정
# base_url="http://localhost:8000"      # /v1 누락
# base_url="http://localhost:8000/v1/"  # 후행 슬래시 주의
```

---

### SDK 버전 호환

**증상:**
```
AttributeError: 'OpenAI' object has no attribute 'responses'
```

**원인:** OpenAI SDK 버전이 Responses API를 지원하지 않음

**해결:**
```bash
# 최신 SDK 설치
pip install --upgrade openai

# 버전 확인 (1.66.0 이상 필요)
python -c "import openai; print(openai.__version__)"
```

---

## Docker 문제

### 포트 충돌

**증상:**
```
Error: address already in use: 0.0.0.0:8000
```

**해결:**
```bash
# 포트 사용 중인 프로세스 확인
lsof -i :8000

# 다른 포트 사용
docker run -p 8001:8000 my-langgraph-api
```

---

### 환경변수 미전달

**증상:** Docker 컨테이너에서 LLM API 호출 실패

**해결:**
```bash
# 환경변수 전달
docker run -e OPENAI_API_KEY=sk-... my-langgraph-api

# env 파일 사용
docker run --env-file .env my-langgraph-api
```

---

## 성능 문제

### 첫 요청이 느림

**원인:** 그래프 모듈 lazy loading, LLM 모델 초기화

**해결:** 서버 시작 후 워밍업 요청 전송:
```bash
curl -X POST http://localhost:8000/v1/responses \
  -H "Content-Type: application/json" \
  -d '{"model": "main-chat", "input": "warmup"}'
```

---

### 동시 요청 처리 부족

**원인:** 워커 수가 1개로 설정됨

**해결:**
```bash
openlang serve --workers 4
```

---

## 관련 문서

- [02. 빠른 시작](../02-quick-start.md) - 기본 설정
- [03. 설정](../03-configuration.md) - 설정 상세
- [09. 인증](../09-authentication.md) - 인증 문제
- [11. 배포](../11-deployment.md) - 배포 문제
