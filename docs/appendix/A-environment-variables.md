# Appendix A. 환경변수 마스터 레퍼런스

## 개요

`langgraph-openai-api`에서 사용하는 모든 환경변수의 마스터 레퍼런스입니다.

---

## 게이트웨이 설정

| 변수 | 설명 | 기본값 | 필수 | 비고 |
|------|------|--------|------|------|
| `OPENLANG_API_KEY` | API 인증 키 (콤마 구분으로 다중 키 지원) | — | 프로덕션 필수 | `openlang serve` 시 필수 |
| `OPENLANG_HOST` | 서버 바인드 호스트 | `0.0.0.0` | No | `dev` 모드는 `127.0.0.1` |
| `OPENLANG_PORT` | 서버 바인드 포트 | `8000` | No | |
| `OPENLANG_DEV` | 개발 모드 활성화 | `false` | No | `true`이면 인증 비활성화 |
| `OPENLANG_WORKERS` | Uvicorn 워커 수 | `1` | No | 프로덕션에서 CPU 수에 맞춰 설정 |
| `OPENLANG_LOG_LEVEL` | 로그 레벨 | `info` | No | `debug`, `info`, `warning`, `error` |
| `OPENLANG_CONFIG` | langgraph.json 경로 | `./langgraph.json` | No | CLI `--config` 옵션과 동일 |
| `OPENLANG_CORS_ORIGINS` | CORS 허용 오리진 (콤마 구분) | `*` | No | 프로덕션에서 제한 권장 |

---

## LLM 프로바이더

| 변수 | 설명 | 기본값 | 비고 |
|------|------|--------|------|
| `OPENAI_API_KEY` | OpenAI API 키 | — | `ChatOpenAI` 사용 시 필수 |
| `OPENAI_API_BASE` | OpenAI API 베이스 URL | — | 커스텀 엔드포인트 |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | — | `ChatAnthropic` 사용 시 |
| `GOOGLE_API_KEY` | Google AI API 키 | — | `ChatGoogleGenerativeAI` 사용 시 |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI 키 | — | Azure 사용 시 |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI 엔드포인트 | — | Azure 사용 시 |
| `AZURE_OPENAI_API_VERSION` | Azure OpenAI API 버전 | — | Azure 사용 시 |

---

## LangChain / LangSmith

| 변수 | 설명 | 기본값 | 비고 |
|------|------|--------|------|
| `LANGCHAIN_TRACING_V2` | LangSmith 추적 활성화 | `false` | `true`로 설정 시 추적 시작 |
| `LANGCHAIN_API_KEY` | LangSmith API 키 | — | 추적 활성화 시 필수 |
| `LANGCHAIN_PROJECT` | LangSmith 프로젝트명 | `default` | |
| `LANGCHAIN_ENDPOINT` | LangSmith 엔드포인트 | `https://api.smith.langchain.com` | |

---

## 데이터베이스

| 변수 | 설명 | 기본값 | 비고 |
|------|------|--------|------|
| `DATABASE_URL` | PostgreSQL 연결 URL | — | 체크포인트 저장 시 |
| `QDRANT_URL` | Qdrant 서버 URL | — | 벡터 스토어 어댑터 사용 시 |
| `QDRANT_API_KEY` | Qdrant API 키 | — | 클라우드 Qdrant 사용 시 |
| `REDIS_URL` | Redis 연결 URL | — | 캐시/세션 사용 시 |

---

## 스토리지

| 변수 | 설명 | 기본값 | 비고 |
|------|------|--------|------|
| `AWS_ACCESS_KEY_ID` | AWS 액세스 키 | — | S3 파일 어댑터 사용 시 |
| `AWS_SECRET_ACCESS_KEY` | AWS 시크릿 키 | — | S3 파일 어댑터 사용 시 |
| `AWS_DEFAULT_REGION` | AWS 기본 리전 | — | S3 파일 어댑터 사용 시 |
| `S3_BUCKET` | S3 버킷 이름 | — | S3 파일 어댑터 사용 시 |

---

## .env 파일 템플릿

```bash
# === 게이트웨이 설정 ===
OPENLANG_API_KEY=sk-your-api-key
OPENLANG_HOST=0.0.0.0
OPENLANG_PORT=8000
OPENLANG_DEV=false
OPENLANG_WORKERS=2
OPENLANG_LOG_LEVEL=info

# === LLM 프로바이더 ===
OPENAI_API_KEY=sk-...

# === LangSmith (선택) ===
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=ls-...
# LANGCHAIN_PROJECT=my-project

# === 데이터베이스 (선택) ===
# DATABASE_URL=postgresql://user:pass@localhost:5432/langgraph
# QDRANT_URL=http://localhost:6333

# === 스토리지 (선택) ===
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
# S3_BUCKET=my-files
```

---

## 우선순위

환경변수 로딩 우선순위 (높은 순):

1. 시스템 환경변수 (쉘에서 직접 설정)
2. `.env` 파일 (`langgraph.json`의 `env` 필드가 가리키는 파일)
3. 기본값

---

## 관련 문서

- [03. 설정](../03-configuration.md) - 설정 상세
- [09. 인증](../09-authentication.md) - 인증 관련 환경변수
- [11. 배포](../11-deployment.md) - 배포 환경별 설정
