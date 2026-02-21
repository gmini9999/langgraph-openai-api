# 예제: RAG + Vector Store 어댑터

## 개요

LangGraph RAG 그래프를 `langgraph-openai-api`로 서빙하고,
벡터 스토어 어댑터를 구현하여 OpenAI의 Vector Stores API를 통해 문서를 관리하는 예제입니다.

---

## 프로젝트 구조

```
rag-example/
├── langgraph.json
├── .env
├── pyproject.toml
├── src/
│   └── agents/
│       └── rag/
│           ├── __init__.py
│           ├── graph.py            # RAG 그래프
│           ├── state.py            # InputState / FullState
│           └── nodes.py            # retrieve, generate 노드
├── adapters/
│   ├── __init__.py
│   └── qdrant_adapter.py          # Qdrant 벡터 스토어 어댑터
└── app.py                          # 앱 설정 (어댑터 등록)
```

---

## 1. State 정의

```python
# src/agents/rag/state.py

from typing import Annotated, Any
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class InputState(TypedDict, total=False):
    """외부 입력 필드."""
    messages: Annotated[list[AnyMessage], add_messages]
    collection_targets: list[str]  # 검색 대상 벡터 스토어 ID 목록


class RAGState(InputState):
    """내부 처리 필드 포함."""
    # 검색 결과
    retrieved_chunks: list[dict[str, Any]]
    rag_context: str

    # 최종 응답
    response: str
```

---

## 2. RAG 그래프

```python
# src/agents/rag/graph.py

from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph

from .state import InputState, RAGState

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


async def retrieve(state: RAGState) -> RAGState:
    """벡터 스토어에서 관련 문서를 검색합니다."""
    query = state["messages"][-1].content
    targets = state.get("collection_targets", [])

    # 실제 구현에서는 벡터 스토어 어댑터를 통해 검색
    # 여기서는 예시로 직접 호출
    from adapters.qdrant_adapter import search_documents

    chunks = await search_documents(query, targets)

    context = "\n\n".join(
        f"[{c['filename']}]\n{c['text']}" for c in chunks
    )

    return {
        "retrieved_chunks": chunks,
        "rag_context": context,
    }


async def generate(state: RAGState) -> RAGState:
    """검색 결과를 기반으로 응답을 생성합니다."""
    context = state.get("rag_context", "")
    messages = list(state["messages"])

    system_prompt = f"""아래 참고 문서를 기반으로 사용자 질문에 답변해주세요.
참고 문서에 없는 내용은 모른다고 답변해주세요.

## 참고 문서
{context}
"""
    messages = [SystemMessage(content=system_prompt)] + messages

    response = await llm.ainvoke(messages)
    return {
        "messages": [response],
        "response": response.content,
    }


# 그래프 빌드
builder = StateGraph(RAGState, input=InputState)
builder.add_node("retrieve", retrieve)
builder.add_node("generate", generate)
builder.add_edge("retrieve", "generate")
builder.set_entry_point("retrieve")
builder.set_finish_point("generate")

graph = builder.compile()


# 커스텀 매퍼 등록
from langgraph_openai_api.translators.state_mapper import (
    register_input_mapper,
    register_output_mapper,
)


def input_mapper(request: dict) -> dict:
    """OpenAI 요청을 RAG State로 변환합니다."""
    messages = request["messages"]
    metadata = request.get("metadata", {})

    # metadata에서 검색 대상 벡터 스토어 전달
    collection_targets = metadata.get("vector_store_ids", [])

    # 또는 tools에서 file_search 설정 추출
    for tool in request.get("tools", []):
        if tool.get("type") == "file_search":
            collection_targets.extend(tool.get("vector_store_ids", []))

    return {
        "messages": messages,
        "collection_targets": collection_targets,
    }


def output_mapper(state: dict) -> str:
    """RAG State에서 응답 텍스트를 추출합니다."""
    return state.get("response", state["messages"][-1].content)


register_input_mapper("rag-agent", input_mapper)
register_output_mapper("rag-agent", output_mapper)
```

---

## 3. Qdrant 벡터 스토어 어댑터

