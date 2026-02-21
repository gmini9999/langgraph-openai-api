# 12. 테스트

## 개요

`langgraph-openai-api`의 단위 테스트, 통합 테스트, OpenAI SDK 호환성 테스트 전략을 정의합니다.

---

## 테스트 구조

```
tests/
├── unit/                       # 단위 테스트
│   ├── test_input_translator.py
│   ├── test_output_translator.py
│   ├── test_stream_translator.py
│   ├── test_state_mapper.py
│   ├── test_graph_loader.py
│   ├── test_graph_registry.py
│   └── test_models.py
├── integration/                # 통합 테스트
│   ├── test_responses_api.py
│   ├── test_models_api.py
│   ├── test_vector_stores_api.py
│   ├── test_files_api.py
│   └── test_streaming.py
├── compatibility/              # OpenAI SDK 호환성 테스트
│   ├── test_openai_sdk.py
│   ├── test_openai_streaming.py
│   └── test_openai_models.py
├── conftest.py                 # 공용 fixture
└── fixtures/                   # 테스트 데이터
    ├── sample_graph.py
    └── langgraph.json
```

---

## 1. 단위 테스트

### 변환기 테스트

변환기(translators) 모듈의 입출력을 검증합니다.

#### input_translator 테스트

```python
# tests/unit/test_input_translator.py

import pytest
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph_openai_api.translators.input_translator import translate_input


class TestTranslateInput:
    """OpenAI 요청 → LangGraph State 변환 테스트."""

    def test_simple_text_input(self):
        """단순 텍스트 입력 변환."""
        request = {
            "model": "main-chat",
            "input": "안녕하세요",
        }
        state = translate_input(request)
        assert len(state["messages"]) == 1
        assert isinstance(state["messages"][0], HumanMessage)
        assert state["messages"][0].content == "안녕하세요"

    def test_message_array_input(self):
        """메시지 배열 입력 변환."""
        request = {
            "model": "main-chat",
            "input": [
                {"role": "user", "content": "안녕하세요"},
            ],
        }
        state = translate_input(request)
        assert len(state["messages"]) == 1
        assert isinstance(state["messages"][0], HumanMessage)

    def test_instructions_as_system_message(self):
        """instructions → SystemMessage 변환."""
        request = {
            "model": "main-chat",
            "instructions": "한국어로 답변해주세요",
            "input": [{"role": "user", "content": "hello"}],
        }
        state = translate_input(request)
        assert len(state["messages"]) == 2
        assert isinstance(state["messages"][0], SystemMessage)
        assert state["messages"][0].content == "한국어로 답변해주세요"

    def test_multimodal_content(self):
        """멀티모달 콘텐츠 변환."""
        request = {
            "model": "main-chat",
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "이미지 설명"},
                        {"type": "input_image", "image_url": "https://example.com/img.png"},
                    ],
                }
            ],
        }
        state = translate_input(request)
        assert isinstance(state["messages"][0].content, list)
```

#### output_translator 테스트

```python
# tests/unit/test_output_translator.py

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph_openai_api.translators.output_translator import translate_output


class TestTranslateOutput:
    """LangGraph State → OpenAI Response 변환 테스트."""

    def test_simple_message_output(self):
        """단순 메시지 출력 변환."""
        state = {
            "messages": [
                HumanMessage(content="안녕"),
                AIMessage(content="안녕하세요!"),
            ]
        }
        response = translate_output(state, model="main-chat")
        assert response["object"] == "response"
        assert response["status"] == "completed"
        assert response["output"][0]["type"] == "message"
        assert response["output"][0]["content"][0]["text"] == "안녕하세요!"

    def test_tool_call_output(self):
        """도구 호출 출력 변환."""
        state = {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[{
                        "id": "call_123",
                        "name": "get_weather",
                        "args": {"city": "서울"},
                    }],
                )
            ]
        }
        response = translate_output(state, model="main-chat")
        assert any(
            item["type"] == "function_call"
            for item in response["output"]
        )

    def test_response_id_generation(self):
        """응답 ID가 resp_ 접두사를 가지는지 확인."""
        state = {"messages": [AIMessage(content="test")]}
        response = translate_output(state, model="main-chat")
        assert response["id"].startswith("resp_")
```

