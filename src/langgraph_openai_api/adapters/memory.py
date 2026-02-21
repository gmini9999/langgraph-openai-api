"""In-memory reference implementations of storage adapters (for development)."""

from __future__ import annotations

import time
from typing import Any

from ..models.common import generate_file_id, generate_vector_store_id
from .base import FileAdapter, VectorStoreAdapter


class InMemoryVectorStoreAdapter(VectorStoreAdapter):
    """In-memory vector store adapter for development/testing."""

    def __init__(self) -> None:
        self._stores: dict[str, dict[str, Any]] = {}
        self._files: dict[str, dict[str, dict[str, Any]]] = {}  # store_id -> {file_id -> file_data}

    async def create_vector_store(
        self,
        name: str | None = None,
        file_ids: list[str] | None = None,
        metadata: dict[str, str] | None = None,
        chunking_strategy: dict[str, Any] | None = None,
        expires_after: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        store_id = generate_vector_store_id()
        store = {
            "id": store_id,
            "name": name or "",
            "status": "completed",
            "created_at": int(time.time()),
            "file_counts": {"total": 0, "completed": 0, "failed": 0, "cancelled": 0, "in_progress": 0},
            "usage_bytes": 0,
            "metadata": metadata or {},
        }
        self._stores[store_id] = store
        self._files[store_id] = {}
        return store

    async def list_vector_stores(
        self,
        limit: int = 20,
        order: str = "desc",
        after: str | None = None,
        before: str | None = None,
    ) -> dict[str, Any]:
        stores = sorted(
            self._stores.values(),
            key=lambda s: s["created_at"],
            reverse=(order == "desc"),
        )
        if after:
            idx = next((i for i, s in enumerate(stores) if s["id"] == after), -1)
            stores = stores[idx + 1:] if idx >= 0 else stores
        stores = stores[:limit]
        return {
            "data": stores,
            "has_more": len(self._stores) > limit,
            "first_id": stores[0]["id"] if stores else None,
            "last_id": stores[-1]["id"] if stores else None,
        }

    async def get_vector_store(self, vector_store_id: str) -> dict[str, Any]:
        if vector_store_id not in self._stores:
            raise KeyError(f"Vector store '{vector_store_id}' not found")
        return self._stores[vector_store_id]

    async def modify_vector_store(
        self,
        vector_store_id: str,
        name: str | None = None,
        metadata: dict[str, str] | None = None,
        expires_after: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        store = await self.get_vector_store(vector_store_id)
        if name is not None:
            store["name"] = name
        if metadata is not None:
            store["metadata"] = metadata
        return store

    async def delete_vector_store(self, vector_store_id: str) -> dict[str, Any]:
        if vector_store_id in self._stores:
            del self._stores[vector_store_id]
            self._files.pop(vector_store_id, None)
        return {"id": vector_store_id, "object": "vector_store.deleted", "deleted": True}

    async def search_vector_store(
        self,
        vector_store_id: str,
        query: str,
        max_num_results: int = 10,
        filters: dict[str, Any] | None = None,
        ranking_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # In-memory implementation: return empty results (no real vector search)
        return {"data": []}

    async def add_file_to_vector_store(
        self,
        vector_store_id: str,
        file_id: str,
        chunking_strategy: dict[str, Any] | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        await self.get_vector_store(vector_store_id)  # Ensure exists
        file_data = {
            "id": file_id,
            "object": "vector_store.file",
            "vector_store_id": vector_store_id,
            "status": "completed",
            "created_at": int(time.time()),
        }
        if vector_store_id not in self._files:
            self._files[vector_store_id] = {}
        self._files[vector_store_id][file_id] = file_data
        store = self._stores[vector_store_id]
        store["file_counts"]["total"] += 1
        store["file_counts"]["completed"] += 1
        return file_data

    async def list_vector_store_files(
        self,
        vector_store_id: str,
        limit: int = 20,
        order: str = "desc",
        after: str | None = None,
    ) -> dict[str, Any]:
        files = list(self._files.get(vector_store_id, {}).values())
        files.sort(key=lambda f: f["created_at"], reverse=(order == "desc"))
        files = files[:limit]
        return {
            "data": files,
            "has_more": False,
            "first_id": files[0]["id"] if files else None,
            "last_id": files[-1]["id"] if files else None,
        }

    async def get_vector_store_file(
        self,
        vector_store_id: str,
        file_id: str,
    ) -> dict[str, Any]:
        files = self._files.get(vector_store_id, {})
        if file_id not in files:
            raise KeyError(f"File '{file_id}' not found in vector store '{vector_store_id}'")
        return files[file_id]

    async def delete_vector_store_file(
        self,
        vector_store_id: str,
        file_id: str,
    ) -> dict[str, Any]:
        files = self._files.get(vector_store_id, {})
        if file_id in files:
            del files[file_id]
            store = self._stores.get(vector_store_id)
            if store:
                store["file_counts"]["total"] = max(0, store["file_counts"]["total"] - 1)
                store["file_counts"]["completed"] = max(0, store["file_counts"]["completed"] - 1)
        return {"id": file_id, "object": "vector_store.file.deleted", "deleted": True}


class InMemoryFileAdapter(FileAdapter):
    """In-memory file adapter for development/testing."""

    def __init__(self) -> None:
        self._files: dict[str, dict[str, Any]] = {}
        self._contents: dict[str, bytes] = {}

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        purpose: str,
    ) -> dict[str, Any]:
        file_id = generate_file_id()
        file_data = {
            "id": file_id,
            "object": "file",
            "filename": filename,
            "bytes": len(file_content),
            "purpose": purpose,
            "created_at": int(time.time()),
        }
        self._files[file_id] = file_data
        self._contents[file_id] = file_content
        return file_data

    async def list_files(
        self,
        purpose: str | None = None,
        limit: int = 10000,
        order: str = "desc",
        after: str | None = None,
    ) -> dict[str, Any]:
        files = list(self._files.values())
        if purpose:
            files = [f for f in files if f["purpose"] == purpose]
        files.sort(key=lambda f: f["created_at"], reverse=(order == "desc"))
        if after:
            idx = next((i for i, f in enumerate(files) if f["id"] == after), -1)
            files = files[idx + 1:] if idx >= 0 else files
        files = files[:limit]
        return {"data": files, "has_more": False}

    async def get_file(self, file_id: str) -> dict[str, Any]:
        if file_id not in self._files:
            raise KeyError(f"File '{file_id}' not found")
        return self._files[file_id]

    async def delete_file(self, file_id: str) -> dict[str, Any]:
        self._files.pop(file_id, None)
        self._contents.pop(file_id, None)
        return {"id": file_id, "object": "file", "deleted": True}

    async def get_file_content(self, file_id: str) -> bytes:
        if file_id not in self._contents:
            raise KeyError(f"File '{file_id}' not found")
        return self._contents[file_id]
