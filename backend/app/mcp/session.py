# backend/app/mcp/session.py
import uuid
from typing import Dict, Optional


class MCPSessionManager:
    """MCP SSE 会话管理器。

    维护 ``session_id → POST endpoint URL`` 的映射，用于 SSE 长连接建立后
    告知客户端向哪个 URL 发送 JSON-RPC 请求。
    """

    def __init__(self):
        """初始化内存会话存储。"""
        self._sessions: Dict[str, str] = {}

    def create_session(self) -> str:
        """创建新会话并生成对应的 POST endpoint URL。

        Returns:
            新生成的会话 ID（UUID）。
        """
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = f"/mcp/v1/messages?session_id={session_id}"
        return session_id

    def get_post_endpoint(self, session_id: str) -> Optional[str]:
        """获取指定会话的 POST endpoint URL。

        Args:
            session_id: 会话唯一标识。

        Returns:
            对应的 POST URL，若会话不存在则返回 ``None``。
        """
        return self._sessions.get(session_id)

    def remove_session(self, session_id: str) -> None:
        """移除指定会话。

        Args:
            session_id: 会话唯一标识。
        """
        self._sessions.pop(session_id, None)

    def clear_all(self) -> None:
        """清空所有会话（测试清理用）。"""
        self._sessions.clear()


mcp_session_manager = MCPSessionManager()