```python
# adapters/qdrant_adapter.py

import time
import uuid
from typing import Any

from langchain_openai import OpenAIEmbeddings
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from langgraph_openai_api.adapters.base import VectorStoreAdapter


class QdrantVectorStoreAdapter(VectorStoreAdapter):
    """Qdrant 기반 벡터 스토어 어댑터."""

    def __init__(self, url: str = "http://localhost:6333"):
        self.client = AsyncQdrantClient(url=url)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self._metadata: dict[str, dict] = {}  # 벡터 스토어 메타데이터 캐시

    def _gen_id(self, prefix: str = "vs") -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    async def create_vector_store(self, name=None, file_ids=None, metadata=None, **kwargs):
        store_id = self._gen_id("vs")
        collection_name = f"store_{store_id}"

        await self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )

        store_meta = {
            "id": store_id,
            "name": name or "",
            "status": "completed",
            "created_at": int(time.time()),
            "file_counts": {"total": 0, "completed": 0, "failed": 0, "cancelled": 0, "in_progress": 0},
            "usage_bytes": 0,
            "metadata": metadata or {},
            "_collection_name": collection_name,
        }
        self._metadata[store_id] = store_meta
        return store_meta

    async def list_vector_stores(self, limit=20, order="desc", **kwargs):
        stores = sorted(
            self._metadata.values(),
            key=lambda s: s["created_at"],
            reverse=(order == "desc"),
        )[:limit]
        return {
            "data": stores,
            "has_more": len(self._metadata) > limit,
            "first_id": stores[0]["id"] if stores else None,
            "last_id": stores[-1]["id"] if stores else None,
        }

    async def get_vector_store(self, vector_store_id):
        if vector_store_id not in self._metadata:
            raise ValueError(f"Vector store {vector_store_id} not found")
        return self._metadata[vector_store_id]

    async def modify_vector_store(self, vector_store_id, name=None, metadata=None, **kwargs):
        store = self._metadata[vector_store_id]
        if name is not None:
            store["name"] = name
        if metadata is not None:
            store["metadata"] = metadata
        return store

    async def delete_vector_store(self, vector_store_id):
        store = self._metadata.pop(vector_store_id, None)
        if store:
            await self.client.delete_collection(store["_collection_name"])
        return {"id": vector_store_id, "deleted": True}

    async def search_vector_store(self, vector_store_id, query, max_num_results=10, **kwargs):
        store = self._metadata[vector_store_id]
        collection_name = store["_collection_name"]

        query_vector = await self.embeddings.aembed_query(query)

        results = await self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=max_num_results,
        )

        return {
            "data": [
                {
                    "file_id": r.payload.get("file_id", ""),
                    "filename": r.payload.get("filename", ""),
                    "score": r.score,
                    "content": [{"type": "text", "text": r.payload.get("text", "")}],
                    "attributes": r.payload.get("attributes", {}),
                }
                for r in results
            ]
        }

    async def add_file_to_vector_store(self, vector_store_id, file_id, **kwargs):
        # 실제 구현: 파일 콘텐츠를 읽어서 청킹 후 임베딩하여 저장
        store = self._metadata[vector_store_id]
        store["file_counts"]["total"] += 1
        store["file_counts"]["completed"] += 1

        return {
            "id": file_id,
            "object": "vector_store.file",
            "vector_store_id": vector_store_id,
            "status": "completed",
            "created_at": int(time.time()),
        }

    async def list_vector_store_files(self, vector_store_id, **kwargs):
        # 실제 구현: Qdrant에서 파일 목록 조회
        return {"data": [], "has_more": False}

    async def get_vector_store_file(self, vector_store_id, file_id):
        return {
            "id": file_id,
            "object": "vector_store.file",
            "vector_store_id": vector_store_id,
            "status": "completed",
        }

    async def delete_vector_store_file(self, vector_store_id, file_id):
        return {"id": file_id, "deleted": True}


# 편의 함수 (그래프에서 직접 호출)
_adapter: QdrantVectorStoreAdapter | None = None


async def search_documents(query: str, store_ids: list[str]) -> list[dict]:
    """여러 벡터 스토어에서 검색합니다."""
    if not _adapter:
        return []

    results = []
    for store_id in store_ids:
        try:
            search_result = await _adapter.search_vector_store(store_id, query)
            results.extend(search_result["data"])
        except Exception:
            continue

    # 점수 기준 정렬
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:10]
```

---

## 4. 앱 설정

```python
# app.py

from langgraph_openai_api.server.app import create_app
from adapters.qdrant_adapter import QdrantVectorStoreAdapter

adapter = QdrantVectorStoreAdapter(url="http://localhost:6333")

app = create_app(
    config_path="./langgraph.json",
    vector_store_adapter=adapter,
)
```

---

## 5. 설정 파일

```json
// langgraph.json
{
  "dependencies": ["."],
  "graphs": {
    "rag-agent": "./src/agents/rag/graph.py:graph"
  },
  "env": ".env"
}
```

```bash
# .env
OPENAI_API_KEY=sk-...
QDRANT_URL=http://localhost:6333
```

---

## 6. 실행 및 API 호출

### 서버 실행

```bash
# Qdrant 시작
docker run -p 6333:6333 qdrant/qdrant

# 개발 서버 시작
openlang dev
```

### 벡터 스토어 생성 및 파일 업로드

```python
from openai import OpenAI

client = OpenAI(
    api_key="not-needed",
    base_url="http://localhost:8000/v1",
)

# 1. 파일 업로드
file = client.files.create(
    file=open("knowledge_base.pdf", "rb"),
    purpose="assistants",
)

# 2. 벡터 스토어 생성
vector_store = client.vector_stores.create(
    name="Knowledge Base",
    file_ids=[file.id],
)

# 3. RAG 질문
response = client.responses.create(
    model="rag-agent",
    input="LangGraph의 주요 기능은 무엇인가요?",
    tools=[{
        "type": "file_search",
        "vector_store_ids": [vector_store.id],
    }],
)
print(response.output[0].content[0].text)
```

### curl로 벡터 스토어 관리

```bash
# 벡터 스토어 생성
curl -X POST http://localhost:8000/v1/vector_stores \
  -H "Content-Type: application/json" \
  -d '{"name": "My Knowledge Base"}'

# 벡터 스토어 목록
curl http://localhost:8000/v1/vector_stores

# 벡터 스토어 검색
curl -X POST http://localhost:8000/v1/vector_stores/vs_abc123/search \
  -H "Content-Type: application/json" \
  -d '{"query": "LangGraph 사용법", "max_num_results": 5}'
```

---

## 관련 문서

- [08. 스토리지 어댑터](../08-storage-adapters.md) - 어댑터 인터페이스 상세
- [06. State 매핑](../06-state-mapping.md) - InputState/FullState 패턴
- [05. API 명세](../05-api-specification.md) - Vector Stores API 스펙
- [예제: 기본 채팅 그래프](./basic-chat-graph.md) - 기본 예제
- [예제: 멀티 그래프](./multi-model-serving.md) - 멀티 모델 예제
