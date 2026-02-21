# 02. 빠른 시작

## 개요

`langgraph-openai-api`를 설치하고, 간단한 그래프를 OpenAI 호환 API로 서빙하는 5분 가이드입니다.

---

## 사전 요구사항

| 항목 | 버전 |
|------|------|
| Python | 3.11+ |
| pip | 최신 |
| LLM API 키 | OpenAI, Anthropic 등 (그래프에서 사용할 LLM에 따라) |

---

## Step 1: 설치

```bash
pip install langgraph-openai-api
```

이 패키지는 다음을 함께 설치합니다:
- `langgraph`
- `langchain-core`
- `fastapi`
- `uvicorn`
- `openlang` CLI

---

## Step 2: 그래프 작성

간단한 채팅 그래프를 작성합니다.

```python
# graph.py

from typing import Annotated
from langchain_core.messages import AnyMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


llm = ChatOpenAI(model="gpt-4o-mini")


async def chatbot(state: State) -> State:
    response = await llm.ainvoke(state["messages"])
    return {"messages": [response]}


builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.set_entry_point("chatbot")
builder.set_finish_point("chatbot")

graph = builder.compile()
```

---

## Step 3: langgraph.json 작성

프로젝트 루트에 `langgraph.json`을 생성합니다.

```json
{
  "dependencies": ["."],
  "graphs": {
    "my-chatbot": "./graph.py:graph"
  },
  "env": ".env"
}
```

- `"my-chatbot"`: 이 이름이 OpenAI API의 `model` 파라미터가 됩니다
- `"./graph.py:graph"`: `graph.py` 파일의 `graph` 변수를 가리킵니다

> **상세**: [03. 설정](./03-configuration.md) 참조

---

## Step 4: 환경변수 설정

```bash
# .env
OPENAI_API_KEY=sk-your-openai-api-key
```

---

## Step 5: 개발 서버 실행

```bash
openlang dev
```

```
🚀 openlang dev server starting...
📦 Graphs loaded:
  - my-chatbot → ./graph.py:graph

🌐 Server: http://127.0.0.1:8000
📖 Docs:   http://127.0.0.1:8000/docs
🔓 Auth:   disabled (dev mode)
```

> **상세**: [10. CLI 레퍼런스](./10-cli-reference.md) 참조

---

## Step 6: API 호출

### curl

```bash
# 모델(그래프) 목록 확인
curl http://localhost:8000/v1/models

# 응답 생성 (비스트리밍)
curl -X POST http://localhost:8000/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "my-chatbot",
    "input": [
      {"role": "user", "content": "안녕하세요! LangGraph가 뭔가요?"}
    ]
  }'
```

### 스트리밍

```bash
curl -X POST http://localhost:8000/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "my-chatbot",
    "input": [{"role": "user", "content": "LangGraph를 설명해주세요"}],
    "stream": true
  }'
```

### OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    api_key="not-needed",  # dev 모드에서는 아무 값이나 OK
    base_url="http://localhost:8000/v1",
)

# 비스트리밍
response = client.responses.create(
    model="my-chatbot",
    input="안녕하세요!",
)
print(response.output[0].content[0].text)

# 스트리밍
stream = client.responses.create(
    model="my-chatbot",
    input="LangGraph를 설명해주세요",
    stream=True,
)
for event in stream:
    if event.type == "response.output_text.delta":
        print(event.delta, end="", flush=True)
print()
```

### OpenAI Node.js SDK

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: "not-needed",
  baseURL: "http://localhost:8000/v1",
});

const response = await client.responses.create({
  model: "my-chatbot",
  input: "안녕하세요!",
});
console.log(response.output[0].content[0].text);
```

---

## 프로젝트 구조 요약

최종 파일 구조:

```
my-project/
├── langgraph.json      # 그래프 등록
├── .env                # 환경변수
├── graph.py            # LangGraph 그래프
└── requirements.txt    # (선택) 의존성
```

```
# requirements.txt
langgraph-openai-api
langchain-openai
```

---

## 다음 단계

| 목표 | 참조 문서 |
|------|----------|
| 설정 상세 이해 | [03. 설정](./03-configuration.md) |
| API 스펙 확인 | [05. API 명세](./05-api-specification.md) |
| 커스텀 State 매핑 | [06. State 매핑](./06-state-mapping.md) |
| 스트리밍 심화 | [07. 스트리밍](./07-streaming.md) |
| 벡터 스토어 연동 | [08. 스토리지 어댑터](./08-storage-adapters.md) |
| 프로덕션 배포 | [11. 배포](./11-deployment.md) |
| 예제 프로젝트 | [예제: 기본 채팅 그래프](./examples/basic-chat-graph.md) |

---

## 관련 문서

- [01. 프로젝트 개요](./01-project-overview.md) - 전체 그림
- [03. 설정](./03-configuration.md) - langgraph.json 상세
- [10. CLI 레퍼런스](./10-cli-reference.md) - openlang 명령어 상세
- [예제: 기본 채팅 그래프](./examples/basic-chat-graph.md) - 확장된 예제
