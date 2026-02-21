# Appendix C. 네이밍 컨벤션

## 개요

`langgraph-openai-api` 프로젝트의 모듈, 변수, API 필드, Graph ID 등의 네이밍 규칙을 정의합니다.

---

## Graph ID

| 규칙 | 설명 | 예시 |
|------|------|------|
| 형식 | kebab-case (소문자 + 하이픈) | `main-chat`, `rag-agent` |
| 네임스페이스 | `--` (더블 하이픈)으로 구분 | `enterprise--main-chat` |
| 허용 문자 | `a-z`, `0-9`, `-` | `my-agent-v2` |
| 금지 문자 | 대문자, 언더스코어, 특수문자 | ~~`Main_Chat`~~ |
| 길이 | 최대 64자 | |

### 예시

| Graph ID | langgraph.json | model 파라미터 |
|----------|----------------|----------------|
| `main-chat` | `"main-chat": "./graph.py:graph"` | `model="main-chat"` |
| `enterprise--rag` | `"enterprise--rag": "./rag/graph.py:graph"` | `model="enterprise--rag"` |
| `code-assistant-v2` | `"code-assistant-v2": "./code/graph.py:graph"` | `model="code-assistant-v2"` |

---

## Python 모듈 / 패키지

| 항목 | 규칙 | 예시 |
|------|------|------|
| 패키지명 | snake_case | `langgraph_openai_api` |
| 모듈명 | snake_case | `input_translator.py` |
| 클래스명 | PascalCase | `VectorStoreAdapter` |
| 함수명 | snake_case | `translate_input()` |
| 상수 | UPPER_SNAKE_CASE | `DEFAULT_PORT = 8000` |
| 변수 | snake_case | `response_id` |
| 프라이빗 | `_` 접두사 | `_internal_state` |

---

## API 관련

### 엔드포인트 경로

| 규칙 | 예시 |
|------|------|
| 소문자 + 언더스코어 | `/v1/vector_stores` |
| 복수형 리소스 | `/v1/responses`, `/v1/models` |
| 중첩 리소스 | `/v1/vector_stores/{id}/files` |
| 버전 접두사 | `/v1/` |

### JSON 필드명

| 규칙 | 예시 |
|------|------|
| snake_case | `created_at`, `file_counts`, `output_text` |
| OpenAI 원본 유지 | `max_output_tokens`, `tool_choice` |

### ID 접두사

| 리소스 | 접두사 | 예시 |
|--------|--------|------|
| 응답 | `resp_` | `resp_abc123` |
| 메시지 | `msg_` | `msg_abc123` |
| 벡터 스토어 | `vs_` | `vs_abc123` |
| 파일 | `file_` | `file_abc123` |
| 함수 호출 | `fc_` | `fc_abc123` |

---

## 환경변수

| 규칙 | 예시 |
|------|------|
| 게이트웨이 변수 | `OPENLANG_` 접두사 | `OPENLANG_API_KEY` |
| UPPER_SNAKE_CASE | `OPENLANG_LOG_LEVEL` |
| 불리언 값 | `true` / `false` (소문자) |

---

## CLI 명령어

| 규칙 | 예시 |
|------|------|
| 명령어 | 소문자 단일 단어 | `dev`, `build`, `serve` |
| 옵션 (긴 형식) | `--kebab-case` | `--log-level`, `--no-reload` |
| 옵션 (짧은 형식) | `-X` (단일 문자) | `-p`, `-h`, `-c` |

---

## 파일 구조

| 항목 | 규칙 | 예시 |
|------|------|------|
| Python 파일 | snake_case | `input_translator.py` |
| 설정 파일 | kebab-case 또는 dot-case | `langgraph.json`, `.env` |
| 문서 파일 | `{번호}-{kebab-case}.md` | `01-project-overview.md` |
| 테스트 파일 | `test_{module}.py` | `test_input_translator.py` |

---

## Pydantic 모델

| 항목 | 규칙 | 예시 |
|------|------|------|
| 요청 모델 | `{동사}{리소스}Request` | `CreateResponseRequest` |
| 응답 모델 | `{리소스}Object` | `ResponseObject`, `ModelObject` |
| 목록 응답 | `{리소스}ListResponse` | `ModelListResponse` |
| 스트리밍 이벤트 | `{이벤트}Event` | `OutputTextDeltaEvent` |

---

## 관련 문서

- [03. 설정](../03-configuration.md) - Graph ID 설정
- [04. 내부 아키텍처](../04-architecture.md) - 모듈 구조
- [05. API 명세](../05-api-specification.md) - 엔드포인트 네이밍
