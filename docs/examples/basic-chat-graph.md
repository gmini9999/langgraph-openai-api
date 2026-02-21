# 예제: 기본 채팅 그래프 서빙

## 개요

간단한 LangGraph 채팅 그래프를 `langgraph-openai-api`로 서빙하는 전체 예제입니다.

---

## 프로젝트 구조

```
basic-chat-example/
├── langgraph.json
├── .env
├── graph.py
└── requirements.txt
```

---

## 1. 의존성

```txt
# requirements.txt
langgraph-openai-api
langchain-openai
```

```bash
pip install -r requirements.txt
```

---

## 2. 그래프 작성

```python
# graph.py

from typing import Annotated

from langchain_core.messages import AnyMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


# --- State 정의 ---

class State(TypedDict):
    """채팅 그래프 상태."""
    messages: Annotated[list[AnyMessage], add_messages]


# --- LLM 설정 ---

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)


# --- 노드 정의 ---

SYSTEM_PROMPT = "당신은 친절하고 도움이 되는 AI 어시스턴트입니다. 한국어로 답변합니다."


async def chatbot(state: State) -> State:
    """사용자 메시지에 응답합니다."""
    messages = state["messages"]

    # 시스템 프롬프트 추가 (없으면)
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    response = await llm.ainvoke(messages)
    return {"messages": [response]}


# --- 그래프 빌드 ---

builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.set_entry_point("chatbot")
builder.set_finish_point("chatbot")

graph = builder.compile()
```

---

## 3. 설정 파일

```json
// langgraph.json
{
  "dependencies": ["."],
  "graphs": {
    "basic-chat": "./graph.py:graph"
  },
  "env": ".env"
}
```

```bash
# .env
OPENAI_API_KEY=sk-your-openai-api-key
```

---

## 4. 서버 실행

```bash
openlang dev
```

```
🚀 openlang dev server starting...
📦 Graphs loaded:
  - basic-chat → ./graph.py:graph

🌐 Server: http://127.0.0.1:8000
📖 Docs:   http://127.0.0.1:8000/docs
🔓 Auth:   disabled (dev mode)
```

---

## 5. API 호출 예제

### 모델 목록 확인

```bash
curl http://localhost:8000/v1/models | python -m json.tool
```

```json
{
  "object": "list",
  "data": [
    {
      "id": "basic-chat",
      "object": "model",
      "created": 1699061776,
      "owned_by": "langgraph-openai-api"
    }
  ]
}
```

### 비스트리밍 응답

```bash
curl -X POST http://localhost:8000/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "basic-chat",
    "input": [
      {"role": "user", "content": "LangGraph가 뭔가요? 간단히 설명해주세요."}
    ]
  }' | python -m json.tool
```

```json
{
  "id": "resp_abc123",
  "object": "response",
  "status": "completed",
  "model": "basic-chat",
  "output": [
    {
      "type": "message",
      "id": "msg_abc123",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "LangGraph는 LLM 기반 에이전트를 구축하기 위한 프레임워크입니다. 상태 기반 그래프로 복잡한 AI 워크플로우를 정의할 수 있습니다."
        }
      ]
    }
  ],
  "usage": {
    "input_tokens": 45,
    "output_tokens": 62,
    "total_tokens": 107
  }
}
```

### 스트리밍 응답

```bash
curl -N -X POST http://localhost:8000/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "basic-chat",
    "input": [{"role": "user", "content": "Python의 장점을 3가지 알려주세요."}],
    "stream": true
  }'
```

### OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    api_key="not-needed",
    base_url="http://localhost:8000/v1",
)

# 비스트리밍
response = client.responses.create(
    model="basic-chat",
    input="안녕하세요! 반갑습니다.",
)
print(response.output[0].content[0].text)

# 스트리밍
stream = client.responses.create(
    model="basic-chat",
    input="Python의 장점을 3가지 알려주세요.",
    stream=True,
)
for event in stream:
    if event.type == "response.output_text.delta":
        print(event.delta, end="", flush=True)
print()

# instructions 활용
response = client.responses.create(
    model="basic-chat",
    instructions="영어로만 답변해주세요.",
    input="한국의 수도는 어디인가요?",
)
print(response.output[0].content[0].text)

# 멀티턴 대화
resp1 = client.responses.create(
    model="basic-chat",
    input="제 이름은 홍길동입니다.",
)
resp2 = client.responses.create(
    model="basic-chat",
    input="제 이름이 뭐라고 했죠?",
    previous_response_id=resp1.id,
)
print(resp2.output[0].content[0].text)
```

---

## 관련 문서

- [02. 빠른 시작](../02-quick-start.md) - 빠른 시작 가이드
- [06. State 매핑](../06-state-mapping.md) - 커스텀 State 매핑
- [예제: RAG + Vector Store](./rag-vector-store.md) - RAG 예제
- [예제: 멀티 그래프](./multi-model-serving.md) - 멀티 모델 예제
