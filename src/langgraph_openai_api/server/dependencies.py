"""FastAPI dependencies: authentication, adapter injection."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


def is_dev_mode() -> bool:
    """Check if running in development mode."""
    return os.environ.get("OPENLANG_DEV", "false").lower() == "true"


def get_api_keys() -> set[str]:
    """Return configured API keys from environment."""
    keys = os.environ.get("OPENLANG_API_KEY", "")
    return {k.strip() for k in keys.split(",") if k.strip()}


async def verify_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """Verify Bearer token authentication."""
    if is_dev_mode():
        return credentials.credentials if credentials else "dev"

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "message": "You didn't provide an API key.",
                    "type": "authentication_error",
                    "param": None,
                    "code": "missing_api_key",
                }
            },
        )

    api_keys = get_api_keys()
    if not api_keys:
        # No keys configured in non-dev mode — reject
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "message": "API key not configured on server.",
                    "type": "authentication_error",
                    "param": None,
                    "code": "missing_api_key",
                }
            },
        )

    if credentials.credentials not in api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "message": "Incorrect API key provided.",
                    "type": "authentication_error",
                    "param": None,
                    "code": "invalid_api_key",
                }
            },
        )

    return credentials.credentials
