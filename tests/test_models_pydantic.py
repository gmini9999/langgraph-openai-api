"""Test Pydantic model serialization/deserialization."""

from langgraph_openai_api.models.common import (
    ListResponse,
    generate_file_id,
    generate_function_call_id,
    generate_message_id,
    generate_response_id,
    generate_vector_store_id,
)
from langgraph_openai_api.models.errors import ErrorDetail, ErrorResponse
from langgraph_openai_api.models.files import FileObject
from langgraph_openai_api.models.models import ModelListResponse, ModelObject
from langgraph_openai_api.models.requests import CreateResponseRequest
from langgraph_openai_api.models.responses import (
    FunctionCallOutputItem,
    MessageOutputItem,
    OutputText,
    ResponseObject,
    Usage,
)
from langgraph_openai_api.models.vector_stores import VectorStoreObject


def test_generate_ids():
    resp_id = generate_response_id()
    assert resp_id.startswith("resp_")

    msg_id = generate_message_id()
    assert msg_id.startswith("msg_")

    fc_id = generate_function_call_id()
    assert fc_id.startswith("fc_")

    vs_id = generate_vector_store_id()
    assert vs_id.startswith("vs_")

    file_id = generate_file_id()
    assert file_id.startswith("file_")


def test_create_response_request():
    req = CreateResponseRequest(
        model="test-model",
        input="Hello",
        stream=True,
        instructions="Be helpful",
        temperature=0.7,
    )
    assert req.model == "test-model"
    assert req.input == "Hello"
    assert req.stream is True
    assert req.instructions == "Be helpful"

    data = req.model_dump()
    assert data["model"] == "test-model"
    assert data["stream"] is True


def test_create_response_request_with_messages():
    req = CreateResponseRequest(
        model="test-model",
        input=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ],
    )
    assert isinstance(req.input, list)
    assert len(req.input) == 2


def test_response_object():
    resp = ResponseObject(
        id="resp_123",
        created_at=1700000000,
        status="completed",
        model="test-model",
        output=[
            MessageOutputItem(
                id="msg_123",
                content=[OutputText(text="Hello!")],
            )
        ],
        usage=Usage(input_tokens=10, output_tokens=20, total_tokens=30),
    )
    data = resp.model_dump()
    assert data["id"] == "resp_123"
    assert data["object"] == "response"
    assert data["output"][0]["type"] == "message"
    assert data["output"][0]["content"][0]["text"] == "Hello!"
    assert data["usage"]["total_tokens"] == 30


def test_function_call_output():
    fc = FunctionCallOutputItem(
        id="fc_123",
        call_id="call_abc",
        name="get_weather",
        arguments='{"city": "Seoul"}',
    )
    data = fc.model_dump()
    assert data["type"] == "function_call"
    assert data["name"] == "get_weather"


def test_model_object():
    model = ModelObject(id="main-chat", created=1700000000)
    assert model.owned_by == "langgraph-openai-api"

    ml = ModelListResponse(data=[model])
    assert ml.object == "list"
    assert len(ml.data) == 1


def test_error_response():
    err = ErrorResponse(
        error=ErrorDetail(
            message="Not found",
            type="not_found_error",
            code="model_not_found",
        )
    )
    data = err.model_dump()
    assert data["error"]["type"] == "not_found_error"


def test_list_response():
    lr = ListResponse(data=[1, 2, 3], first_id="a", last_id="c", has_more=True)
    assert lr.object == "list"
    assert lr.has_more is True


def test_vector_store_object():
    vs = VectorStoreObject(id="vs_123", name="Test Store")
    assert vs.object == "vector_store"
    assert vs.status == "completed"


def test_file_object():
    f = FileObject(id="file_123", filename="test.txt", bytes=100, purpose="assistants")
    assert f.object == "file"
