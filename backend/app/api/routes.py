import uuid
import asyncio
import json
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Request
from fastapi.responses import JSONResponse, StreamingResponse
from app.models.document import TaskDetail, TaskStatus
from app.models.chat import ChatRequest, ChatHistoryResponse
from app.parser.tasks import create_task, run_parse_task, get_task_status
from app.agents.supervisor import supervisor_agent
from app.agents.state import AgentState
from app.api.streaming import create_sse_response
from app.memory.memory_manager import memory_manager
from app.rag.vector_store import vector_store

router = APIRouter(prefix="/api/v1")
"""REST API 主路由，前缀 ``/api/v1``。"""

# 同一 session 的并发请求锁
session_locks: dict[str, asyncio.Lock] = {}


def _ok(data=None, message="success"):
    """构造统一成功响应。

    Args:
        data: 响应负载数据，默认 ``None``。
        message: 提示文本，默认 ``"success"``。

    Returns:
        封装后的 ``JSONResponse``，code 为 0。
    """
    return JSONResponse(content={"code": 0, "data": data, "message": message})


def _err(code: int, message: str, status_code: int = 400):
    """构造统一失败响应。

    Args:
        code: 业务错误码。
        message: 错误描述。
        status_code: HTTP 状态码，默认 400。

    Returns:
        封装后的 ``JSONResponse``，data 为 ``None``。
    """
    return JSONResponse(status_code=status_code, content={"code": code, "data": None, "message": message})


