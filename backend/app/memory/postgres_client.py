import asyncpg
from typing import List
from app.config import settings

class PostgresClient:
    """PostgreSQL 持久记忆客户端。

    基于 ``asyncpg`` 连接池管理对话历史的长期存储。
    提供建表、写入、查询与清理能力，作为 Redis 过期后的兜底持久层。
    """

    def __init__(self) -> None:
        """初始化连接池引用（延迟连接）。"""
        self.pool: asyncpg.pool | None = None

    async def connect(self) -> None:
        """创建异步连接池（幂等：已连接则直接返回）。"""
        if self.pool is not None:
            return
        self.pool = await asyncpg.create_pool(
            settings.DATABASE_URL, min_size=1, max_size=5
        )
    
    async def close(self) -> None:
        """关闭连接池，释放资源。"""
        if self.pool:
            await self.pool.close()

    async def init_tables(self) -> None:
        """初始化数据表与索引（幂等：IF NOT EXISTS）。"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(64) NOT NULL,
                    role VARCHAR(16) NOT NULL,
                    content TEXT NOT NULL,
                    msg_type VARCHAR(16),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_session_created ON chat_messages(session_id, created_at);
            """)
    
    async def add_message(
        self, session_id: str, role: str, content: str, msg_type: str | None = None
    ) -> None:
        """向持久层插入一条消息。

        Args:
            session_id: 会话唯一标识。
            role: 消息角色，如 ``user`` 或 ``assistant``。
            content: 消息正文。
            msg_type: 消息类型，如 ``text`` 或 ``code``，默认为 ``None``。
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO chat_messages (session_id, role, content, msg_type) VALUES ($1, $2, $3, $4)",
                session_id, role, content, msg_type
            )
    
    async def get_history(self, session_id: str, limit: int = 20) -> List[dict]:
        """查询指定会话的最近 N 条消息（按时间正序返回）。

        Args:
            session_id: 会话唯一标识。
            limit: 返回消息数量上限，默认 20。

        Returns:
            消息字典列表，每条包含 ``role``、``content``、``type``、``timestamp``。
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT role, content, msg_type, created_at FROM chat_messages WHERE session_id = $1 ORDER BY created_at DESC LIMIT $2",
                session_id, limit,
            )
            history = []
            for row in reversed(rows):
                history.append({
                    "role": row["role"],
                    "content": row["content"],
                    "type": row["msg_type"],
                    "timestamp": row["created_at"].isoformat() if row["created_at"] else None,
                })
            return history
    
    async def clear_session(self, session_id: str) -> None:
        """删除指定会话的全部持久化消息。

        Args:
            session_id: 会话唯一标识。
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM chat_messages WHERE session_id = $1",
                session_id,
            )

postgres_client = PostgresClient()