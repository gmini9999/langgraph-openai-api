# 예제: 멀티 그래프/모델 서빙

## 개요

여러 LangGraph 그래프를 동시에 서빙하여 OpenAI API의 `model` 파라미터로 선택하는 예제입니다.
하나의 게이트웨이에서 다양한 목적의 에이전트를 통합 관리합니다.

---

## 프로젝트 구조

```
multi-model-example/
├── langgraph.json
├── .env
├── pyproject.toml
├── src/
│   └── agents/
│       ├── chat/
│       │   ├── __init__.py
│       │   ├── graph.py        # 일반 채팅
│       │   └── state.py
│       ├── code/
│       │   ├── __init__.py
│       │   ├── graph.py        # 코드 어시스턴트
│       │   └── state.py
│       └── summary/
│           ├── __init__.py
│           ├── graph.py        # 요약 에이전트
│           └── state.py
└── tests/
```

---

## 1. langgraph.json

```json
{
  "dependencies": ["."],
  "graphs": {
    "chat": "./src/agents/chat/graph.py:graph",
    "code-assistant": "./src/agents/code/graph.py:graph",
    "summarizer": "./src/agents/summary/graph.py:graph"
  },
  "env": ".env"
}
```

---

## 2. 채팅 그래프

```python
# src/agents/chat/graph.py

from typing import Annotated

from langchain_core.messages import AnyMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)


async def chatbot(state: State) -> State:
    messages = [
        SystemMessage(content="친절하고 도움이 되는 AI 어시스턴트입니다. 한국어로 답변합니다."),
        *state["messages"],
    ]
    response = await llm.ainvoke(messages)
    return {"messages": [response]}


builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.set_entry_point("chatbot")
builder.set_finish_point("chatbot")

graph = builder.compile()
```

---

## 3. 코드 어시스턴트 그래프

```python
# src/agents/code/graph.py

from typing import Annotated

from langchain_core.messages import AnyMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


llm = ChatOpenAI(model="gpt-4o", temperature=0)

CODE_SYSTEM_PROMPT = """당신은 전문 프로그래밍 어시스턴트입니다.

규칙:
1. 코드 예제를 포함하여 답변합니다.
2. 코드 블록에는 언어 태그를 명시합니다.
3. 모범 사례와 주의사항을 함께 안내합니다.
4. 한국어로 설명하되, 코드 주석은 영어로 작성합니다.
"""


async def code_assistant(state: State) -> State:
    messages = [
        SystemMessage(content=CODE_SYSTEM_PROMPT),
        *state["messages"],
    ]
    response = await llm.ainvoke(messages)
    return {"messages": [response]}


builder = StateGraph(State)
builder.add_node("code_assistant", code_assistant)
builder.set_entry_point("code_assistant")
builder.set_finish_point("code_assistant")

graph = builder.compile()
```

---

## 4. 요약 에이전트 그래프

```python
# src/agents/summary/graph.py

from typing import Annotated, Any

from langchain_core.messages import AIMessage, AnyMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from langgraph_openai_api.translators.state_mapper import (
    register_input_mapper,
    register_output_mapper,
)


# --- State ---

class InputState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    summary_style: str  # "brief", "detailed", "bullet"


class SummaryState(InputState):
    summary: str
    word_count: int


# --- 노드 ---

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

SUMMARY_PROMPTS = {
    "brief": "다음 텍스트를 2-3문장으로 간결하게 요약해주세요.",
    "detailed": "다음 텍스트를 상세하게 요약해주세요. 주요 포인트를 모두 포함합니다.",
    "bullet": "다음 텍스트를 핵심 포인트 별로 불릿 리스트로 요약해주세요.",
}


async def summarize(state: SummaryState) -> SummaryState:
    style = state.get("summary_style", "brief")
    prompt = SUMMARY_PROMPTS.get(style, SUMMARY_PROMPTS["brief"])

    messages = [
        SystemMessage(content=prompt),
        *state["messages"],
    ]

    response = await llm.ainvoke(messages)

    return {
        "messages": [response],
        "summary": response.content,
        "word_count": len(response.content.split()),
    }


# --- 그래프 ---

builder = StateGraph(SummaryState, input=InputState)
builder.add_node("summarize", summarize)
builder.set_entry_point("summarize")
builder.set_finish_point("summarize")

graph = builder.compile()


# --- 커스텀 매퍼 ---

def input_mapper(request: dict) -> dict:
    """metadata에서 summary_style을 추출합니다."""
    messages = request["messages"]
    metadata = request.get("metadata", {})
    return {
        "messages": messages,
        "summary_style": metadata.get("summary_style", "brief"),
    }


def output_mapper(state: dict) -> str:
    """요약 결과와 단어 수를 포함합니다."""
    summary = state.get("summary", "")
    word_count = state.get("word_count", 0)
    return f"{summary}\n\n---\n단어 수: {word_count}"


register_input_mapper("summarizer", input_mapper)
register_output_mapper("summarizer", output_mapper)
```

