# backend/app/mcp/server.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from app.mcp.session import mcp_session_manager
from app.mcp.tools import MCP_TOOL_MAP
import json
import asyncio

mcp_router = APIRouter(prefix="/mcp/v1")
"""MCP 独立子路由，前缀 ``/mcp/v1``。"""

message_queues: dict[str, asyncio.Queue] = {}
"""全局消息队列映射：``session_id → asyncio.Queue``，用于 SSE 与 POST handler 通信。"""


@mcp_router.get("/sse")
async def mcp_sse_endpoint(request: Request):
    """MCP SSE 连接端点：建立长连接并返回 POST endpoint URL。

    Args:
        request: FastAPI 请求对象，用于校验 ``Accept`` 头。

    Returns:
        ``StreamingResponse``（SSE 流式），首条事件为 ``endpoint``。

    Raises:
        HTTPException: 当请求头未声明 ``text/event-stream`` 时返回 406。
    """
    accept = request.headers.get("accept", "")
    if "text/event-stream" not in accept:
        raise HTTPException(status_code=406, detail="Accept 头必须为 text/event-stream")

    session_id = mcp_session_manager.create_session()
    post_url = mcp_session_manager.get_post_endpoint(session_id)
    queue = asyncio.Queue()
    message_queues[session_id] = queue

    async def event_generator():
        """内部 SSE 事件生成器：发送 endpoint 事件后持续监听队列。"""
        yield f"event: endpoint\ndata: {post_url}\n\n"
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"event: message\ndata: {json.dumps(msg, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            mcp_session_manager.remove_session(session_id)
            message_queues.pop(session_id, None)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@mcp_router.post("/messages")
async def mcp_messages_endpoint(request: Request):
    """MCP 消息接收端点：处理 JSON-RPC 工具调用请求。

    Args:
        request: FastAPI 请求对象，需携带 ``session_id`` Query 参数。

    Returns:
        若 SSE 连接仍存在则通过队列异步返回结果；否则直接返回 JSON-RPC 响应。
    """
    body = await request.json()
    jsonrpc = body.get("jsonrpc")
    req_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})

    session_id = request.query_params.get("session_id")
    queue = message_queues.get(session_id) if session_id else None

    if jsonrpc != "2.0":
        result = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32600, "message": "Invalid Request"}}
    elif method != "tools/call":
        result = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}
    else:
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})
        tool_func = MCP_TOOL_MAP.get(tool_name)

        if not tool_func:
            result = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"}}
        else:
            try:
                tool_result = await tool_func(tool_params, session_id=session_id or "")
                result = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(tool_result, ensure_ascii=False)}]},
                }
            except Exception as e:
                result = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(e)}}

    if queue:
        await queue.put(result)
        return {"status": "accepted"}
    else:
        return result
