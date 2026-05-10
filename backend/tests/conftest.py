# backend/tests/conftest.py
import pytest
from app.parser.tasks import clear_tasks
from app.rag.vector_store import vector_store
from app.mcp.session import mcp_session_manager
from app.mcp.server import message_queues
from app.memory.postgres_client import postgres_client


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """测试自动清理 Fixture：在每个测试结束后清空任务、向量库与 MCP 会话数据。"""
    yield
    clear_tasks()
    try:
        vector_store.delete_all()
    except Exception:
        pass
    mcp_session_manager.clear_all()
    message_queues.clear()
