# Basic Chat Example

A simple echo chat graph that demonstrates `langgraph-openai-api`.

## Setup

```bash
pip install langgraph-openai-api
```

## Run

```bash
cd examples/basic-chat
openlang dev
```

## Test

```bash
# Non-streaming
curl -X POST http://localhost:8000/v1/responses \
  -H "Content-Type: application/json" \
  -d '{"model": "echo-chat", "input": "Hello!"}'

# Streaming
curl -X POST http://localhost:8000/v1/responses \
  -H "Content-Type: application/json" \
  -d '{"model": "echo-chat", "input": "Hello!", "stream": true}'

# List models
curl http://localhost:8000/v1/models
```

## With OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dev")
response = client.responses.create(model="echo-chat", input="Hello!")
print(response.output[0].content[0].text)
```
