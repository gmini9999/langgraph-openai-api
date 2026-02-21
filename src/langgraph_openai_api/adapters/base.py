"""Abstract base classes for storage adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class VectorStoreAdapter(ABC):
    """Vector store CRUD + search adapter interface."""

    @abstractmethod
    async def create_vector_store(
        self,
        name: str | None = None,
        file_ids: list[str] | None = None,
        metadata: dict[str, str] | None = None,
        chunking_strategy: dict[str, Any] | None = None,
        expires_after: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def list_vector_stores(
        self,
        limit: int = 20,
        order: str = "desc",
        after: str | None = None,
        before: str | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def get_vector_store(self, vector_store_id: str) -> dict[str, Any]: ...

    @abstractmethod
    async def modify_vector_store(
        self,
        vector_store_id: str,
        name: str | None = None,
        metadata: dict[str, str] | None = None,
        expires_after: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def delete_vector_store(self, vector_store_id: str) -> dict[str, Any]: ...

    @abstractmethod
    async def search_vector_store(
        self,
        vector_store_id: str,
        query: str,
        max_num_results: int = 10,
        filters: dict[str, Any] | None = None,
        ranking_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def add_file_to_vector_store(
        self,
        vector_store_id: str,
        file_id: str,
        chunking_strategy: dict[str, Any] | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def list_vector_store_files(
        self,
        vector_store_id: str,
        limit: int = 20,
        order: str = "desc",
        after: str | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def get_vector_store_file(
        self,
        vector_store_id: str,
        file_id: str,
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def delete_vector_store_file(
        self,
        vector_store_id: str,
        file_id: str,
    ) -> dict[str, Any]: ...


class FileAdapter(ABC):
    """File upload/management adapter interface."""

    @abstractmethod
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        purpose: str,
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def list_files(
        self,
        purpose: str | None = None,
        limit: int = 10000,
        order: str = "desc",
        after: str | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def get_file(self, file_id: str) -> dict[str, Any]: ...

    @abstractmethod
    async def delete_file(self, file_id: str) -> dict[str, Any]: ...

    @abstractmethod
    async def get_file_content(self, file_id: str) -> bytes: ...
