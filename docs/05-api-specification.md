# 05. API 명세

## 개요

`langgraph-openai-api`가 노출하는 모든 OpenAI 호환 엔드포인트의 상세 스펙을 정의합니다.
OpenAI Responses API를 기반으로 하되, LangGraph 그래프 실행에 맞게 조정된 부분을 명시합니다.

---

## 엔드포인트 요약

| 메서드 | 엔드포인트 | 설명 | 구현 우선순위 |
|--------|-----------|------|-------------|
| POST | `/v1/responses` | 그래프 실행 (응답 생성) | P0 |
| GET | `/v1/responses/{response_id}` | 응답 조회 | P1 |
| GET | `/v1/responses/{response_id}/input_items` | 입력 항목 조회 | P2 |
| POST | `/v1/responses/{response_id}/cancel` | 응답 취소 | P2 |
| GET | `/v1/models` | 등록된 그래프 목록 | P0 |
| GET | `/v1/models/{model}` | 특정 그래프 정보 | P0 |
| GET | `/v1/vector_stores` | 벡터 스토어 목록 | P1 |
| POST | `/v1/vector_stores` | 벡터 스토어 생성 | P1 |
| GET | `/v1/vector_stores/{id}` | 벡터 스토어 조회 | P1 |
| POST | `/v1/vector_stores/{id}` | 벡터 스토어 수정 | P2 |
| DELETE | `/v1/vector_stores/{id}` | 벡터 스토어 삭제 | P2 |
| POST | `/v1/vector_stores/{id}/search` | 벡터 스토어 검색 | P1 |
| GET | `/v1/vector_stores/{id}/files` | 벡터 스토어 파일 목록 | P1 |
| POST | `/v1/vector_stores/{id}/files` | 벡터 스토어 파일 추가 | P1 |
| GET | `/v1/vector_stores/{id}/files/{file_id}` | 벡터 스토어 파일 조회 | P2 |
| DELETE | `/v1/vector_stores/{id}/files/{file_id}` | 벡터 스토어 파일 삭제 | P2 |
| GET | `/v1/files` | 파일 목록 | P1 |
| POST | `/v1/files` | 파일 업로드 | P1 |
| GET | `/v1/files/{file_id}` | 파일 메타데이터 조회 | P1 |
| DELETE | `/v1/files/{file_id}` | 파일 삭제 | P2 |
| GET | `/v1/files/{file_id}/content` | 파일 콘텐츠 다운로드 | P2 |

---

## 1. Responses API

### POST /v1/responses — 응답 생성

그래프를 실행하고 OpenAI Responses API 형식의 응답을 반환합니다.

#### 요청

```json
{
  "model": "main-chat",
  "input": [
    {
      "role": "user",
      "content": "안녕하세요, 오늘 날씨는 어때요?"
    }
  ],
  "stream": false,
  "instructions": "한국어로 답변해주세요.",
  "temperature": 0.7,
  "max_output_tokens": 1024,
  "metadata": {"user_id": "user-123"},
  "previous_response_id": null,
  "tools": [],
  "tool_choice": "auto"
}
```

#### 요청 필드 상세

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `model` | string | Yes | 실행할 그래프 ID (`langgraph.json`에 등록된 이름) |
| `input` | string \| array | Yes | 입력 텍스트 또는 메시지 배열 |
| `stream` | boolean | No | SSE 스트리밍 여부 (기본: `false`) |
| `instructions` | string \| null | No | 시스템 프롬프트 |
| `temperature` | number | No | 샘플링 온도 (0-2, 기본: 1.0) |
| `top_p` | number | No | 누클리어스 샘플링 (기본: 1.0) |
| `max_output_tokens` | integer \| null | No | 최대 출력 토큰 수 |
| `tools` | array | No | 도구 정의 배열 |
| `tool_choice` | string \| object | No | 도구 선택 방식 (`auto`, `none`, `required`) |
| `metadata` | object \| null | No | 메타데이터 (최대 16개 키-값 쌍) |
| `previous_response_id` | string \| null | No | 이전 응답 ID (멀티턴 대화) |
| `store` | boolean | No | 응답 저장 여부 (기본: `true`) |
| `text` | object | No | 텍스트 출력 형식 설정 |
| `reasoning` | object | No | 추론 설정 (`effort`, `summary`) |

