#!/usr/bin/env python3
"""
Logging utilities for MCP server
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import Request

try:
    from .config import LOG_FILE
except ImportError:
    from config import LOG_FILE


def log_request(request_info: dict):
    """Log request information to a text file."""
    try:
        # Ensure log directory exists
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Format timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Build log entry
        log_entry = f"""
{'='*80}
REQUEST LOG ENTRY - {request_id}
Timestamp: {timestamp}
{'='*80}

REQUEST INFORMATION:
{json.dumps(request_info, indent=2, default=str)}

{'='*80}
END OF ENTRY
{'='*80}

"""

        # Append to log file
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)

    except Exception as e:
        # If logging fails, print to stderr but don't break the main functionality
        print(f"Logging error: {e}", file=sys.stderr)


def log_http_request(request: Request, endpoint: str, additional_info: dict = None):
    """Log HTTP request information."""
    try:
        request_info = {
            "request_type": "http_request",
            "endpoint": endpoint,
            "method": request.method,
            "url": str(request.url),
            "client_info": {
                "ip_address": request.client.host if hasattr(request, 'client') and request.client else None,
                "port": request.client.port if hasattr(request, 'client') and request.client else None,
                "user_agent": request.headers.get('user-agent'),
                "accept": request.headers.get('accept'),
                "content_type": request.headers.get('content-type'),
                "host": request.headers.get('host'),
                "connection": request.headers.get('connection'),
                "referer": request.headers.get('referer'),
                "origin": request.headers.get('origin'),
            },
            "server_info": {
                "server_name": "simple-utils-server",
                "server_version": "1.0.0",
                "request_id": str(uuid.uuid4()),
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if additional_info:
            request_info.update(additional_info)

        log_request(request_info)

    except Exception as e:
        print(f"HTTP request logging error: {e}", file=sys.stderr)


def create_tool_log_info(name: str, arguments: dict[str, Any], request: Request = None) -> dict:
    """Create comprehensive logging information for tool calls."""
    return {
        "request_type": "tool_call",
        "tool_name": name,
        "arguments": arguments,
        "client_info": {
            "ip_address": request.client.host if request and hasattr(request, 'client') and request.client else None,
            "port": request.client.port if request and hasattr(request, 'client') and request.client else None,
            "user_agent": request.headers.get('user-agent') if request else None,
            "accept": request.headers.get('accept') if request else None,
            "content_type": request.headers.get('content-type') if request else None,
            "host": request.headers.get('host') if request else None,
            "connection": request.headers.get('connection') if request else None,
        } if request else {},
        "server_info": {
            "server_name": "simple-utils-server",
            "server_version": "1.0.0",
            "request_id": str(uuid.uuid4()),
        },
        "timestamp_start": datetime.now(timezone.utc).isoformat(),
    }