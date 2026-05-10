# backend/tests/test_supervisor.py
import pytest
from app.agents.supervisor import supervisor_agent
from app.agents.state import AgentState


@pytest.mark.asyncio
async def test_supervisor_rule_codegen():
    state: AgentState = {"user_message": "生成登录代码"}
    result = await supervisor_agent._classify_node(state)
    assert result["intent"] == "codegen"


@pytest.mark.asyncio
async def test_supervisor_rule_qa():
    state: AgentState = {"user_message": "登录接口怎么用"}
    result = await supervisor_agent._classify_node(state)
    assert result["intent"] == "qa"


@pytest.mark.asyncio
async def test_supervisor_rule_default():
    state: AgentState = {"user_message": "今天天气怎样"}
    result = await supervisor_agent._classify_node(state)
    assert result["intent"] == "qa"
