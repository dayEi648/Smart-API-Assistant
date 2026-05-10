# backend/app/agents/qa_agent.py
from typing import AsyncGenerator
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.agents.state import AgentState
from app.rag.retriever import retriever
from app.memory.memory_manager import memory_manager


class QAAgent:
    """问答 Agent：基于 RAG 检索结果回答 API 使用问题。

    负责读取会话历史、检索相关 API 文档、组装 Prompt 并流式生成中文回答。
    """

    def __init__(self) -> None:
        """初始化流式 LLM 客户端（temperature=0.7）。"""
        self.llm = ChatOpenAI(
            model=settings.DEEPSEEK_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            temperature=0.7,
            streaming=True,
        )

    async def prepare(self, state: AgentState) -> AgentState:
        """LangGraph 节点：准备 QA 的流式生成器并写入 ``state``。

        Args:
            state: 当前图状态，必须包含 ``session_id`` 与 ``user_message``。

        Returns:
            更新后的状态字典，新增 ``generator`` 与 ``save_type`` 字段。
        """
        session_id = state["session_id"]
        user_message = state["user_message"]

        history = await memory_manager.get_session_history(session_id, limit=10)
        docs = await retriever.retrieve(user_message, top_k=5)
        context = "\n\n".join(f"[相关文档 {i+1}]\n{doc['content']}" for i, doc in enumerate(docs))

        system_prompt = (
            "你是一个 API 文档智能助手。请基于以下提供的 API 文档片段回答用户问题。\n"
            "1. 必须基于提供的文档内容，不要编造未提及的参数\n"
            "2. 如果文档中没有相关信息，明确告知用户\n"
            "3. 在回答中引用相关文档片段的来源端点\n"
            "4. 保持简洁、准确，使用中文回答\n\n"
            f"【相关文档片段】\n{context}"
        )

        messages = [SystemMessage(content=system_prompt)]
        for h in history:
            if h["role"] == "user":
                messages.append(HumanMessage(content=h["content"]))
            else:
                messages.append(AIMessage(content=h["content"]))
        if not history or history[-1].get("role") != "user" or history[-1].get("content") != user_message:
            messages.append(HumanMessage(content=user_message))

        state["generator"] = self._wrap_generator(self.llm.astream(messages), session_id)
        state["save_type"] = "text"
        return state

    async def _wrap_generator(self, gen, session_id: str):
        """包装 LLM 异步生成器，在流式输出结束后自动持久化完整回答。

        Args:
            gen: LLM 原始异步生成器（yield ``AIMessageChunk``）。
            session_id: 当前会话 ID，用于持久化。

        Yields:
            字典：``{"type": "text", "content": "片段"}``。
        """
        full_answer = ""
        try:
            async for chunk in gen:
                text = chunk.content
                if text:
                    full_answer += text
                    yield {"type": "text", "content": text}
        finally:
            if full_answer:
                try:
                    await memory_manager.append_assistant_message(session_id, full_answer, msg_type="text")
                except Exception:
                    pass

    async def stream_answer(self, session_id: str, user_message: str) -> AsyncGenerator[str, None]:
        """独立测试用的兼容包装：调用 prepare 后消费 generator。

        Args:
            session_id: 会话唯一标识。
            user_message: 用户输入内容。

        Yields:
            回答文本片段。
        """
        state: AgentState = {"session_id": session_id, "user_message": user_message}
        state = await self.prepare(state)
        generator = state.get("generator")
        if not generator:
            return
        async for item in generator:
            yield item.get("content", "")


qa_agent = QAAgent()
