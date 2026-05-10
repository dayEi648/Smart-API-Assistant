from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    """
    文档解析任务的状态枚举
    """
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentUploadResponse(BaseModel):
    """
    文档上传接口的响应模型
    """
    task_id: str = Field(..., description="异步解析任务唯一标识")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    doc_id: str = Field(..., description="文档唯一标识")

class ParserResult(BaseModel):
    """文档解析完成后的结果统计模型。"""
    total_endpoints: int = Field(..., description="API 端点总数")
    total_chunks: int = Field(..., description="向量 Chunk 总数")
    doc_id: str = Field(..., description="文档唯一标识")

class TaskDetail(BaseModel):
    """
    任务状态查询的详细响应模型。

    支持 ``created_at`` / ``updated_at`` 的字符串自动反序列化（兼容 ISO 格式）。
    """
    task_id: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    result: Optional[ParserResult] = Field(default=None)
    error: Optional[str] = Field(default=None)

    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v