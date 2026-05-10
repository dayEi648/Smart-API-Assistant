import json
import redis.asyncio as redis
from typing import List, Optional
from datetime import datetime, timezone
from app.config import settings

class RedisClient:
    """Redis 中期记忆客户端。

    负责按 ``session_id`` 存取会话消息列表，支持追加、读取、过期与清理。
    所有消息以 JSON 字符串形式存储在 Redis List 中，默认 TTL 为 30 分钟。
    """
    KEY_PREFIX: str = "sma:session"


    def __init__(self) -> None:
        """初始化异步 Redis 连接。"""
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
    

    def _key(self, session_id: str) -> str:
        """构造 Redis Key。

        Args:
            session_id: 会话唯一标识。

        Returns:
            带统一前缀的 Redis Key。
        """
        return f"{self.KEY_PREFIX}:{session_id}"


    async def add_message(self, session_id: str, role: str, content: str, msg_type: Optional[str] = None) -> None:
        """向指定会话追加一条消息，并刷新 TTL。

        Args:
            session_id: 会话唯一标识。
            role: 消息角色，如 ``user`` 或 ``assistant``。
            content: 消息正文。
            msg_type: 消息类型，如 ``text`` 或 ``code``，默认为 ``None``。
        """
        message = {
            "role": role,
            "content": content,
            "type": msg_type,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        key = self._key(session_id)
        await self.client.rpush(key, json.dumps(message, ensure_ascii=False))
        await self.client.expire(key, settings.REDIS_SESSION_TTL)
    
    async def get_history(self, session_id: str, limit: int = 20) -> List[dict]:
        """获取指定会话的最近 N 条消息。

        Args:
            session_id: 会话唯一标识。
            limit: 返回消息数量上限，默认 20。

        Returns:
            按时间正序排列的消息字典列表。
        """
        key = self._key(session_id)
        raw_messages = await self.client.lrange(key, -limit, -1)
        history = []
        for raw in raw_messages:
            try:
                history.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
        return history
    
    async def rpush_raw(self, session_id: str, raw_json: str) -> None:
        """直接 RPUSH 已序列化的 JSON（用于从 PG 回填 Redis）。

        Args:
            session_id: 会话唯一标识。
            raw_json: 已序列化的 JSON 字符串。
        """
        await self.client.rpush(self._key(session_id), raw_json)

    async def expire(self, session_id: str, ttl: int) -> None:
        """显式设置会话 Key 的过期时间。

        Args:
            session_id: 会话唯一标识。
            ttl: 过期时间（秒）。
        """
        await self.client.expire(self._key(session_id), ttl)

    async def clear_session(self, session_id: str) -> None:
        """删除指定会话的全部缓存数据。

        Args:
            session_id: 会话唯一标识。
        """
        await self.client.delete(self._key(session_id))
    
    async def close(self) -> None:
        """关闭 Redis 连接，释放资源。"""
        await self.client.close()

redis_client = RedisClient()