### 그래프 로더 테스트

```python
# tests/unit/test_graph_loader.py

import pytest
from langgraph_openai_api.graph.loader import load_graphs


class TestGraphLoader:
    """langgraph.json → 그래프 인스턴스 로딩 테스트."""

    def test_load_valid_config(self, tmp_path):
        """유효한 설정 파일 로딩."""
        config = tmp_path / "langgraph.json"
        config.write_text('{"graphs": {"test": "./graph.py:graph"}}')

        # ... 그래프 파일 생성 및 로딩 테스트 ...

    def test_invalid_module_path(self, tmp_path):
        """잘못된 모듈 경로 에러."""
        config = tmp_path / "langgraph.json"
        config.write_text('{"graphs": {"test": "./nonexistent.py:graph"}}')

        with pytest.raises(ImportError):
            load_graphs(str(config))

    def test_missing_variable(self, tmp_path):
        """존재하지 않는 변수명 에러."""
        # ... 테스트 ...
```

---

## 2. 통합 테스트

### FastAPI TestClient 사용

```python
# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from langgraph_openai_api.server.app import create_app


@pytest.fixture
def app():
    """테스트용 FastAPI 앱."""
    return create_app(config_path="tests/fixtures/langgraph.json")


@pytest.fixture
def client(app):
    """테스트 클라이언트."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """인증 헤더."""
    return {"Authorization": "Bearer test-api-key"}
```

### Responses API 통합 테스트

```python
# tests/integration/test_responses_api.py

import pytest


class TestResponsesAPI:
    """POST /v1/responses 통합 테스트."""

    def test_create_response_non_streaming(self, client, auth_headers):
        """비스트리밍 응답 생성."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "test-graph",
                "input": [{"role": "user", "content": "hello"}],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "response"
        assert data["status"] == "completed"
        assert len(data["output"]) > 0

    def test_create_response_streaming(self, client, auth_headers):
        """스트리밍 응답 생성."""
        with client.stream(
            "POST",
            "/v1/responses",
            json={
                "model": "test-graph",
                "input": [{"role": "user", "content": "hello"}],
                "stream": True,
            },
            headers=auth_headers,
        ) as response:
            assert response.status_code == 200
            events = list(response.iter_lines())
            event_types = [
                line.split("event: ")[1]
                for line in events
                if line.startswith("event: ")
            ]
            assert "response.created" in event_types
            assert "response.output_text.delta" in event_types
            assert "response.completed" in event_types

    def test_invalid_model(self, client, auth_headers):
        """존재하지 않는 모델 에러."""
        response = client.post(
            "/v1/responses",
            json={"model": "nonexistent", "input": "hello"},
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "model_not_found"

    def test_missing_input(self, client, auth_headers):
        """input 필드 누락 에러."""
        response = client.post(
            "/v1/responses",
            json={"model": "test-graph"},
            headers=auth_headers,
        )
        assert response.status_code == 400
```

### Models API 통합 테스트

```python
# tests/integration/test_models_api.py

class TestModelsAPI:
    """GET /v1/models 통합 테스트."""

    def test_list_models(self, client, auth_headers):
        """모델 목록 조회."""
        response = client.get("/v1/models", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "list"
        assert len(data["data"]) > 0
        assert all(m["object"] == "model" for m in data["data"])

    def test_get_model(self, client, auth_headers):
        """특정 모델 조회."""
        response = client.get("/v1/models/test-graph", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-graph"
        assert data["object"] == "model"

    def test_get_nonexistent_model(self, client, auth_headers):
        """존재하지 않는 모델 조회."""
        response = client.get("/v1/models/nonexistent", headers=auth_headers)
        assert response.status_code == 404
```

---

## 3. OpenAI SDK 호환성 테스트

OpenAI Python SDK를 사용하여 실제 호환성을 검증합니다.

