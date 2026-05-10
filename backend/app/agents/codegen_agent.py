# backend/app/agents/codegen_agent.py
import re
from typing import AsyncGenerator, Optional, Tuple
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.agents.state import AgentState
from app.rag.retriever import retriever
from app.memory.memory_manager import memory_manager


_LANG_PATTERN = re.compile(
    r"(python|java|javascript|js|typescript|ts|c\+\+|cpp|go|golang|curl|bash|shell|ruby|php|csharp|c#)",
    re.IGNORECASE,
)


class CodeGenAgent:
    """代码生成 Agent：根据用户描述生成多语言 API 调用代码。

    自动从消息中提取目标语言（默认 Python，temperature=0.3 减少幻觉），
    检索相关端点后流式生成带注释的代码片段。
    """

    def __init__(self) -> None:
        """初始化流式 LLM 客户端（temperature=0.3）。"""
        self.llm = ChatOpenAI(
            model=settings.DEEPSEEK_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            temperature=0.3,
            streaming=True,
        )

    def _extract_language(self, message: str) -> str:
        """从用户消息中提取目标编程语言。

        Args:
            message: 用户原始输入。

        Returns:
            标准化后的语言名称（如 ``python``、``javascript``、``go``），
            未匹配到则默认返回 ``python``。
        """
        match = _LANG_PATTERN.search(message)
        if match:
            lang = match.group(1).lower()
            alias_map = {"js": "javascript", "ts": "typescript", "cpp": "c++", "golang": "go", "shell": "bash", "c#": "csharp"}
            return alias_map.get(lang, lang)
        return "python"

    async def prepare(self, state: AgentState) -> AgentState:
        """LangGraph 节点：准备 CodeGen 的流式生成器并写入 ``state``。

        Args:
            state: 当前图状态，必须包含 ``session_id`` 与 ``user_message``。

        Returns:
            更新后的状态字典，新增 ``generator``、``save_type``、``code_lang`` 字段。
        """
        session_id = state["session_id"]
        user_message = state["user_message"]
        target_lang = self._extract_language(user_message)
        history = await memory_manager.get_session_history(session_id, limit=10)
        docs = await retriever.retrieve(user_message, top_k=3)

        if not docs:
            state["generator"] = self._wrap_no_docs(session_id)
            state["save_type"] = "text"
            return state

        context = docs[0]["content"]
        system_prompt = (
            f"你是一个专业的 API 代码生成助手。请基于以下 API 文档，生成 {target_lang} 的调用代码。\n"
            "1. 代码必须严格基于文档中的参数定义，禁止编造字段\n"
            "2. 为每个关键步骤添加简洁的中文注释\n"
            "3. 包含完整的 import/依赖声明\n"
            "4. 处理常见的错误情况\n"
            "5. 将代码包裹在 Markdown 代码块中\n\n"
            f"【API 文档详情】\n{context}"
        )

        messages = [SystemMessage(content=system_prompt)]
        for h in history:
            if h["role"] == "user":
                messages.append(HumanMessage(content=h["content"]))
            else:
                messages.append(AIMessage(content=h["content"]))
        if not history or history[-1].get("role") != "user" or history[-1].get("content") != user_message:
            messages.append(HumanMessage(content=user_message))

        state["generator"] = self._wrap_generator(self.llm.astream(messages), session_id, target_lang)
        state["save_type"] = "code"
        state["code_lang"] = target_lang
        return state

    async def _wrap_no_docs(self, session_id: str):
        """当未检索到相关文档时返回提示信息。

        Args:
            session_id: 当前会话 ID。

        Yields:
            提示文本字典。
        """
        msg = "根据现有文档，未能找到与该请求相关的 API 端点。请先上传 API 文档。"
        try:
            yield {"type": "text", "content": msg}
        finally:
            try:
                await memory_manager.append_assistant_message(session_id, msg, msg_type="text")
            except Exception:
                pass

    async def _wrap_generator(self, gen, session_id: str, target_lang: str):
        """包装 LLM 异步生成器，在流式输出结束后自动持久化完整代码。

        Args:
            gen: LLM 原始异步生成器。
            session_id: 当前会话 ID，用于持久化。
            target_lang: 目标编程语言标识。

        Yields:
            字典：``{"type": "code", "content": "片段", "lang": "python"}``。
        """
        full_code = ""
        try:
            async for chunk in gen:
                text = chunk.content
                if text:
                    full_code += text
                    yield {"type": "code", "content": text, "lang": target_lang}
        finally:
            if full_code:
                try:
                    await memory_manager.append_assistant_message(session_id, full_code, msg_type="code")
                except Exception:
                    pass

    async def stream_code(self, session_id: str, user_message: str) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        """独立测试和 MCP 用的兼容包装：调用 prepare 后消费 generator。

        Args:
            session_id: 会话唯一标识。
            user_message: 用户输入内容。

        Yields:
            二元组 ``(text_fragment, lang)``。
        """
        state: AgentState = {"session_id": session_id, "user_message": user_message}
        state = await self.prepare(state)
        generator = state.get("generator")
        if not generator:
            return
        async for item in generator:
            yield (item.get("content", ""), item.get("lang"))


codegen_agent = CodeGenAgent()
