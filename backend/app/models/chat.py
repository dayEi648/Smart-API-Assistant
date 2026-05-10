from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    """
    SSE 流式消息类型枚举
    """
    TEXT = "text"
    CODE = "code"

class ChatRequest(BaseModel):
    """
    流式对话请求模型
    """
    session_id: str = Field(...,min_length = 1 ,description="会话唯一标识")
    message: str = Field(...,min_length = 1 ,description="用户输入的自然语言内容")

class ChatStreamMessage(BaseModel):
    """
    SSE 流式流式消息片段模型
    """
    type: MessageType
    content: str = Field(..., description="内容片段")
    lang: Optional[str] = Field(default=None ,description="代码语言标识")

class ChatDoneEvent(BaseModel):
    """
    SSE 流式结束事件模型
    """
    finish_reason: str = Field(default="stop",description="结束原因")


class ChatHistoryMessage(BaseModel):
    """单条会话历史消息模型。

    支持 ``timestamp`` 字符串自动反序列化（兼容 Redis 存储的 ISO 格式）。
    """
    role: Literal["user", "assistant"]
    content: str
    type: Optional[MessageType] = Field(default=None)
    timestamp: Optional[datetime] = Field(default=None, description="消息产生时间（UTC），部分来源可能无此字段")

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v


class ChatHistoryResponse(BaseModel):
    """会话历史查询响应模型。"""
    session_id: str
    messages: list[ChatHistoryMessage]