@router.post("/documents/upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(None)):
    """上传 API 文档并触发异步解析任务。

    Args:
        background_tasks: FastAPI 后台任务注入。
        file: 上传的文件对象（.json / .yaml / .yml）。

    Returns:
        包含 ``task_id``、``status``、``doc_id`` 的成功响应；
        校验失败时返回对应错误码。
    """
    if not file or not file.filename:
        return _err(40001, "未上传文件")
    allowed = (".json", ".yaml", ".yml")
    if not file.filename.lower().endswith(allowed):
        return _err(40001, "仅支持 .json / .yaml / .yml 文件")
    content = await file.read()
    if len(content) == 0:
        return _err(40001, "文件内容为空")
    if len(content) > 10 * 1024 * 1024:
        return _err(40002, "文件大小超过 10MB 限制", 413)

    doc_id = str(uuid.uuid4())
    task_id = create_task()
    background_tasks.add_task(run_parse_task, task_id, content, file.filename, doc_id)
    return _ok(data={"task_id": task_id, "status": TaskStatus.PENDING.value, "doc_id": doc_id})


@router.get("/documents/tasks/{task_id}")
async def get_task(task_id: str):
    """查询文档解析任务的当前状态与结果。

    Args:
        task_id: 上传接口返回的任务 ID。

    Returns:
        任务详情响应；任务不存在时返回 40401。
    """
    task = get_task_status(task_id)
    if not task:
        return _err(40401, "任务不存在", 404)
    return _ok(data=TaskDetail(**task).model_dump(mode='json'))


@router.post("/chat")
async def chat(request: ChatRequest, req: Request):
    """统一 SSE 对话入口：根据用户意图自动路由到 QA Agent 或 CodeGen Agent。

    Args:
        request: 包含 ``session_id`` 与 ``message`` 的请求体。
        req: FastAPI 原始请求对象，用于校验 ``Accept`` 头。

    Returns:
        ``StreamingResponse``（SSE 流式）；校验失败时返回 JSON 错误响应。
    """
    accept = req.headers.get("accept", "")
    if "text/event-stream" not in accept:
        return _err(40004, "Accept 头必须为 text/event-stream", 406)

    lock = session_locks.setdefault(request.session_id, asyncio.Lock())

    async with lock:
        await memory_manager.append_user_message(request.session_id, request.message)
        state: AgentState = {"session_id": request.session_id, "user_message": request.message}

        try:
            state = await supervisor_agent.run(state)
        except Exception as e:
            error_msg = str(e)
            async def _error_stream():
                error_payload = json.dumps({"code": 50001, "message": f"Agent 执行失败: {error_msg}"})
                yield f"event: error\ndata: {error_payload}\n\n"
                done_payload = json.dumps({"finish_reason": "error"})
                yield f"event: done\ndata: {done_payload}\n\n"
            return StreamingResponse(_error_stream(), media_type="text/event-stream")

        generator = state.get("generator")
        if not generator:
            async def _error_stream():
                error_payload = json.dumps({"code": 50001, "message": "生成器初始化失败"})
                yield f"event: error\ndata: {error_payload}\n\n"
                done_payload = json.dumps({"finish_reason": "error"})
                yield f"event: done\ndata: {done_payload}\n\n"
            return StreamingResponse(_error_stream(), media_type="text/event-stream")

        return create_sse_response(generator)


@router.get("/chat/sessions/{session_id}/history")
async def get_chat_history(session_id: str, limit: int = 20):
    """查询指定会话的对话历史。

    Args:
        session_id: 会话唯一标识。
        limit: 返回最近 N 条消息，默认 20。

    Returns:
        包含 ``session_id`` 与 ``messages`` 列表的响应。
    """
    messages = await memory_manager.get_session_history(session_id, limit=limit)
    formatted = []
    for m in messages:
        item = {
            "role": m["role"],
            "content": m["content"],
            "timestamp": m.get("timestamp"),
        }
        if m.get("type") is not None:
            item["type"] = m["type"]
        formatted.append(item)
    return _ok(data=ChatHistoryResponse(session_id=session_id, messages=formatted).model_dump(mode='json'))


@router.delete("/chat/sessions/{session_id}")
async def clear_chat_session(session_id: str):
    """清除指定会话的全部历史（Redis + PG）并释放并发锁。

    Args:
        session_id: 会话唯一标识。

    Returns:
        标准成功响应。
    """
    await memory_manager.clear_session(session_id)
    session_locks.pop(session_id, None)
    return _ok()


@router.get("/knowledge/apis")
async def get_api_overview(limit: int = 50, offset: int = 0):
    """获取当前知识库中已索引的所有 API 端点概览。

    Args:
        limit: 分页大小，默认 50。
        offset: 分页偏移，默认 0。

    Returns:
        包含 ``total`` 总数与 ``items`` 端点列表的响应。
    """
    results = vector_store.get_all(limit=limit, offset=offset)
    items = []
    ids = results.get("ids") or []
    metadatas = results.get("metadatas") or []
    for idx, meta in enumerate(metadatas):
        if meta:
            tags_raw = meta.get("tags", "")
            if isinstance(tags_raw, list):
                tags = tags_raw
            else:
                tags = tags_raw.split(",") if tags_raw else []
            items.append({
                "id": ids[idx] if idx < len(ids) else "",
                "path": meta.get("path", ""),
                "method": meta.get("method", ""),
                "summary": meta.get("summary", ""),
                "tags": tags,
            })
    return _ok(data={"total": vector_store.count(), "items": items})


@router.get("/knowledge/search")
async def search_api_docs(q: str = "", top_k: int = 5):
    """基于关键词对向量库执行相似度检索。

    Args:
        q: 检索关键词或自然语言描述（必填）。
        top_k: 返回最相关的 N 条结果，默认 5。

    Returns:
        包含原始查询与检索结果列表的响应；``q`` 为空时返回 40005。
    """
    if not q or not q.strip():
        return _err(40005, "检索关键词不能为空")
    from app.rag.retriever import retriever
    docs = await retriever.retrieve(q, top_k=top_k)
    results = []
    for doc in docs:
        meta = doc.get("metadata", {})
        results.append({
            "id": doc.get("id", ""),
            "path": meta.get("path", ""),
            "method": meta.get("method", ""),
            "summary": meta.get("summary", ""),
            "score": doc.get("score", 0),
            "content": doc.get("content", ""),
        })
    return _ok(data={"query": q, "results": results})


@router.delete("/knowledge/apis/{api_id}")
async def delete_api_endpoint(api_id: str):
    """删除知识库中指定的 API 端点。

    Args:
        api_id: 端点在向量库中的唯一标识（chunk_id）。

    Returns:
        删除成功响应；端点不存在时返回 40402。
    """
    existing = vector_store.collection.get(ids=[api_id])
    if not existing or not existing.get("ids"):
        return _err(40402, "API 端点不存在", 404)
    vector_store.delete_by_ids([api_id])
    return _ok()
