#!/usr/bin/env python3
"""
Authentication functions for MCP server
"""

from fastapi import HTTPException, Depends
from fastapi.security import APIKeyHeader

try:
    from .config import API_KEY, API_KEY_NAME
except ImportError:
    from config import API_KEY, API_KEY_NAME

# Create API key header dependency
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify the API key from request headers."""
    if API_KEY and api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    return api_key