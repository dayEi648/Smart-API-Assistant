import json
from typing import AsyncGenerator, Optional, Tuple
from fastapi.responses import StreamingResponse
from app.models.chat import ChatStreamMessage, ChatDoneEvent

async def _sse_wrapper(generator):
    """
    将 Agent 异步生成器包装为 SSE 事件流。

    支持 dict、tuple 与纯字符串三种 yield 格式，自动映射到
    ``ChatStreamMessage`` 或 ``ChatDoneEvent``。

    Args:
        generator: Agent 产生的异步生成器，yield 单个片段。

    Yields:
        符合 SSE 规范的字符串行（含 ``event:`` 与 ``data:``）。
    """
    try:
        async for item in generator:
            if isinstance(item, dict):
                msg_type = item.get("type", "text")
                text = item.get("content", "")
                lang = item.get("lang")
            elif isinstance(item, tuple):
                text, lang = item
                msg_type = "code" if lang else "text"
            else:
                text, lang = item, None
                msg_type = "text"
            message = ChatStreamMessage(type=msg_type, content=text, lang=lang)
            yield f"event: message\ndata: {message.model_dump_json(exclude_none=True)}\n\n"
        done = ChatDoneEvent()
        yield f"event: done\ndata: {done.model_dump_json()}\n\n"
    except Exception as e:
        error_payload = json.dumps({"code": 50001, "message": str(e)})
        yield f"event: error\ndata: {error_payload}\n\n"
        done = ChatDoneEvent()
        yield f"event: done\ndata: {done.model_dump_json()}\n\n"


def create_sse_response(generator):
    """
    基于生成器创建 FastAPI ``StreamingResponse``（SSE 格式）。

    Args:
        generator: 异步生成器，yield 内容片段。

    Returns:
        已设置 ``text/event-stream`` MediaType 的 ``StreamingResponse`` 对象。
    """
    return StreamingResponse(
        _sse_wrapper(generator),
        media_type="text/event-stream",
    )