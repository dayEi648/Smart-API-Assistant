# backend/app/models/mcp.py
from pydantic import BaseModel, Field
from typing import Optional


class SearchAPIDocsParams(BaseModel):
    """``search_api_docs`` 工具的参数模型。"""
    query: str = Field(..., min_length=1, description="检索关键词")
    top_k: int = Field(default=5, ge=1, le=20, description="返回结果数量上限")


class GenerateAPICodeParams(BaseModel):
    """``generate_api_code`` 工具的参数模型。"""
    path: str = Field(..., description="API 端点路径")
    method: str = Field(default="GET", description="HTTP 方法")
    lang: str = Field(default="python", description="目标编程语言")


class APISummaryItem(BaseModel):
    """API 概览列表中的单项模型。"""
    path: str
    method: str
    summary: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