#### input 메시지 형식

```json
[
  {
    "role": "user",
    "content": "텍스트 메시지"
  },
  {
    "role": "user",
    "content": [
      {"type": "input_text", "text": "이미지를 설명해주세요"},
      {"type": "input_image", "image_url": "https://...", "detail": "auto"}
    ]
  },
  {
    "role": "assistant",
    "content": "이전 어시스턴트 응답"
  },
  {
    "role": "system",
    "content": "시스템 지시사항"
  }
]
```

#### 응답 (비스트리밍)

```json
{
  "id": "resp_abc123",
  "object": "response",
  "created_at": 1741476542,
  "status": "completed",
  "model": "main-chat",
  "output": [
    {
      "type": "message",
      "id": "msg_abc123",
      "status": "completed",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "안녕하세요! 오늘 날씨는...",
          "annotations": []
        }
      ]
    }
  ],
  "usage": {
    "input_tokens": 36,
    "output_tokens": 87,
    "total_tokens": 123
  },
  "metadata": {},
  "temperature": 0.7,
  "max_output_tokens": 1024,
  "top_p": 1.0,
  "tools": [],
  "tool_choice": "auto",
  "text": {"format": {"type": "text"}},
  "previous_response_id": null,
  "store": true
}
```

#### 응답 필드 상세

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | string | 응답 고유 ID (`resp_` 접두사) |
| `object` | string | 항상 `"response"` |
| `created_at` | integer | 생성 시간 (Unix timestamp) |
| `status` | string | `completed` \| `failed` \| `cancelled` \| `incomplete` \| `in_progress` |
| `model` | string | 실행된 그래프 ID |
| `output` | array | 출력 항목 배열 |
| `usage` | object | 토큰 사용량 |
| `metadata` | object | 요청 시 전달된 메타데이터 |

#### Output 항목 타입

| 타입 | 설명 | 게이트웨이 지원 |
|------|------|----------------|
| `message` | 어시스턴트 메시지 | Yes |
| `function_call` | 함수 호출 | Yes (도구 사용 그래프) |
| `reasoning` | 추론 요약 | 조건부 (그래프 구현 의존) |
| `file_search_call` | 파일 검색 호출 | Yes (어댑터 연동) |
| `web_search_call` | 웹 검색 호출 | No (미지원) |

#### 스트리밍 응답

`stream: true`일 때 SSE로 응답합니다. 상세는 [07. 스트리밍](./07-streaming.md) 참조.

---

### GET /v1/responses/{response_id} — 응답 조회

이전에 생성된 응답을 조회합니다.

#### 요청

```
GET /v1/responses/resp_abc123
Authorization: Bearer <api-key>
```

#### 응답

POST `/v1/responses`의 응답과 동일한 `ResponseObject`.

---

### GET /v1/responses/{response_id}/input_items — 입력 항목 조회

응답 생성 시 사용된 입력 항목들을 조회합니다.

#### 응답

```json
{
  "object": "list",
  "data": [
    {
      "type": "message",
      "role": "user",
      "content": [
        {"type": "input_text", "text": "안녕하세요"}
      ]
    }
  ]
}
```

---

## 2. Models API

### GET /v1/models — 모델(그래프) 목록

`langgraph.json`에 등록된 모든 그래프를 OpenAI 모델 형식으로 반환합니다.

#### 응답

```json
{
  "object": "list",
  "data": [
    {
      "id": "main-chat",
      "object": "model",
      "created": 1686935002,
      "owned_by": "langgraph-openai-api"
    },
    {
      "id": "rag-agent",
      "object": "model",
      "created": 1686935002,
      "owned_by": "langgraph-openai-api"
    }
  ]
}
```

