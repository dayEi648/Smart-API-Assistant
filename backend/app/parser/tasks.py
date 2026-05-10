import uuid 
import time
from typing import Dict, Optional
from app.parser.parser_agent import parser_agent
from app.models.document import TaskStatus, ParserResult

task_store: Dict[str, dict] = {}
"""内存任务状态存储（MVP 阶段），以 task_id 为键。"""

def create_task() -> str:
    """
    创建一个新的解析任务，初始状态为 ``PENDING``。

    Returns:
        生成的唯一任务 ID（UUID）。
    """
    task_id = str(uuid.uuid4())
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    task_store[task_id] = {
        "task_id": task_id,
        "status": TaskStatus.PENDING,
        "created_at": now,
        "updated_at": now,
        "result": None,
        "error": None,
    }
    return task_id

async def run_parse_task(task_id: str, content: bytes, filename: str, doc_id: str) -> None:
    """执行文档解析与索引任务，并更新任务状态。

    Args:
        task_id: 任务唯一标识。
        content: 文档原始字节内容。
        filename: 原始文件名。
        doc_id: 文档唯一标识。
    """
    task_store[task_id]["status"] = TaskStatus.PROCESSING
    try:
        result = await parser_agent.parse_and_index(content, filename, doc_id)
        task_store[task_id]["status"] = TaskStatus.COMPLETED
        task_store[task_id]["result"] = ParserResult(**result).model_dump()
    except Exception as e:
        task_store[task_id]["status"] = TaskStatus.FAILED
        task_store[task_id]["error"] = str(e)
    task_store[task_id]["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def get_task_status(task_id: str) -> Optional[dict]:
    """查询指定任务的当前状态。

    Args:
        task_id: 任务唯一标识。

    Returns:
        任务状态字典，若不存在则返回 ``None``。
    """
    return task_store.get(task_id)

def clear_tasks() -> None:
    """清空所有任务记录（测试清理用）。"""
    task_store.clear()