```python
# tests/compatibility/test_openai_sdk.py

import pytest
from openai import OpenAI


@pytest.fixture
def openai_client(live_server):
    """실제 서버에 연결하는 OpenAI 클라이언트."""
    return OpenAI(
        api_key="test-api-key",
        base_url=f"http://localhost:{live_server.port}/v1",
    )


class TestOpenAISDKCompatibility:
    """OpenAI SDK 호환성 테스트."""

    def test_models_list(self, openai_client):
        """SDK로 모델 목록 조회."""
        models = openai_client.models.list()
        assert len(models.data) > 0

    def test_models_retrieve(self, openai_client):
        """SDK로 특정 모델 조회."""
        model = openai_client.models.retrieve("test-graph")
        assert model.id == "test-graph"

    def test_responses_create(self, openai_client):
        """SDK로 응답 생성."""
        response = openai_client.responses.create(
            model="test-graph",
            input="안녕하세요",
        )
        assert response.id.startswith("resp_")
        assert response.status == "completed"
        assert len(response.output) > 0
        assert response.output[0].content[0].text

    def test_responses_create_streaming(self, openai_client):
        """SDK로 스트리밍 응답 생성."""
        stream = openai_client.responses.create(
            model="test-graph",
            input="안녕하세요",
            stream=True,
        )

        text_deltas = []
        for event in stream:
            if event.type == "response.output_text.delta":
                text_deltas.append(event.delta)

        assert len(text_deltas) > 0
        full_text = "".join(text_deltas)
        assert len(full_text) > 0

    def test_responses_with_instructions(self, openai_client):
        """SDK로 instructions 포함 응답 생성."""
        response = openai_client.responses.create(
            model="test-graph",
            instructions="한국어로 답변해주세요",
            input="What is LangGraph?",
        )
        assert response.status == "completed"

    def test_responses_multi_turn(self, openai_client):
        """SDK로 멀티턴 대화."""
        # 첫 번째 요청
        response1 = openai_client.responses.create(
            model="test-graph",
            input="제 이름은 홍길동입니다.",
        )

        # 두 번째 요청 (이전 응답 참조)
        response2 = openai_client.responses.create(
            model="test-graph",
            input="제 이름이 뭐라고 했죠?",
            previous_response_id=response1.id,
        )
        assert response2.status == "completed"
```

---

## 4. 테스트 실행

### 전체 테스트

```bash
# 전체 실행
pytest tests/

# 단위 테스트만
pytest tests/unit/

# 통합 테스트만
pytest tests/integration/

# 호환성 테스트만 (서버 실행 필요)
pytest tests/compatibility/
```

### 커버리지

```bash
pytest tests/ --cov=langgraph_openai_api --cov-report=html
```

### CI 설정 (GitHub Actions)

```yaml
# .github/workflows/test.yml

name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[test]"
      - run: pytest tests/unit/ tests/integration/ --cov
```

---

## 5. 테스트용 그래프 Fixture

```python
# tests/fixtures/sample_graph.py

from typing import Annotated
from langchain_core.messages import AIMessage, AnyMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


async def echo_node(state: State) -> State:
    """입력을 그대로 반환하는 테스트용 노드."""
    last_msg = state["messages"][-1].content
    return {"messages": [AIMessage(content=f"Echo: {last_msg}")]}


builder = StateGraph(State)
builder.add_node("echo", echo_node)
builder.set_entry_point("echo")
builder.set_finish_point("echo")

graph = builder.compile()
```

```json
// tests/fixtures/langgraph.json
{
  "graphs": {
    "test-graph": "./sample_graph.py:graph"
  }
}
```

---

## 관련 문서

- [04. 내부 아키텍처](./04-architecture.md) - 모듈 구조 이해
- [05. API 명세](./05-api-specification.md) - 테스트할 엔드포인트 스펙
- [06. State 매핑](./06-state-mapping.md) - 변환 규칙 검증
- [07. 스트리밍](./07-streaming.md) - 스트리밍 이벤트 검증
