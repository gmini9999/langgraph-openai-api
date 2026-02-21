# Appendix B. OpenAI Responses API 빠른 참조

## 개요

OpenAI Responses API 원본 스펙과 `langgraph-openai-api`의 구현 범위를 비교합니다.

---

## Responses API 비교

### 엔드포인트

| 엔드포인트 | OpenAI 원본 | 게이트웨이 구현 | 비고 |
|-----------|------------|----------------|------|
| `POST /v1/responses` | Yes | Yes | 핵심 엔드포인트 |
| `GET /v1/responses/{id}` | Yes | Yes | 응답 조회 |
| `GET /v1/responses/{id}/input_items` | Yes | Yes | 입력 항목 조회 |
| `POST /v1/responses/{id}/cancel` | Yes | Yes | 응답 취소 |

### 요청 필드

| 필드 | OpenAI 원본 | 게이트웨이 | 비고 |
|------|------------|-----------|------|
| `model` | 모델 ID (gpt-4o 등) | 그래프 ID | 핵심 매핑 |
| `input` | string \| array | Yes | 동일 |
| `instructions` | string | Yes | SystemMessage로 변환 |
| `stream` | boolean | Yes | SSE 스트리밍 |
| `temperature` | number | Yes | 그래프에 전달 (매퍼 의존) |
| `top_p` | number | Yes | 그래프에 전달 (매퍼 의존) |
| `max_output_tokens` | integer | Yes | 그래프에 전달 (매퍼 의존) |
| `tools` | array | 부분 지원 | function 타입만 지원 |
| `tool_choice` | string \| object | 부분 지원 | auto, none, required |
| `metadata` | object | Yes | 커스텀 매퍼에서 활용 |
| `previous_response_id` | string | Yes | 체크포인트 매핑 |
| `store` | boolean | Yes | 응답 저장 |
| `text` | object | 부분 지원 | format.type=text만 |
| `reasoning` | object | 조건부 | 그래프 구현 의존 |
| `parallel_tool_calls` | boolean | No | 그래프 내부 처리 |
| `truncation` | string | No | 그래프 내부 처리 |
| `background` | boolean | No | 미지원 |
| `service_tier` | string | No | 미지원 |
| `top_logprobs` | integer | No | 미지원 |

### 도구 타입

| 도구 타입 | OpenAI 원본 | 게이트웨이 | 비고 |
|----------|------------|-----------|------|
| `function` | Yes | Yes | 함수 호출 |
| `web_search_preview` | Yes | No | 그래프 내부 구현 |
| `file_search` | Yes | 부분 지원 | 어댑터 연동 |
| `code_interpreter` | Yes | No | 미지원 |
| `mcp` | Yes | No | 미지원 |
| `image_generation` | Yes | No | 미지원 |
| `computer_use_preview` | Yes | No | 미지원 |

### 응답 출력 타입

| 출력 타입 | OpenAI 원본 | 게이트웨이 | 비고 |
|----------|------------|-----------|------|
| `message` | Yes | Yes | 텍스트 메시지 |
| `function_call` | Yes | Yes | 함수 호출 |
| `reasoning` | Yes | 조건부 | 그래프 구현 의존 |
| `file_search_call` | Yes | 부분 지원 | 어댑터 연동 |
| `web_search_call` | Yes | No | |
| `code_interpreter_call` | Yes | No | |
| `image_generation_call` | Yes | No | |
| `mcp_call` | Yes | No | |

---

## SSE 이벤트 비교

### 지원 이벤트

| 이벤트 | OpenAI 원본 | 게이트웨이 | 비고 |
|--------|------------|-----------|------|
| `response.created` | Yes | Yes | |
| `response.in_progress` | Yes | Yes | |
| `response.completed` | Yes | Yes | usage 포함 |
| `response.failed` | Yes | Yes | 에러 포함 |
| `response.cancelled` | Yes | Yes | |
| `response.incomplete` | Yes | Yes | |
| `response.output_item.added` | Yes | Yes | |
| `response.output_item.done` | Yes | Yes | |
| `response.content_part.added` | Yes | Yes | |
| `response.content_part.done` | Yes | Yes | |
| `response.output_text.delta` | Yes | Yes | 핵심 이벤트 |
| `response.output_text.done` | Yes | Yes | |
| `response.function_call_arguments.delta` | Yes | Yes | |
| `response.function_call_arguments.done` | Yes | Yes | |
| `error` | Yes | Yes | |

### 미지원 이벤트

