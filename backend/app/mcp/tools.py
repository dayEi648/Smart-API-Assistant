# backend/app/mcp/tools.py
from app.rag.retriever import retriever
from app.rag.vector_store import vector_store
from app.agents.codegen_agent import codegen_agent
from app.models.mcp import SearchAPIDocsParams, GenerateAPICodeParams


class MCPTools:
    """MCP 暴露的标准化工具集。

    内部直接复用已有的 RAG 检索与 CodeGen 能力，不经过 LangGraph Supervisor。
    """

    @staticmethod
    async def search_api_docs(params: dict, session_id: str = "") -> dict:
        """基于关键词检索 API 文档端点。

        Args:
            params: 包含 ``query`` 与可选 ``top_k`` 的字典。
            session_id: 当前 MCP 会话 ID（预留，当前未使用）。

        Returns:
            工具执行结果字典，包含检索到的文档列表。
        """
        validated = SearchAPIDocsParams(**params)
        docs = await retriever.retrieve(validated.query, top_k=validated.top_k)
        return {"tool": "search_api_docs", "results": docs}

    @staticmethod
    async def generate_api_code(params: dict, session_id: str = "") -> dict:
        """为指定端点生成调用代码。

        Args:
            params: 包含 ``path``、``method``、``lang`` 的字典。
            session_id: 当前 MCP 会话 ID。

        Returns:
            工具执行结果字典，包含生成的代码字符串。
        """
        validated = GenerateAPICodeParams(**params)
        code_parts = []
        mcp_session = session_id if session_id else "mcp_default"
        async for text, _ in codegen_agent.stream_code(mcp_session, f"生成 {validated.path} 的 {validated.lang} 调用代码"):
            code_parts.append(text)
        return {"tool": "generate_api_code", "path": validated.path, "lang": validated.lang, "code": "".join(code_parts)}

    @staticmethod
    async def get_api_summary(params: dict, session_id: str = "") -> dict:
        """获取当前知识库中所有 API 的概览列表。

        Args:
            params: 空字典（工具无必填参数）。
            session_id: 当前 MCP 会话 ID（预留，当前未使用）。

        Returns:
            工具执行结果字典，包含 ``total`` 与 ``items`` 列表。
        """
        results = vector_store.get_all(limit=100, offset=0)
        items = []
        for meta in (results.get("metadatas") or []):
            if meta:
                tags_raw = meta.get("tags", "")
                if isinstance(tags_raw, list):
                    tags = tags_raw
                else:
                    tags = tags_raw.split(",") if tags_raw else []
                items.append({"path": meta.get("path", ""), "method": meta.get("method", ""), "summary": meta.get("summary", ""), "tags": tags})
        return {"tool": "get_api_summary", "total": vector_store.count(), "items": items}


MCP_TOOL_MAP: dict[str, callable] = {
    "search_api_docs": MCPTools.search_api_docs,
    "generate_api_code": MCPTools.generate_api_code,
    "get_api_summary": MCPTools.get_api_summary,
}
