import json
from typing import List
from app.memory.redis_client import redis_client
from app.memory.postgres_client import postgres_client
from app.config import settings

class MemoryManager:
    """记忆管理器：协调 Redis（中期记忆）与 PostgreSQL（持久记忆）的双层架构。

    写入时优先持久化到 PG 再写 Redis；读取时优先读 Redis，不足则从 PG 补全并回填。
    """
    async def get_session_history(self, session_id: str, limit: int = 20) -> List[dict]:
        """获取会话历史，自动处理 Redis → PG 的降级与回填。

        Args:
            session_id: 会话唯一标识。
            limit: 返回消息数量上限，默认 20。

        Returns:
            按时间正序排列的消息字典列表。
        """
        # 1. 先查 Redis（热缓存）
        redis_history = await redis_client.get_history(session_id, limit)
        if len(redis_history) >= limit:
            return redis_history
        
        # 2. Redis 数据不足，从 PG（持久层）补全
        pg_history = await postgres_client.get_history(session_id, limit)
        if len(pg_history) > len(redis_history):
            # 用完整数据回填 Redis
            await redis_client.clear_session(session_id)
            for msg in pg_history:
                await redis_client.rpush_raw(session_id, json.dumps(msg, ensure_ascii=False))
            await redis_client.expire(session_id,settings.REDIS_SESSION_TTL)
            return pg_history
        
        return redis_history

    async def append_user_message(self, session_id: str, content: str) -> None:
        """追加用户消息到双层存储。

        Args:
            session_id: 会话唯一标识。
            content: 用户消息正文。
        """
        await postgres_client.add_message(session_id, role="user", content=content)
        await redis_client.add_message(session_id, role="user", content=content)

    async def append_assistant_message(self, session_id: str, content: str, msg_type: str = "text") -> None:
        """追加助手消息到双层存储。

        Args:
            session_id: 会话唯一标识。
            content: 助手生成的消息正文。
            msg_type: 消息类型，如 ``text`` 或 ``code``，默认 ``text``。
        """
        await postgres_client.add_message(session_id, role="assistant", content=content, msg_type=msg_type)
        await redis_client.add_message(session_id, role="assistant", content=content, msg_type=msg_type)

    async def clear_session(self, session_id: str) -> None:
        """清除指定会话在 Redis 与 PG 中的全部历史。

        Args:
            session_id: 会话唯一标识。
        """
        await postgres_client.clear_session(session_id)
        await redis_client.clear_session(session_id)

memory_manager = MemoryManager()