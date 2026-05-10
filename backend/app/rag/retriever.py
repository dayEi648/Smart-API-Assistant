from typing import List, Optional
from app.rag.vector_store import vector_store
from app.rag.embeddings import embedding_client

class APIRetriever:
    """
     API 文档检索器：将 Embedding 生成与向量查询串联为高层检索接口。

    负责把用户查询文本转为向量，再从 Chroma 召回最相关的 API 文档片段，
    并将距离分数转换为相似度分数返回。
    """

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        where: Optional[dict] = None,
    ) -> List[dict]:
        """基于自然语言查询检索相关 API 文档。

            Args:
                query: 用户输入的查询文本或自然语言问题。
                top_k: 返回最相关的结果数量，默认 5。
                where: 可选的元数据过滤条件（如 ``{"method": "GET"}``）。

            Returns:
                按相似度降序排列的结果列表，每条包含 ``content``、``metadata``、
                ``score``。注意：当前使用 ``1.0 - distance`` 作为相似度，
                在 cosine 空间下可能产生负值，生产环境建议根据实际距离分布调整归一化策略。
        """
        query_embedding = await embedding_client.embed_text(query)
        results = vector_store.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
        )
        formatted: List[dict] = []
        documents = results.get("documents", [[]])[0] or []
        metadatas = results.get("metadatas", [[]])[0] or []
        distances = results.get("distances", [[]])[0] or []
        ids = results.get("ids", [[]])[0] or []

        for idx, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
            similarity = 1.0 - float(dist)
            formatted.append({
                "id": ids[idx] if idx < len(ids) else "",
                "content": doc,
                "metadata": meta or {},
                "score": round(similarity, 4),
            })
        formatted.sort(key=lambda x: x["score"], reverse=True)
        return formatted
    
    async def search_by_endpoint(
        self,
        path: str,
        method: Optional[str] = None,
    ) -> List[dict]:
        """按端点路径（及可选方法）精确检索。

        Args:
            path: API 路径，如 ``/api/auth/login``。
            method: HTTP 方法过滤，如 ``GET``、``POST``。

        Returns:
            匹配端点的前 3 条检索结果。
        """
        where_filter = None
        if method:
            where_filter = {"method": method.upper()}
        return await self.retrieve(query=path, top_k=3, where=where_filter)


retriever = APIRetriever()