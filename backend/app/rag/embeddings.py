import httpx
from typing import List, Optional
from app.config import settings

class DashScopeEmbedding:
    """阿里云百炼 Embedding 服务客户端。

    基于 httpx 异步 HTTP 客户端，封装了 text-embedding-v4 模型的单条/批量嵌入能力。
    通过 ``Settings`` 自动读取环境变量中的 API Key 与模型配置。

    Attributes:
        BASE_URL: 百炼 Embedding API 的基础 URL，从配置中读取。
        MODEL: 使用的 Embedding 模型名称，从配置中读取。
    """
    BASE_URL: str = settings.DASHSCOPE_BASE_URL
    MODEL: str = settings.EMBEDDING_MODEL

    def __init__(self) -> None:
        """
        初始化客户端，延迟创建 HTTP 连接
        """
        self.api_key = settings.DASHSCOPE_API_KEY
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """获取或创建异步 HTTP 客户端。

        Returns:
            已配置好 base_url、鉴权头和超时时间的 ``httpx.AsyncClient`` 实例。

        Raises:
            ValueError: 当环境变量中未配置 ``DASHSCOPE_API_KEY`` 时抛出。
        """
        if self._client is None:
            if not self.api_key:
                raise ValueError("DASHSCOPE_API_KEY is not configured")
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(30.0),
            )
        return self._client
    
    async def embed_text(self, text: str) -> List[float]:
        """
        对单条文本生成 Embedding 向量。

        Args:
            text: 待嵌入的原始文本。

        Returns:
            该文本对应的浮点向量列表。
        """
        payload = {
                "model": self.MODEL,
                "input": {"texts": [text]},
            }
        response = await self.client.post("", json=payload)
        response.raise_for_status()
        data = response.json()
        return data["output"]["embeddings"][0]["embedding"]
    
    async def embed_batch(self, texts: List[str], batch_size: int = 25) -> List[List[float]]:
        """
        批量生成 Embedding，自动分批避免超出 API 限制。

        Args:
            texts: 待嵌入的文本列表。
            batch_size: 每批发送的文本数量，默认 25（阿里云百炼 text-embedding-v4 的限制）。

        Returns:
            与输入顺序一致的向量列表。
        """
        if not texts:
            return []
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            payload = {
                "model": self.MODEL,
                "input": {"texts": batch},
            }
            response = await self.client.post("", json=payload)
            response.raise_for_status()
            data = response.json()
            embeddings = data["output"]["embeddings"]
            results.extend([item["embedding"] for item in embeddings])
        return results
    
    async def close(self) -> None:
        """关闭内部 HTTP 客户端，释放连接资源。"""
        if self._client:
            await self._client.aclose()

embedding_client = DashScopeEmbedding()