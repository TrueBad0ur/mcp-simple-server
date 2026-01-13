#!/usr/bin/env python3
"""
HTTP/SSE wrapper for MCP server
Allows remote connections via HTTP Server-Sent Events
"""

import asyncio
import json
import shlex
import random
import os
import sys
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
import uvicorn
from mcp.server import Server
from mcp.types import Tool, TextContent
import math
from typing import Any, Sequence


# Create the MCP server instance
server = Server("simple-utils-server")


# Logging configuration
LOG_FILE = "logs/requests_log.txt"

# Authentication configuration
API_KEY = os.getenv("MCP_API_KEY")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify the API key from request headers."""
    if API_KEY and api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    return api_key

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
                "x_forwarded_for": request.headers.get('x-forwarded-for'),
                "x_real_ip": request.headers.get('x-real-ip'),
            },
            "server_info": {
                "server_name": "simple-utils-server",
                "server_version": "1.0.0",
                "request_id": str(uuid.uuid4()),
            },
            "timestamp_start": datetime.now(timezone.utc).isoformat(),
        }

        if additional_info:
            request_info.update(additional_info)

        log_request(request_info)

    except Exception as e:
        print(f"HTTP logging error: {e}", file=sys.stderr)


@server.list_tools()
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
    log_info = {
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
        
        formats = {
            "iso": now.strftime("%Y-%m-%d"),
            "us": now.strftime("%m/%d/%Y"),
            "european": now.strftime("%d/%m/%Y"),
            "unix": str(int(now.timestamp())),
        }
        
        result = {
            "date": formats.get(format_type, formats["iso"]),
            "all_formats": formats,
            "day_of_week": now.strftime("%A"),
            "day_of_year": now.timetuple().tm_yday,
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
        
        if not expression:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Expression is required"}, indent=2)
            )]
        
        # Safe evaluation with math functions
        safe_dict = {
            "__builtins__": {},
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e,
            "floor": math.floor,
            "ceil": math.ceil,
        }
        
        try:
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            final_result = {
                "expression": expression,
                "result": result,
                "type": type(result).__name__
            }

            # Log the response
            log_info["timestamp_end"] = datetime.now(timezone.utc).isoformat()
            log_info["response"] = final_result
            log_info["success"] = True
            log_request(log_info)

            return [TextContent(
                type="text",
                text=json.dumps(final_result, indent=2)
            )]
        except Exception as e:
            error_result = {"error": f"Calculation error: {str(e)}"}

            # Log the error
            log_info["timestamp_end"] = datetime.now(timezone.utc).isoformat()
            log_info["response"] = error_result
            log_info["success"] = False
            log_info["error"] = str(e)
            log_request(log_info)

            return [TextContent(
                type="text",
                text=json.dumps(error_result, indent=2)
            )]
    
    elif name == "get_timezone_info":
        timezone_name = arguments.get("timezone", "UTC")
        
        try:
            import zoneinfo
            tz = zoneinfo.ZoneInfo(timezone_name)
            now = datetime.now(tz)

            result = {
                "timezone": timezone_name,
                "current_time": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                "utc_offset": str(now.utcoffset()),
                "is_dst": now.dst() is not None and now.dst().total_seconds() != 0,
            }
            success = True
        except Exception as e:
            result = {
                "timezone": timezone_name,
                "error": f"Invalid timezone: {str(e)}",
                "note": "Try 'UTC', 'America/New_York', 'Europe/London', etc."
            }
            success = False

        # Log the response
        log_info["timestamp_end"] = datetime.now(timezone.utc).isoformat()
        log_info["response"] = result
        log_info["success"] = success
        if not success:
            log_info["error"] = str(e)
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
        if not isinstance(count, int) or count < 1 or count > 100:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "count must be an integer between 1 and 100"}, indent=2)
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

            # Log the response
            log_info["timestamp_end"] = datetime.now(timezone.utc).isoformat()
            log_info["response"] = result
            log_info["success"] = True
            log_request(log_info)

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        except Exception as e:
            error_result = {"error": f"Random number generation error: {str(e)}"}

            # Log the error
            log_info["timestamp_end"] = datetime.now(timezone.utc).isoformat()
            log_info["response"] = error_result
            log_info["success"] = False
            log_info["error"] = str(e)
            log_request(log_info)

            return [TextContent(
                type="text",
                text=json.dumps(error_result, indent=2)
            )]
    
    elif name == "execute_command":
        command = arguments.get("command", "")
        working_directory = arguments.get("working_directory")
        timeout = arguments.get("timeout", 30)
        
        if not command:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Command is required"}, indent=2)
            )]
        
        try:
            # Parse command into list for subprocess
            # Use shlex.split to handle quoted arguments properly
            try:
                cmd_parts = shlex.split(command)
            except ValueError:
                # If shlex fails, try simple split (for Windows compatibility)
                cmd_parts = command.split()
            
            # Execute command with timeout
            process = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *cmd_parts,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=working_directory if working_directory else None,
                ),
                timeout=timeout
            )
            
            stdout, stderr = await process.communicate()
            
            result = {
                "command": command,
                "return_code": process.returncode,
                "stdout": stdout.decode('utf-8', errors='replace') if stdout else "",
                "stderr": stderr.decode('utf-8', errors='replace') if stderr else "",
                "success": process.returncode == 0,
            }

            # Log the response
            log_info["timestamp_end"] = datetime.now(timezone.utc).isoformat()
            log_info["response"] = result
            log_info["success"] = result["success"]
            log_request(log_info)

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        except asyncio.TimeoutError as e:
            error_result = {
                "error": f"Command timed out after {timeout} seconds",
                "command": command
            }

            # Log the timeout error
            log_info["timestamp_end"] = datetime.now(timezone.utc).isoformat()
            log_info["response"] = error_result
            log_info["success"] = False
            log_info["error"] = f"Timeout after {timeout}s"
            log_request(log_info)

            return [TextContent(
                type="text",
                text=json.dumps(error_result, indent=2)
            )]
        except FileNotFoundError as e:
            error_result = {
                "error": f"Command not found: {command.split()[0] if command.split() else command}",
                "command": command
            }

            # Log the command not found error
            log_info["timestamp_end"] = datetime.now(timezone.utc).isoformat()
            log_info["response"] = error_result
            log_info["success"] = False
            log_info["error"] = f"Command not found: {command.split()[0] if command.split() else command}"
            log_request(log_info)

            return [TextContent(
                type="text",
                text=json.dumps(error_result, indent=2)
            )]
        except Exception as e:
            error_result = {
                "error": f"Execution error: {str(e)}",
                "command": command
            }

            # Log the execution error
            log_info["timestamp_end"] = datetime.now(timezone.utc).isoformat()
            log_info["response"] = error_result
            log_info["success"] = False
            log_info["error"] = str(e)
            log_request(log_info)

            return [TextContent(
                type="text",
                text=json.dumps(error_result, indent=2)
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


# Create FastAPI app
app = FastAPI(title="Simple MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root(request: Request, api_key: str = Depends(verify_api_key)):
    """Health check endpoint."""
    # Log the HTTP request
    log_http_request(request, "/")

    return {
        "status": "ok",
        "server": "simple-utils-server",
        "message": "MCP Server is running",
        "authenticated": True
    }


@app.get("/.well-known/oauth-authorization-server")
async def oauth_discovery():
    """OAuth discovery endpoint - returns 404 to indicate no OAuth support."""
    raise HTTPException(status_code=404, detail="OAuth not supported")


@app.get("/health")
async def health(request: Request, api_key: str = Depends(verify_api_key)):
    """Health check endpoint."""
    # Log the HTTP request
    log_http_request(request, "/health")

    return {"status": "healthy"}


@app.post("/message")
async def message_endpoint(request: Request, api_key: str = Depends(verify_api_key)):
    """Alternative endpoint for sending JSON-RPC messages."""
    # Log the HTTP request
    log_http_request(request, "/message")

    return await sse_post_endpoint(request)


@app.post("/mcp/call")
async def mcp_call(request: Request, api_key: str = Depends(verify_api_key)):
    """Handle MCP tool calls via HTTP POST (legacy endpoint)."""
    # Log the HTTP request
    log_http_request(request, "/mcp/call")

    try:
        body = await request.json()
        tool_name = body.get("tool")
        arguments = body.get("arguments", {})

        # Call the tool
        result = await call_tool(tool_name, arguments, request)

        # Extract text content
        if result and len(result) > 0:
            response_text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            return JSONResponse(content={"result": response_text})
        else:
            return JSONResponse(content={"result": "No result"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/tools")
async def mcp_tools(request: Request, api_key: str = Depends(verify_api_key)):
    """List available MCP tools."""
    # Log the HTTP request
    log_http_request(request, "/mcp/tools")

    tools = await list_tools()
    return JSONResponse(content={
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            }
            for tool in tools
        ]
    })


# Store active SSE connections
active_connections: dict[str, asyncio.Queue] = {}


@app.get("/sse")
async def sse_endpoint(request: Request, api_key: str = Depends(verify_api_key)):
    """SSE endpoint for MCP protocol - receives responses."""
    # Log the HTTP request
    log_http_request(request, "/sse", {"connection_type": "sse_get"})

    connection_id = request.headers.get("X-Connection-ID", "default")

    # Create a queue for this connection
    if connection_id not in active_connections:
        active_connections[connection_id] = asyncio.Queue()

    queue = active_connections[connection_id]
    
    async def event_stream():
        try:
            # Don't send initial message - wait for client to send initialize request
            # Process messages from queue
            while True:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive as notification (no id field)
                    ping_message = {
                        "jsonrpc": "2.0",
                        "method": "ping",
                        "params": {}
                    }
                    yield f"data: {json.dumps(ping_message)}\n\n"
        except Exception as e:
            # Error notification (no id for notifications)
            error_message = {
                "jsonrpc": "2.0",
                "method": "error",
                "params": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            yield f"data: {json.dumps(error_message)}\n\n"
        finally:
            # Clean up connection
            if connection_id in active_connections:
                del active_connections[connection_id]
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/sse")
async def sse_post_endpoint(request: Request, api_key: str = Depends(verify_api_key)):
    """Handle JSON-RPC requests sent via POST to SSE endpoint."""
    try:
        body = await request.json()

        # Log the HTTP request with JSON-RPC details
        json_rpc_info = {
            "jsonrpc_version": body.get("jsonrpc"),
            "jsonrpc_method": body.get("method"),
            "jsonrpc_id": body.get("id"),
            "connection_type": "sse_post"
        }
        log_http_request(request, "/sse", json_rpc_info)

        connection_id = request.headers.get("X-Connection-ID", "default")
        request_id = body.get("id")
        
        # Validate JSON-RPC 2.0 format
        if not isinstance(body, dict):
            error_response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: body must be an object"
                }
            }
            if connection_id in active_connections:
                await active_connections[connection_id].put(error_response)
            return JSONResponse(status_code=400, content=error_response)
        
        if body.get("jsonrpc") != "2.0":
            error_response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: jsonrpc must be '2.0'"
                }
            }
            if connection_id in active_connections:
                await active_connections[connection_id].put(error_response)
            return JSONResponse(status_code=400, content=error_response)
        
        method = body.get("method")
        if not method:
            error_response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: method is required"
                }
            }
            if connection_id in active_connections:
                await active_connections[connection_id].put(error_response)
            return JSONResponse(status_code=400, content=error_response)
        
        params = body.get("params", {})
        
        # Check if this is a notification (no id field) - notifications don't require responses
        is_notification = request_id is None
        
        # Handle notifications silently
        if is_notification:
            if method == "notifications/initialized":
                # Client has finished initialization - acknowledge silently
                return JSONResponse(status_code=200, content={})
            elif method.startswith("notifications/"):
                # Handle other notifications silently
                return JSONResponse(status_code=200, content={})
            # For other notifications without id, just acknowledge
            return JSONResponse(status_code=200, content={})
        
        # Handle MCP protocol methods (requests with id)
        if method == "initialize":
            # Initialize the MCP server
            # MCP initialize response format
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "simple-utils-server",
                        "version": "1.0.0"
                    }
                }
            }
            
            # Send response via SSE if connection exists
            if connection_id in active_connections:
                await active_connections[connection_id].put(response)
            
            return JSONResponse(content=response)
        
        elif method == "tools/list":
            # List available tools
            tools = await list_tools()
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        }
                        for tool in tools
                    ]
                }
            }
            
            if connection_id in active_connections:
                await active_connections[connection_id].put(response)
            
            return JSONResponse(content=response)
        
        elif method == "tools/call":
            # Call a tool
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            result = await call_tool(tool_name, arguments, request)
            
            # Extract text content
            if result and len(result) > 0:
                response_text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            else:
                response_text = "No result"
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": response_text
                        }
                    ],
                    "isError": False
                }
            }
            
            if connection_id in active_connections:
                await active_connections[connection_id].put(response)
            
            return JSONResponse(content=response)
        
        else:
            # Unknown method - only return error if it's a request (has id)
            if not is_notification:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
                if connection_id in active_connections:
                    await active_connections[connection_id].put(response)
                
                return JSONResponse(status_code=404, content=response)
            else:
                # Unknown notification - acknowledge silently
                return JSONResponse(status_code=200, content={})
    
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": body.get("id") if 'body' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting HTTP server on port {port}")

    uvicorn.run(app, host="0.0.0.0", port=port)