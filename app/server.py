#!/usr/bin/env python3
"""
HTTP/SSE wrapper for MCP server
Allows remote connections via HTTP Server-Sent Events
"""

import asyncio
import json
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

try:
    # Try relative imports (when run as module)
    from .config import HOST, PORT, CORS_ORIGINS
    from .auth import verify_api_key
    from .logging_utils import log_http_request
    from .tools import server, list_tools, call_tool
except ImportError:
    # Fall back to absolute imports (when run directly)
    from config import HOST, PORT, CORS_ORIGINS
    from auth import verify_api_key
    from logging_utils import log_http_request
    from tools import server, list_tools, call_tool


# Create FastAPI app
app = FastAPI(title="Simple MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root(request: Request, api_key: str = Depends(verify_api_key)):
    """Root endpoint."""
    log_http_request(request, "/")
    return {"message": "Simple MCP Server", "status": "running"}


@app.get("/health")
async def health(request: Request, api_key: str = Depends(verify_api_key)):
    """Health check endpoint."""
    log_http_request(request, "/health")
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/mcp/tools")
async def mcp_tools(request: Request, api_key: str = Depends(verify_api_key)):
    """List available MCP tools."""
    log_http_request(request, "/mcp/tools")
    tools = await list_tools()
    return {"tools": [{"name": tool.name, "description": tool.description, "inputSchema": tool.inputSchema} for tool in tools]}


@app.post("/mcp/call")
async def mcp_call(request: Request, api_key: str = Depends(verify_api_key)):
    """Handle MCP JSON-RPC calls."""
    try:
        body = await request.json()

        # Validate JSON-RPC 2.0 format
        if body.get("jsonrpc") != "2.0":
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32600,
                        "message": "Invalid JSON-RPC version"
                    }
                }
            )

        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        log_http_request(request, "/mcp/call", {"method": method, "params": params})

        # Handle MCP protocol methods
        if method == "initialize":
            # MCP initialization
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": True
                        }
                    },
                    "serverInfo": {
                        "name": "simple-utils-server",
                        "version": "1.0.0"
                    }
                }
            }

        elif method == "tools/list":
            # List available tools
            tools = await list_tools()
            return {
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

        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})

            if not name:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": "Tool name is required"
                    }
                }

            try:
                result = await call_tool(name, arguments, request)
                # Extract content from TextContent objects
                content = []
                for item in result:
                    if hasattr(item, 'type') and hasattr(item, 'text'):
                        content.append({
                            "type": item.type,
                            "text": item.text
                        })
                    else:
                        content.append(str(item))

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": content
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"Tool execution error: {str(e)}"
                    }
                }

        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

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
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
        )


@app.get("/sse")
async def sse_endpoint(request: Request, api_key: str = Depends(verify_api_key)):
    """Server-Sent Events endpoint for MCP."""
    log_http_request(request, "/sse")

    async def event_generator():
        """Generate SSE events."""
        try:
            # Keep connection alive with occasional comments
            while True:
                await asyncio.sleep(30)  # Send keep-alive every 30 seconds
                yield ": keepalive\n\n"

        except asyncio.CancelledError:
            # Connection closed by client
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        }
    )


@app.post("/sse")
async def sse_post_endpoint(request: Request, api_key: str = Depends(verify_api_key)):
    """Handle POST requests to SSE endpoint for MCP calls."""
    try:
        body = await request.json()

        # Validate JSON-RPC 2.0 format
        if body.get("jsonrpc") != "2.0":
            response = {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "error": {
                    "code": -32600,
                    "message": "Invalid JSON-RPC version"
                }
            }

            async def error_generator():
                yield f"data: {json.dumps(response)}\n\n"

            return StreamingResponse(
                error_generator(),
                media_type="text/event-stream"
            )

        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        log_http_request(request, "/sse", {"method": method, "params": params})

        # Handle MCP protocol methods
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": True
                        }
                    },
                    "serverInfo": {
                        "name": "simple-utils-server",
                        "version": "1.0.0"
                    }
                }
            }

        elif method == "tools/list":
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

        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})

            if not name:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": "Tool name is required"
                    }
                }
            else:
                try:
                    result = await call_tool(name, arguments, request)
                    # Extract content from TextContent objects
                    content = []
                    for item in result:
                        if hasattr(item, 'type') and hasattr(item, 'text'):
                            content.append({
                                "type": item.type,
                                "text": item.text
                            })
                        else:
                            content.append(str(item))

                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": content
                        }
                    }
                except Exception as e:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Tool execution error: {str(e)}"
                        }
                    }
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

        async def response_generator():
            yield f"data: {json.dumps(response)}\n\n"

        return StreamingResponse(
            response_generator(),
            media_type="text/event-stream"
        )

    except json.JSONDecodeError:
        response = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": "Parse error"
            }
        }

        async def error_generator():
            yield f"data: {json.dumps(response)}\n\n"

        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream"
        )
    except Exception as e:
        response = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

        async def error_generator():
            yield f"data: {json.dumps(response)}\n\n"

        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream"
        )


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=HOST,
        port=PORT,
        reload=True
    )