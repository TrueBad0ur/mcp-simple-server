#!/usr/bin/env python3
"""
HTTP/SSE wrapper for MCP server
Allows remote connections via HTTP Server-Sent Events
"""

import asyncio
import json
import shlex
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from mcp.server import Server
from mcp.types import Tool, TextContent
from datetime import datetime, timezone
import math
from typing import Any, Sequence


# Create the MCP server instance
server = Server("simple-utils-server")


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
            name="format_number",
            description="Format a number with various options",
            inputSchema={
                "type": "object",
                "properties": {
                    "number": {
                        "type": "number",
                        "description": "Number to format"
                    },
                    "decimals": {
                        "type": "integer",
                        "description": "Number of decimal places",
                        "default": 2
                    },
                    "scientific": {
                        "type": "boolean",
                        "description": "Use scientific notation",
                        "default": False
                    }
                },
                "required": ["number"],
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
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
    """Handle tool calls."""
    
    if name == "get_current_time":
        now = datetime.now(timezone.utc)
        local_now = datetime.now()
        
        result = {
            "utc_time": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "local_time": local_now.strftime("%Y-%m-%d %H:%M:%S"),
            "unix_timestamp": int(now.timestamp()),
            "iso_format": now.isoformat(),
        }
        
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
            return [TextContent(
                type="text",
                text=json.dumps({
                    "expression": expression,
                    "result": result,
                    "type": type(result).__name__
                }, indent=2)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Calculation error: {str(e)}"}, indent=2)
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
        except Exception as e:
            result = {
                "timezone": timezone_name,
                "error": f"Invalid timezone: {str(e)}",
                "note": "Try 'UTC', 'America/New_York', 'Europe/London', etc."
            }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "format_number":
        number = arguments.get("number")
        decimals = arguments.get("decimals", 2)
        scientific = arguments.get("scientific", False)
        
        if scientific:
            formatted = f"{number:.{decimals}e}"
        else:
            formatted = f"{number:.{decimals}f}"
        
        result = {
            "original": number,
            "formatted": formatted,
            "decimals": decimals,
            "scientific_notation": scientific,
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
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
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        except asyncio.TimeoutError:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Command timed out after {timeout} seconds",
                    "command": command
                }, indent=2)
            )]
        except FileNotFoundError:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Command not found: {command.split()[0] if command.split() else command}",
                    "command": command
                }, indent=2)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Execution error: {str(e)}",
                    "command": command
                }, indent=2)
            )]
    
    else:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
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
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "server": "simple-utils-server",
        "message": "MCP Server is running"
    }


@app.get("/.well-known/oauth-authorization-server")
async def oauth_discovery():
    """OAuth discovery endpoint - returns 404 to indicate no OAuth support."""
    raise HTTPException(status_code=404, detail="OAuth not supported")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/message")
async def message_endpoint(request: Request):
    """Alternative endpoint for sending JSON-RPC messages."""
    return await sse_post_endpoint(request)


@app.post("/mcp/call")
async def mcp_call(request: Request):
    """Handle MCP tool calls via HTTP POST (legacy endpoint)."""
    try:
        body = await request.json()
        tool_name = body.get("tool")
        arguments = body.get("arguments", {})
        
        # Call the tool
        result = await call_tool(tool_name, arguments)
        
        # Extract text content
        if result and len(result) > 0:
            response_text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            return JSONResponse(content={"result": response_text})
        else:
            return JSONResponse(content={"result": "No result"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/tools")
async def mcp_tools():
    """List available MCP tools."""
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
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP protocol - receives responses."""
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
async def sse_post_endpoint(request: Request):
    """Handle JSON-RPC requests sent via POST to SSE endpoint."""
    try:
        body = await request.json()
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
            
            result = await call_tool(tool_name, arguments)
            
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
