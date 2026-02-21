"""Test input translation from OpenAI format to LangGraph state."""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from langgraph_openai_api.models.requests import CreateResponseRequest
from langgraph_openai_api.translators.input_translator import translate_input
from langgraph_openai_api.translators.state_mapper import register_input_mapper


def test_string_input():
    req = CreateResponseRequest(model="test", input="Hello")
    state = translate_input(req)
    assert len(state["messages"]) == 1
    assert isinstance(state["messages"][0], HumanMessage)
    assert state["messages"][0].content == "Hello"


def test_message_array_input():
    req = CreateResponseRequest(
        model="test",
        input=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you?"},
        ],
    )
    state = translate_input(req)
    assert len(state["messages"]) == 3
    assert isinstance(state["messages"][0], HumanMessage)
    assert isinstance(state["messages"][1], AIMessage)
    assert isinstance(state["messages"][2], HumanMessage)


def test_system_message():
    req = CreateResponseRequest(
        model="test",
        input=[{"role": "system", "content": "You are helpful"}],
    )
    state = translate_input(req)
    assert isinstance(state["messages"][0], SystemMessage)


def test_instructions_prepended():
    req = CreateResponseRequest(
        model="test",
        input=[{"role": "user", "content": "Hello"}],
        instructions="Be concise",
    )
    state = translate_input(req)
    assert len(state["messages"]) == 2
    assert isinstance(state["messages"][0], SystemMessage)
    assert state["messages"][0].content == "Be concise"
    assert isinstance(state["messages"][1], HumanMessage)


def test_multimodal_content():
    req = CreateResponseRequest(
        model="test",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Describe this"},
                    {"type": "input_image", "image_url": "https://example.com/img.png"},
                ],
            }
        ],
    )
    state = translate_input(req)
    msg = state["messages"][0]
    assert isinstance(msg, HumanMessage)
    assert isinstance(msg.content, list)
    assert msg.content[0]["type"] == "text"
    assert msg.content[1]["type"] == "image_url"
    assert msg.content[1]["image_url"]["url"] == "https://example.com/img.png"


def test_custom_input_mapper():
    def my_mapper(data):
        return {
            "messages": data["messages"],
            "custom_field": "custom_value",
        }

    register_input_mapper("custom-graph", my_mapper)

    req = CreateResponseRequest(model="custom-graph", input="Hello")
    state = translate_input(req)
    assert "custom_field" in state
    assert state["custom_field"] == "custom_value"

    # Clean up
    from langgraph_openai_api.translators.state_mapper import _input_mappers
    _input_mappers.pop("custom-graph", None)


def test_developer_role():
    req = CreateResponseRequest(
        model="test",
        input=[{"role": "developer", "content": "System instructions"}],
    )
    state = translate_input(req)
    assert isinstance(state["messages"][0], SystemMessage)
