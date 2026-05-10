# backend/app/agents/state.py
from typing import TypedDict, List, Optional, Literal, Any


class AgentState(TypedDict, total=False):
    """LangGraph 多 Agent 共享状态定义。

    各节点通过读写此状态字典实现数据流转。``total=False`` 表示所有字段均为可选，
    节点可按需填充，避免初始化时传入全部字段。
    """
    session_id: str
    user_message: str
    history: List[dict]
    intent: Literal["qa", "codegen"]
    retrieved_docs: List[dict]
    generator: Any
    save_type: str
    code_lang: Optional[str]
    final_answer: str
