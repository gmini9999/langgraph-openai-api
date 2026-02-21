"""Test output translation from LangGraph state to OpenAI format."""

from langchain_core.messages import AIMessage, HumanMessage

from langgraph_openai_api.models.requests import CreateResponseRequest
from langgraph_openai_api.translators.output_translator import translate_output


def test_basic_text_output():
    state = {
        "messages": [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
        ]
    }
    req = CreateResponseRequest(model="test", input="Hello")
    resp = translate_output(state, req)

    assert resp.status == "completed"
    assert resp.model == "test"
    assert len(resp.output) == 1
    assert resp.output[0].type == "message"
    assert resp.output[0].content[0].text == "Hi there!"
    assert resp.id.startswith("resp_")


def test_tool_calls_output():
    state = {
        "messages": [
            HumanMessage(content="What's the weather?"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call_123",
                        "name": "get_weather",
                        "args": {"city": "Seoul"},
                    }
                ],
            ),
        ]
    }
    req = CreateResponseRequest(model="test", input="What's the weather?")
    resp = translate_output(state, req)

    assert len(resp.output) == 1
    fc = resp.output[0]
    assert fc.type == "function_call"
    assert fc.name == "get_weather"
    assert '"city"' in fc.arguments
    assert fc.call_id == "call_123"


def test_custom_output_mapper():
    from langgraph_openai_api.translators.state_mapper import register_output_mapper, _output_mappers

    def my_mapper(state):
        return state.get("custom_response", "default")

    register_output_mapper("custom-out", my_mapper)

    state = {"custom_response": "Custom output!", "messages": []}
    req = CreateResponseRequest(model="custom-out", input="test")
    resp = translate_output(state, req)

    assert resp.output[0].content[0].text == "Custom output!"

    _output_mappers.pop("custom-out", None)


def test_response_metadata_passthrough():
    state = {"messages": [AIMessage(content="OK")]}
    req = CreateResponseRequest(
        model="test",
        input="test",
        temperature=0.5,
        max_output_tokens=100,
        metadata={"user_id": "u1"},
    )
    resp = translate_output(state, req)

    assert resp.temperature == 0.5
    assert resp.max_output_tokens == 100
    assert resp.metadata == {"user_id": "u1"}


def test_custom_response_id():
    state = {"messages": [AIMessage(content="OK")]}
    req = CreateResponseRequest(model="test", input="test")
    resp = translate_output(state, req, response_id="resp_custom123")
    assert resp.id == "resp_custom123"
