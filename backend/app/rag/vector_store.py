import chromadb
from chromadb.api.models.Collection import Collection
from typing import List, Optional
from app.config import settings 

class VectorStore:
    """
    Chroma 向量存储封装。

    提供文档增删改查、相似度检索等高层接口，内部自动管理 HTTP 连接与 Collection 生命周期。
    启动时会通过重试机制等待 Chroma 服务就绪（当前使用同步 ``time.sleep``，会阻塞事件循环，
    生产环境建议替换为 ``asyncio.sleep`` 配合异步初始化）。
    """
    def __init__(self) -> None:
        """初始化客户端引用（延迟连接）。"""
        self._client = None
        self._collection = None
    
    def _ensure_connected(self):
        """建立与 Chroma 服务的连接，最多重试 10 次。"""
        if self._client is not None:
            return
        import time 
        last_err = None
        for _ in range(10):
            try:
                self._client = chromadb.HttpClient(
                    host=settings.CHROMA_HOST,
                    port=settings.CHROMA_PORT,)
                self._collection: Collection = self._client.get_or_create_collection(
                    name=settings.CHROMA_CONNECTION,
                    metadata={"hnsw:space": "cosine"})
                return
            except Exception as e:
                last_err = e
                time.sleep(1)
        raise last_err

    @property
    def collection(self) -> Collection:
        """获取已连接的 Chroma Collection（首次访问时触发连接）。"""
        self._ensure_connected()
        return self._collection
    
    def add_documents(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[dict]] = None,
    ) -> None:
        """批量写入文档及其向量到 Chroma。

        Args:
            ids: 文档唯一标识列表。
            documents: 原始文本列表。
            embeddings: 对应的 Embedding 向量列表。
            metadatas: 可选的元数据字典列表。
        """
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[dict] = None,
    ) -> dict:
        """执行向量相似度检索。

        Args:
            query_embeddings: 查询向量列表（通常仅含一条）。
            n_results: 返回最相似的结果数量，默认 5。
            where: 可选的元数据过滤条件。

        Returns:
            Chroma 原始查询结果字典，包含 ``ids``、``documents``、
            ``metadatas``、``distances`` 等字段。
        """
        return self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where,
        )

    def get_all(self, limit: int = 100, offset: int = 0) -> dict:
        """分页获取 Collection 中的全部数据。"""
        return self.collection.get(limit=limit, offset=offset)

    def count(self) -> int:
        """返回当前 Collection 中的文档总数。"""
        return self.collection.count()

    def delete_by_ids(self, ids: List[str]) -> None:
        """按 ID 列表删除指定文档。

        Args:
            ids: 待删除的文档 ID 列表。
        """
        if ids:
            self.collection.delete(ids=ids)

    def delete_all(self) -> None:
        """清空当前 Collection 中的所有文档。"""
        all_data = self.collection.get()
        if all_data:
            ids = all_data.get("ids", []) or []
            if ids:
                self.collection.delete(ids=ids)

vector_store = VectorStore()