---

## 5. 실행 및 사용

### 서버 실행

```bash
openlang dev
```

```
🚀 openlang dev server starting...
📦 Graphs loaded:
  - chat            → ./src/agents/chat/graph.py:graph
  - code-assistant  → ./src/agents/code/graph.py:graph
  - summarizer      → ./src/agents/summary/graph.py:graph

🌐 Server: http://127.0.0.1:8000
```

### 모델 목록 확인

```bash
curl http://localhost:8000/v1/models | python -m json.tool
```

```json
{
  "object": "list",
  "data": [
    {"id": "chat", "object": "model", "owned_by": "langgraph-openai-api"},
    {"id": "code-assistant", "object": "model", "owned_by": "langgraph-openai-api"},
    {"id": "summarizer", "object": "model", "owned_by": "langgraph-openai-api"}
  ]
}
```

### model 파라미터로 그래프 선택

```python
from openai import OpenAI

client = OpenAI(
    api_key="not-needed",
    base_url="http://localhost:8000/v1",
)

# 일반 채팅
chat_response = client.responses.create(
    model="chat",
    input="오늘 점심 뭐 먹을까?",
)
print(f"[chat] {chat_response.output[0].content[0].text}")

# 코드 어시스턴트
code_response = client.responses.create(
    model="code-assistant",
    input="Python으로 퀵소트 알고리즘을 구현해주세요",
)
print(f"[code] {code_response.output[0].content[0].text}")

# 요약 (커스텀 매퍼 + metadata)
summary_response = client.responses.create(
    model="summarizer",
    input="LangGraph는 LLM 기반 에이전트를 구축하기 위한 프레임워크입니다. 상태 기반 그래프로 복잡한 AI 워크플로우를 정의할 수 있으며, 체크포인트, 휴먼인더루프 등의 기능을 제공합니다. LangChain 생태계의 일부로, LangChain의 다양한 통합 기능을 활용할 수 있습니다.",
    metadata={"summary_style": "bullet"},
)
print(f"[summary] {summary_response.output[0].content[0].text}")
```

### 스트리밍으로 사용

```python
# 각 모델 스트리밍 가능
for model_name in ["chat", "code-assistant", "summarizer"]:
    print(f"\n--- {model_name} ---")
    stream = client.responses.create(
        model=model_name,
        input="Python이란 무엇인가요?",
        stream=True,
    )
    for event in stream:
        if event.type == "response.output_text.delta":
            print(event.delta, end="", flush=True)
    print()
```

---

## 6. 활용 시나리오

### 클라이언트에서 모델 동적 선택

```python
def ask_ai(question: str, task_type: str = "chat") -> str:
    """질문 유형에 따라 적절한 모델을 선택합니다."""
    model_map = {
        "chat": "chat",
        "code": "code-assistant",
        "summary": "summarizer",
    }
    model = model_map.get(task_type, "chat")

    response = client.responses.create(
        model=model,
        input=question,
    )
    return response.output[0].content[0].text


# 사용
print(ask_ai("안녕하세요", "chat"))
print(ask_ai("Python 리스트 컴프리헨션 예제", "code"))
print(ask_ai("긴 텍스트...", "summary"))
```

### 네임스페이스로 조직화

대규모 프로젝트에서는 `--`로 네임스페이스를 구분합니다:

```json
{
  "graphs": {
    "enterprise--chat": "./src/agents/enterprise/chat/graph.py:graph",
    "enterprise--rag": "./src/agents/enterprise/rag/graph.py:graph",
    "internal--admin": "./src/agents/internal/admin/graph.py:graph",
    "internal--analytics": "./src/agents/internal/analytics/graph.py:graph"
  }
}
```

```python
# 네임스페이스 포함 모델 선택
response = client.responses.create(
    model="enterprise--chat",
    input="프로젝트 상태를 알려주세요",
)
```

---

## 관련 문서

- [01. 프로젝트 개요](../01-project-overview.md) - Graph=Model 개념
- [03. 설정](../03-configuration.md) - Graph ID 규칙
- [06. State 매핑](../06-state-mapping.md) - 커스텀 매퍼
- [예제: 기본 채팅 그래프](./basic-chat-graph.md) - 기본 예제
- [예제: RAG + Vector Store](./rag-vector-store.md) - RAG 예제
