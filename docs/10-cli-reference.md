# 10. CLI 레퍼런스

## 개요

`openlang` CLI 도구의 명령어, 옵션, 사용 예제를 정의합니다.
`openlang`은 `langgraph-openai-api` 패키지와 함께 설치됩니다.

---

## 설치

```bash
pip install langgraph-openai-api
```

설치 후 `openlang` 명령어를 사용할 수 있습니다.

```bash
openlang --version
# langgraph-openai-api 0.1.0

openlang --help
```

---

## 명령어 요약

| 명령어 | 설명 | 주 용도 |
|--------|------|--------|
| `openlang dev` | 개발 서버 실행 | 로컬 개발 |
| `openlang build` | Docker 이미지 빌드 | 배포 준비 |
| `openlang serve` | 프로덕션 서버 실행 | 프로덕션 |

---

## openlang dev

개발용 서버를 실행합니다. 핫 리로드가 활성화되고, 인증이 비활성화됩니다.

### 사용법

```bash
openlang dev [OPTIONS]
```

### 옵션

| 옵션 | 단축 | 타입 | 기본값 | 설명 |
|------|------|------|--------|------|
| `--host` | `-h` | string | `127.0.0.1` | 바인드 호스트 |
| `--port` | `-p` | int | `8000` | 바인드 포트 |
| `--config` | `-c` | path | `./langgraph.json` | 설정 파일 경로 |
| `--reload` | | flag | `true` | 코드 변경 시 자동 리로드 |
| `--no-reload` | | flag | `false` | 리로드 비활성화 |
| `--log-level` | | string | `debug` | 로그 레벨 |

### 예시

```bash
# 기본 실행
openlang dev

# 포트 변경
openlang dev --port 3000

# 커스텀 설정 파일
openlang dev --config ./config/langgraph.json

# 리로드 비활성화
openlang dev --no-reload
```

### 동작

1. `langgraph.json` 로딩
2. 그래프 모듈 import 및 등록
3. `OPENLANG_DEV=true` 설정 (인증 비활성화)
4. Uvicorn 개발 서버 시작 (리로드 활성화)
5. `http://{host}:{port}/docs` 에서 Swagger UI 확인 가능

### 출력 예시

```
🚀 openlang dev server starting...
📋 Config: ./langgraph.json
📦 Graphs loaded:
  - main-chat     → ./src/agents/main_chat/graph.py:graph
  - rag-agent     → ./src/agents/rag/graph.py:graph

🌐 Server: http://127.0.0.1:8000
📖 Docs:   http://127.0.0.1:8000/docs
🔓 Auth:   disabled (dev mode)

INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process
```

---

## openlang build

Docker 이미지를 빌드합니다.

### 사용법

```bash
openlang build [OPTIONS]
```

### 옵션

| 옵션 | 단축 | 타입 | 기본값 | 설명 |
|------|------|------|--------|------|
| `--tag` | `-t` | string | `langgraph-api:latest` | 이미지 태그 |
| `--config` | `-c` | path | `./langgraph.json` | 설정 파일 경로 |
| `--platform` | | string | — | 타겟 플랫폼 (`linux/amd64`, `linux/arm64`) |
| `--no-cache` | | flag | `false` | 빌드 캐시 미사용 |

### 예시

```bash
# 기본 빌드
openlang build

# 커스텀 태그
openlang build -t my-api:v1.0

# 멀티 플랫폼
openlang build --platform linux/amd64
```

### 동작

1. `langgraph.json`과 프로젝트 파일 수집
2. Dockerfile 생성 (임시)
3. `docker build` 실행
4. 이미지 생성 완료

### 생성되는 Dockerfile 구조

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# 프로젝트 파일 복사
COPY . .

# langgraph-openai-api 설치
RUN pip install langgraph-openai-api

# 서버 실행
CMD ["openlang", "serve"]
```

---

## openlang serve

프로덕션 서버를 실행합니다. 인증이 활성화되고, 최적화된 설정으로 실행됩니다.

### 사용법

```bash
openlang serve [OPTIONS]
```

### 옵션

| 옵션 | 단축 | 타입 | 기본값 | 설명 |
|------|------|------|--------|------|
| `--host` | `-h` | string | `0.0.0.0` | 바인드 호스트 |
| `--port` | `-p` | int | `8000` | 바인드 포트 |
| `--config` | `-c` | path | `./langgraph.json` | 설정 파일 경로 |
| `--workers` | `-w` | int | `1` | 워커 프로세스 수 |
| `--log-level` | | string | `info` | 로그 레벨 |

### 예시

```bash
# 기본 실행 (API 키 필수)
OPENLANG_API_KEY=sk-... openlang serve

# 멀티 워커
openlang serve --workers 4

# 커스텀 포트
openlang serve --port 80 --host 0.0.0.0
```

### 동작

1. `OPENLANG_API_KEY` 환경변수 확인 (없으면 에러)
2. `langgraph.json` 로딩
3. 그래프 모듈 import 및 등록
4. Uvicorn 프로덕션 서버 시작 (리로드 비활성화)

### dev vs serve 비교

| 항목 | `openlang dev` | `openlang serve` |
|------|----------------|------------------|
| 인증 | 비활성화 | 활성화 (API 키 필수) |
| 리로드 | 활성화 | 비활성화 |
| 기본 호스트 | `127.0.0.1` | `0.0.0.0` |
| 로그 레벨 | `debug` | `info` |
| 워커 | 1 (고정) | 설정 가능 |
| Swagger UI | 활성화 | 비활성화 |

---

## 글로벌 옵션

모든 명령어에 공통으로 적용되는 옵션:

| 옵션 | 설명 |
|------|------|
| `--version` | 버전 출력 |
| `--help` | 도움말 출력 |
| `--verbose` | 상세 출력 |

---

## 종료 코드

| 코드 | 의미 |
|------|------|
| 0 | 정상 종료 |
| 1 | 일반 에러 |
| 2 | 설정 파일 에러 (`langgraph.json` 없음 또는 파싱 실패) |
| 3 | 그래프 로딩 에러 (모듈 import 실패) |
| 4 | 인증 설정 에러 (`OPENLANG_API_KEY` 미설정, serve 모드) |

---

## 관련 문서

- [02. 빠른 시작](./02-quick-start.md) - openlang dev 빠른 시작
- [03. 설정](./03-configuration.md) - langgraph.json 상세
- [11. 배포](./11-deployment.md) - Docker 빌드 및 프로덕션 배포
- [Appendix A. 환경변수](./appendix/A-environment-variables.md) - CLI 관련 환경변수
