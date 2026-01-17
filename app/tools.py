#!/usr/bin/env python3
"""
Tool definitions and implementations for MCP server
"""

import asyncio
import json
import math
import random
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Sequence

import pytz
from fastapi import Request
from mcp.server import Server
from mcp.types import Tool, TextContent

try:
    from .config import MAX_RANDOM_NUMBERS, COMMAND_TIMEOUT
    from .logging_utils import log_request, create_tool_log_info
except ImportError:
    from config import MAX_RANDOM_NUMBERS, COMMAND_TIMEOUT
    from logging_utils import log_request, create_tool_log_info

# Create the MCP server instance
server = Server("simple-utils-server")


async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_current_time",
            description="Get the current time in UTC and local timezone",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_current_date",
            description="Get the current date in various formats",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "Date format: 'iso', 'us', 'european', or 'unix'",
                        "enum": ["iso", "us", "european", "unix"],
                        "default": "iso"
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="calculate",
            description="Perform basic mathematical calculations",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'sin(pi/2)')"
                    }
                },
                "required": ["expression"],
            },
        ),
        Tool(
            name="get_timezone_info",
            description="Get information about a timezone",
            inputSchema={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone name (e.g., 'UTC', 'America/New_York', 'Europe/London')",
                        "default": "UTC"
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="generate_random_number",
            description="Generate a random number within a specified range",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_value": {
                        "type": "number",
                        "description": "Minimum value (inclusive)",
                        "default": 1
                    },
                    "max_value": {
                        "type": "number",
                        "description": "Maximum value (inclusive)",
                        "default": 100
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of random numbers to generate",
                        "default": 1,
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="execute_command",
            description="Execute a shell command and return the output. WARNING: Use with caution as this can execute arbitrary commands.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute (e.g., 'ls -la', 'echo hello', 'python --version')"
                    },
                    "working_directory": {
                        "type": "string",
                        "description": "Working directory for the command (optional, defaults to current directory)",
                        "default": None
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (optional, defaults to 30 seconds)",
                        "default": 30
                    }
                },
                "required": ["command"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any], request: Request = None) -> Sequence[TextContent]:
    """Handle tool calls."""

    # Prepare comprehensive logging information
    log_info = create_tool_log_info(name, arguments, request)

    if name == "get_current_time":
        now = datetime.now(timezone.utc)
        local_now = datetime.now()

        result = {
            "utc_time": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "local_time": local_now.strftime("%Y-%m-%d %H:%M:%S"),
            "unix_timestamp": int(now.timestamp()),
            "iso_format": now.isoformat(),
        }

        # Log the response
        log_info["timestamp_end"] = datetime.now(timezone.utc).isoformat()
        log_info["response"] = result
        log_info["success"] = True
        log_request(log_info)

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    elif name == "get_current_date":
        now = datetime.now()
        format_type = arguments.get("format", "iso")

        if format_type == "us":
            formatted_date = now.strftime("%m/%d/%Y")
        elif format_type == "european":
            formatted_date = now.strftime("%d/%m/%Y")
        elif format_type == "unix":
            formatted_date = str(int(now.timestamp()))
        else:  # iso
            formatted_date = now.strftime("%Y-%m-%d")

        result = {
            "date": formatted_date,
            "format": format_type,
            "unix_timestamp": int(now.timestamp()),
            "iso_format": now.strftime("%Y-%m-%d")
        }

        # Log the response
        log_info["timestamp_end"] = datetime.now(timezone.utc).isoformat()
        log_info["response"] = result
        log_info["success"] = True
        log_request(log_info)

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    elif name == "calculate":
        expression = arguments.get("expression", "")

        if not expression.strip():
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Expression is required"}, indent=2)
            )]

        try:
            # Safe evaluation of mathematical expressions
            # Only allow safe mathematical operations
            allowed_names = {
                k: v for k, v in math.__dict__.items() if not k.startswith("__")
            }
            allowed_names.update({"__builtins__": {}})

            result_value = eval(expression, allowed_names)
            result = {
                "expression": expression,
                "result": result_value,
                "type": type(result_value).__name__
            }

        except Exception as e:
            result = {
                "expression": expression,
                "error": f"Calculation error: {str(e)}",
                "type": "error"
            }
            log_info["success"] = False
            log_info["error"] = str(e)

        # Log the response
        log_info["timestamp_end"] = datetime.now(timezone.utc).isoformat()
        log_info["response"] = result
        log_request(log_info)

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    elif name == "get_timezone_info":
        timezone_name = arguments.get("timezone", "UTC")

        try:
            tz = pytz.timezone(timezone_name)
            now = datetime.now(tz)

            result = {
                "timezone": timezone_name,
                "current_time": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                "utc_offset": now.strftime("%z"),
                "is_dst": now.dst() != datetime.timedelta(0),
                "timezone_info": str(tz)
            }

        except pytz.exceptions.UnknownTimeZoneError:
            result = {
                "error": f"Unknown timezone: {timezone_name}",
                "available_timezones": "Use pytz.common_timezones for valid timezone names"
            }
            log_info["success"] = False
            log_info["error"] = f"Unknown timezone: {timezone_name}"

        # Log the response
        log_info["timestamp_end"] = datetime.now(timezone.utc).isoformat()
        log_info["response"] = result
        log_request(log_info)

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    elif name == "generate_random_number":
        min_value = arguments.get("min_value", 1)
        max_value = arguments.get("max_value", 100)
        count = arguments.get("count", 1)

        # Validate inputs
        if not isinstance(min_value, (int, float)):
            return [TextContent(
                type="text",
                text=json.dumps({"error": "min_value must be a number"}, indent=2)
            )]
        if not isinstance(max_value, (int, float)):
            return [TextContent(
                type="text",
                text=json.dumps({"error": "max_value must be a number"}, indent=2)
            )]
        if min_value >= max_value:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "min_value must be less than max_value"}, indent=2)
            )]
        if not isinstance(count, int) or count < 1 or count > MAX_RANDOM_NUMBERS:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"count must be an integer between 1 and {MAX_RANDOM_NUMBERS}"}, indent=2)
            )]

        try:
            if count == 1:
                # Single random number
                random_number = random.uniform(min_value, max_value)
                result = {
                    "random_number": random_number,
                    "min_value": min_value,
                    "max_value": max_value,
                    "type": "single"
                }
            else:
                # Multiple random numbers
                random_numbers = [random.uniform(min_value, max_value) for _ in range(count)]
                result = {
                    "random_numbers": random_numbers,
                    "count": count,
                    "min_value": min_value,
                    "max_value": max_value,
                    "type": "multiple"
                }

        except Exception as e:
            result = {"error": f"Random number generation error: {str(e)}"}
            log_info["success"] = False
            log_info["error"] = str(e)

        # Log the response
        log_info["timestamp_end"] = datetime.now(timezone.utc).isoformat()
        log_info["response"] = result
        log_request(log_info)

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    elif name == "execute_command":
        command = arguments.get("command", "")
        working_directory = arguments.get("working_directory")
        timeout = arguments.get("timeout", COMMAND_TIMEOUT)

        if not command.strip():
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Command is required"}, indent=2)
            )]

        try:
            # Execute the command
            process = subprocess.run(
                shlex.split(command),
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_directory
            )

            result = {
                "command": command,
                "return_code": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "success": process.returncode == 0,
                "working_directory": working_directory or "current directory",
                "timeout_used": timeout
            }

        except subprocess.TimeoutExpired:
            result = {
                "command": command,
                "error": f"Command timed out after {timeout} seconds",
                "timeout": timeout
            }
            log_info["success"] = False
            log_info["error"] = f"Command timeout: {timeout}s"

        except Exception as e:
            result = {
                "command": command,
                "error": f"Command execution error: {str(e)}"
            }
            log_info["success"] = False
            log_info["error"] = str(e)

        # Log the response
        log_info["timestamp_end"] = datetime.now(timezone.utc).isoformat()
        log_info["response"] = result
        log_request(log_info)

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    else:
        error_result = {"error": f"Unknown tool: {name}"}

        # Log the unknown tool error
        log_info["timestamp_end"] = datetime.now(timezone.utc).isoformat()
        log_info["response"] = error_result
        log_info["success"] = False
        log_info["error"] = f"Unknown tool: {name}"
        log_request(log_info)

        return [TextContent(
            type="text",
            text=json.dumps(error_result, indent=2)
        )]