### GET /v1/models/{model} — 특정 모델(그래프) 정보

#### 응답

```json
{
  "id": "main-chat",
  "object": "model",
  "created": 1686935002,
  "owned_by": "langgraph-openai-api"
}
```

#### 에러 (존재하지 않는 모델)

```json
{
  "error": {
    "message": "The model 'unknown-model' does not exist",
    "type": "invalid_request_error",
    "param": "model",
    "code": "model_not_found"
  }
}
```

---

## 3. Vector Stores API

벡터 스토어 관련 엔드포인트는 **어댑터 패턴**으로 구현됩니다.
게이트웨이는 OpenAI 형식 변환만 담당하고, 실제 CRUD는 `VectorStoreAdapter` 구현체에 위임합니다.

> **상세**: 어댑터 인터페이스는 [08. 스토리지 어댑터](./08-storage-adapters.md) 참조

### POST /v1/vector_stores — 벡터 스토어 생성

#### 요청

```json
{
  "name": "Knowledge Base",
  "metadata": {"project": "my-project"},
  "file_ids": ["file-abc123"],
  "chunking_strategy": {
    "type": "static",
    "static": {
      "max_chunk_size_tokens": 800,
      "chunk_overlap_tokens": 400
    }
  }
}
```

#### 요청 필드

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `name` | string | No | 벡터 스토어 이름 |
| `file_ids` | array | No | 초기 추가할 파일 ID 배열 |
| `metadata` | object | No | 메타데이터 (최대 16개 키-값) |
| `chunking_strategy` | object | No | 청킹 전략 |
| `expires_after` | object | No | 만료 설정 |

#### 응답

```json
{
  "id": "vs_abc123",
  "object": "vector_store",
  "created_at": 1699061776,
  "name": "Knowledge Base",
  "status": "completed",
  "file_counts": {
    "in_progress": 0,
    "completed": 1,
    "failed": 0,
    "cancelled": 0,
    "total": 1
  },
  "usage_bytes": 139920,
  "metadata": {"project": "my-project"}
}
```

### GET /v1/vector_stores — 벡터 스토어 목록

#### 쿼리 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `limit` | integer | 20 | 결과 수 (1-100) |
| `order` | string | `"desc"` | 정렬 (`asc` \| `desc`) |
| `after` | string | — | 페이지네이션 커서 |
| `before` | string | — | 페이지네이션 커서 |

#### 응답

```json
{
  "object": "list",
  "data": [...],
  "first_id": "vs_abc123",
  "last_id": "vs_abc456",
  "has_more": false
}
```

### POST /v1/vector_stores/{vector_store_id}/search — 벡터 스토어 검색

#### 요청

```json
{
  "query": "LangGraph 사용법",
  "max_num_results": 10,
  "filters": {
    "type": "eq",
    "key": "category",
    "value": "tutorial"
  },
  "ranking_options": {
    "ranker": "default-2024-11-15",
    "score_threshold": 0.5
  }
}
```

#### 응답

```json
{
  "object": "vector_store.search_results",
  "data": [
    {
      "file_id": "file-abc123",
      "filename": "guide.pdf",
      "score": 0.92,
      "content": [
        {"type": "text", "text": "LangGraph는 ..."}
      ],
      "attributes": {"category": "tutorial"}
    }
  ]
}
```

### 벡터 스토어 파일 엔드포인트

| 메서드 | 엔드포인트 | 요청 | 응답 |
|--------|-----------|------|------|
| POST | `/v1/vector_stores/{id}/files` | `{"file_id": "file-abc123"}` | VectorStoreFile 객체 |
| GET | `/v1/vector_stores/{id}/files` | 쿼리 파라미터 (limit, order, after) | 목록 |
| GET | `/v1/vector_stores/{id}/files/{file_id}` | — | VectorStoreFile 객체 |
| DELETE | `/v1/vector_stores/{id}/files/{file_id}` | — | 삭제 확인 |

