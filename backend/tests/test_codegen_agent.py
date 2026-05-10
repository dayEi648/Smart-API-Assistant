# backend/tests/test_codegen_agent.py
import pytest
from app.agents.codegen_agent import codegen_agent


def test_extract_language_python():
    assert codegen_agent._extract_language("生成 Python 代码") == "python"


def test_extract_language_java():
    assert codegen_agent._extract_language("给我写个Java示例") == "java"


def test_extract_language_curl():
    assert codegen_agent._extract_language("curl 调用") == "curl"


def test_extract_language_default():
    assert codegen_agent._extract_language("怎么调用这个接口") == "python"


def test_extract_language_alias_js():
    assert codegen_agent._extract_language("用 js 写") == "javascript"


def test_extract_language_alias_golang():
    assert codegen_agent._extract_language("golang 版本") == "go"
