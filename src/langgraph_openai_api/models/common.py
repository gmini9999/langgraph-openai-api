"""Common models and ID generation utilities."""

from __future__ import annotations

import secrets
import time
from typing import Any

from pydantic import BaseModel, Field


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    return f"{prefix}{secrets.token_hex(12)}"


def generate_response_id() -> str:
    return generate_id("resp_")


def generate_message_id() -> str:
    return generate_id("msg_")


def generate_function_call_id() -> str:
    return generate_id("fc_")


def generate_vector_store_id() -> str:
    return generate_id("vs_")


def generate_file_id() -> str:
    return generate_id("file_")


def unix_timestamp() -> int:
    return int(time.time())


class ListResponse(BaseModel):
    """Common paginated list response."""

    object: str = "list"
    data: list[Any] = Field(default_factory=list)
    first_id: str | None = None
    last_id: str | None = None
    has_more: bool = False
