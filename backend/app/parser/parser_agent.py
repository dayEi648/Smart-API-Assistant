# backend/app/parser/parser_agent.py
from typing import Dict, Any
from app.parser.chunker import OpenAPIChunker
from app.rag.embeddings import embedding_client
from app.rag.vector_store import vector_store


class ParserAgent:
    """文档解析 Agent：将 OpenAPI 文档分片、Embedding 并向量化入库。

    这是独立链路，不经过 LangGraph Supervisor，由 FastAPI BackgroundTasks 直接触发。
    """

    def __init__(self) -> None:
        """初始化分片器。"""
        self.chunker = OpenAPIChunker()

    async def parse_and_index(self, content: bytes, filename: str, doc_id: str) -> Dict[str, Any]:
        """解析文档并写入向量库。

        Args:
            content: 文档原始字节内容。
            filename: 原始文件名。
            doc_id: 文档唯一标识。

        Returns:
            解析统计字典，包含 ``total_endpoints``、``total_chunks``、``doc_id``。
        """
        chunks = self.chunker.parse(content, filename, doc_id)
        if not chunks:
            return {"total_endpoints": 0, "total_chunks": 0, "doc_id": doc_id}

        texts = [chunk["text"] for chunk in chunks]
        embeddings = await embedding_client.embed_batch(texts)

        ids = [chunk["id"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        vector_store.add_documents(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)

        return {"total_endpoints": len(chunks), "total_chunks": len(chunks), "doc_id": doc_id}


parser_agent = ParserAgent()