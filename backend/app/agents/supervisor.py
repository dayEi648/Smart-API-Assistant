# backend/app/agents/supervisor.py
import re
from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from app.config import settings
from app.agents.state import AgentState


_CODEGEN_KEYWORDS = re.compile(
    r"(代码|怎么写|生成|写个|示例|snippet|curl|python|java|javascript|typescript|golang|代码示例)",
    re.IGNORECASE,
)


class SupervisorAgent:
    """Supervisor Agent：基于 LangGraph 的意图识别与路由中心。

    先通过规则引擎快速分类，规则未命中时调用 LLM（temperature=0.0）兜底，
    最终根据 ``intent`` 字段将状态路由到 QA Agent 或 CodeGen Agent。
    """

    def __init__(self) -> None:
        """初始化 LLM 与编译后的状态图。"""
        self.llm = ChatOpenAI(
            model=settings.DEEPSEEK_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            temperature=0.0,
        )
        self.graph = self._build_graph()

    def _build_graph(self):
        """构建 LangGraph 状态图：classify → 条件边 → prepare_qa / prepare_codegen → END。

        Returns:
            编译后的状态图对象，可通过 ``ainvoke`` 异步执行。
        """
        graph = StateGraph(AgentState)
        graph.add_node("classify", self._classify_node)
        graph.add_node("prepare_qa", self._prepare_qa_node)
        graph.add_node("prepare_codegen", self._prepare_codegen_node)
        graph.set_entry_point("classify")
        graph.add_conditional_edges(
            "classify",
            self._route,
            {"qa": "prepare_qa", "codegen": "prepare_codegen"},
        )
        graph.add_edge("prepare_qa", END)
        graph.add_edge("prepare_codegen", END)
        return graph.compile()

    def _rule_classify(self, message: str) -> Literal["qa", "codegen", "unknown"]:
        """基于关键词规则的快速意图分类。

        Args:
            message: 用户原始输入。

        Returns:
            ``qa``、``codegen`` 或 ``unknown``（表示规则未命中，需 LLM 兜底）。
        """
        msg_lower = message.lower()
        if _CODEGEN_KEYWORDS.search(msg_lower):
            return "codegen"
        if any(kw in msg_lower for kw in ["是什么", "什么意思", "怎么用", "如何", "介绍"]):
            return "qa"
        return "unknown"

    async def _classify_node(self, state: AgentState) -> AgentState:
        """LangGraph 节点：规则 + LLM 兜底，判断意图并写入 ``state["intent"]``。

        Args:
            state: 当前图状态，必须包含 ``user_message``。

        Returns:
            更新后的状态字典。
        """
        message = state.get("user_message", "")
        rule_result = self._rule_classify(message)
        if rule_result != "unknown":
            state["intent"] = rule_result
            return state

        system_prompt = (
            "你是一个意图分类助手。请根据用户输入，判断用户是想：\n"
            "1. 'qa' - 询问 API 的功能、参数、用法等\n"
            "2. 'codegen' - 请求生成调用代码\n"
            "只输出一个单词：qa 或 codegen。"
        )
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=message),
        ]
        response = await self.llm.ainvoke(messages)
        intent_text = response.content.strip().lower()
        state["intent"] = "codegen" if intent_text == "codegen" else "qa"
        return state

    def _route(self, state: AgentState) -> Literal["qa", "codegen"]:
        """条件路由函数：根据 ``intent`` 决定图的出口节点。

        Args:
            state: 当前图状态。

        Returns:
            下一节点名称：``qa`` 或 ``codegen``。
        """
        return state.get("intent", "qa")

    async def _prepare_qa_node(self, state: AgentState) -> AgentState:
        """LangGraph 节点：调用 QA Agent 准备流式生成器。"""
        from app.agents.qa_agent import qa_agent
        return await qa_agent.prepare(state)

    async def _prepare_codegen_node(self, state: AgentState) -> AgentState:
        """LangGraph 节点：调用 CodeGen Agent 准备流式生成器。"""
        from app.agents.codegen_agent import codegen_agent
        return await codegen_agent.prepare(state)

    async def run(self, state: AgentState) -> AgentState:
        """对外接口：执行完整 Supervisor 图（意图识别 + Agent 准备）。

        Args:
            state: 初始状态，至少包含 ``session_id`` 与 ``user_message``。

        Returns:
            执行结束后的状态字典，包含 ``generator``、``save_type`` 等字段。
        """
        return await self.graph.ainvoke(state)


supervisor_agent = SupervisorAgent()