| 이벤트 | 사유 |
|--------|------|
| `response.output_text.annotation.added` | 향후 지원 예정 |
| `response.refusal.delta` | 그래프에서 직접 처리 |
| `response.refusal.done` | 그래프에서 직접 처리 |
| `response.file_search_call.*` | 어댑터 패턴으로 대체 |
| `response.web_search_call.*` | 미지원 |
| `response.code_interpreter_call.*` | 미지원 |
| `response.image_generation_call.*` | 미지원 |
| `response.mcp_call.*` | 미지원 |
| `response.reasoning_summary_*` | 조건부 (그래프 구현 의존) |
| `response.queued` | background 모드 미지원 |

---

## Models API 비교

| 엔드포인트 | OpenAI 원본 | 게이트웨이 | 비고 |
|-----------|------------|-----------|------|
| `GET /v1/models` | Yes | Yes | 그래프 목록 반환 |
| `GET /v1/models/{model}` | Yes | Yes | 그래프 정보 반환 |
| `DELETE /v1/models/{model}` | Yes | No | 파인튜닝 관련 |

### 응답 필드 차이

| 필드 | OpenAI 원본 | 게이트웨이 | 비고 |
|------|------------|-----------|------|
| `id` | 모델 ID | 그래프 ID | |
| `object` | `"model"` | `"model"` | 동일 |
| `created` | 생성 시간 | 서버 시작 시간 | |
| `owned_by` | `"openai"` 등 | `"langgraph-openai-api"` | |

---

## Vector Stores API 비교

| 엔드포인트 | OpenAI 원본 | 게이트웨이 | 비고 |
|-----------|------------|-----------|------|
| `POST /v1/vector_stores` | Yes | Yes | 어댑터 위임 |
| `GET /v1/vector_stores` | Yes | Yes | 어댑터 위임 |
| `GET /v1/vector_stores/{id}` | Yes | Yes | 어댑터 위임 |
| `POST /v1/vector_stores/{id}` | Yes | Yes | 어댑터 위임 |
| `DELETE /v1/vector_stores/{id}` | Yes | Yes | 어댑터 위임 |
| `POST /v1/vector_stores/{id}/search` | Yes | Yes | 어댑터 위임 |
| `POST /v1/vector_stores/{id}/files` | Yes | Yes | 어댑터 위임 |
| `GET /v1/vector_stores/{id}/files` | Yes | Yes | 어댑터 위임 |
| `GET /v1/vector_stores/{id}/files/{fid}` | Yes | Yes | 어댑터 위임 |
| `DELETE /v1/vector_stores/{id}/files/{fid}` | Yes | Yes | 어댑터 위임 |
| 파일 배치 엔드포인트 (`file_batches`) | Yes | No | 미지원 |

> 벡터 스토어 API의 실제 동작은 `VectorStoreAdapter` 구현체에 따라 결정됩니다.

---

## Files API 비교

| 엔드포인트 | OpenAI 원본 | 게이트웨이 | 비고 |
|-----------|------------|-----------|------|
| `POST /v1/files` | Yes | Yes | 어댑터 위임 |
| `GET /v1/files` | Yes | Yes | 어댑터 위임 |
| `GET /v1/files/{id}` | Yes | Yes | 어댑터 위임 |
| `DELETE /v1/files/{id}` | Yes | Yes | 어댑터 위임 |
| `GET /v1/files/{id}/content` | Yes | Yes | 어댑터 위임 |

### purpose 필드 차이

| purpose | OpenAI 원본 | 게이트웨이 | 비고 |
|---------|------------|-----------|------|
| `assistants` | Yes | Yes | 벡터 스토어용 |
| `user_data` | Yes | Yes | 사용자 데이터 |
| `batch` | Yes | No | 배치 API 미지원 |
| `fine-tune` | Yes | No | 파인튜닝 미지원 |
| `vision` | Yes | 조건부 | 그래프 구현 의존 |
| `responses` | Yes | 조건부 | |

---

## 구현 우선순위 요약

| 우선순위 | 항목 | 설명 |
|---------|------|------|
| P0 | Responses (비스트리밍) | 핵심 기능 |
| P0 | Responses (스트리밍) | 핵심 기능 |
| P0 | Models (목록/조회) | 기본 기능 |
| P1 | Responses (조회/취소) | 대화 연속성 |
| P1 | Vector Stores (CRUD) | RAG 지원 |
| P1 | Files (CRUD) | 파일 관리 |
| P2 | Vector Stores (검색) | 고급 기능 |
| P2 | 도구 호출 스트리밍 | 고급 기능 |

---

## 관련 문서

- [05. API 명세](../05-api-specification.md) - 게이트웨이 엔드포인트 상세
- [07. 스트리밍](../07-streaming.md) - SSE 이벤트 매핑 상세
- [08. 스토리지 어댑터](../08-storage-adapters.md) - 어댑터 인터페이스