---

## 4. Files API

파일 관련 엔드포인트는 `FileAdapter` 구현체에 위임됩니다.

### POST /v1/files — 파일 업로드

#### 요청 (multipart/form-data)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `file` | file | Yes | 업로드할 파일 |
| `purpose` | string | Yes | 용도: `assistants`, `batch`, `user_data` |

#### 응답

```json
{
  "id": "file-abc123",
  "object": "file",
  "bytes": 120000,
  "created_at": 1677610602,
  "filename": "document.pdf",
  "purpose": "assistants"
}
```

### GET /v1/files — 파일 목록

#### 쿼리 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `purpose` | string | — | 용도별 필터 |
| `limit` | integer | 10000 | 결과 수 (1-10000) |
| `order` | string | `"desc"` | 정렬 |
| `after` | string | — | 페이지네이션 커서 |

#### 응답

```json
{
  "object": "list",
  "data": [...],
  "has_more": false
}
```

### GET /v1/files/{file_id} — 파일 정보 조회

```json
{
  "id": "file-abc123",
  "object": "file",
  "bytes": 120000,
  "created_at": 1677610602,
  "filename": "document.pdf",
  "purpose": "assistants"
}
```

### DELETE /v1/files/{file_id} — 파일 삭제

```json
{
  "id": "file-abc123",
  "object": "file",
  "deleted": true
}
```

### GET /v1/files/{file_id}/content — 파일 콘텐츠 다운로드

바이너리 파일 콘텐츠를 반환합니다.

---

## 5. 공통 사항

### 인증

모든 엔드포인트는 Bearer 토큰 인증이 필요합니다.

```
Authorization: Bearer <api-key>
```

> **상세**: [09. 인증](./09-authentication.md) 참조

### 에러 응답 형식

OpenAI 에러 형식을 따릅니다.

```json
{
  "error": {
    "message": "에러 설명",
    "type": "invalid_request_error",
    "param": "model",
    "code": "model_not_found"
  }
}
```

| HTTP 상태 | type | 설명 |
|-----------|------|------|
| 400 | `invalid_request_error` | 잘못된 요청 파라미터 |
| 401 | `authentication_error` | 인증 실패 |
| 404 | `not_found_error` | 리소스 없음 |
| 429 | `rate_limit_error` | 요청 제한 초과 |
| 500 | `server_error` | 내부 서버 오류 |

### 페이지네이션

목록 엔드포인트는 커서 기반 페이지네이션을 지원합니다.

```json
{
  "object": "list",
  "data": [...],
  "first_id": "obj_first",
  "last_id": "obj_last",
  "has_more": true
}
```

---

## 6. OpenAI API 대비 미지원 항목

| 항목 | 설명 |
|------|------|
| `web_search_call` | 웹 검색 도구 (그래프 내부 구현으로 대체) |
| `code_interpreter_call` | 코드 인터프리터 |
| `image_generation_call` | 이미지 생성 |
| `mcp_call` | MCP 호출 |
| `computer_use_preview` | 컴퓨터 사용 도구 |
| `background` 모드 | 백그라운드 실행 |
| 파인튜닝 관련 | 모델 삭제 등 |
| 파일 배치 | vector_stores 파일 배치 처리 |

---

## 관련 문서

- [01. 프로젝트 개요](./01-project-overview.md) - 전체 그림
- [06. State 매핑](./06-state-mapping.md) - 요청/응답 변환 규칙
- [07. 스트리밍](./07-streaming.md) - SSE 스트리밍 상세
- [08. 스토리지 어댑터](./08-storage-adapters.md) - 어댑터 인터페이스
- [09. 인증](./09-authentication.md) - 인증 상세
- [Appendix B. OpenAI API 참조](./appendix/B-openai-api-reference.md) - 원본 API 비교
