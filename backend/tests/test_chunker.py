# backend/tests/test_chunker.py
import pytest
from app.parser.chunker import OpenAPIChunker


SAMPLE_JSON = (
    '{"paths": {"/api/auth/login": {"post": {"summary": "\u7528\u6237\u767b\u5f55", '
    '"parameters": [{"name": "username", "in": "body", "schema": {"type": "string"}, '
    '"description": "\u7528\u6237\u540d"}]}}}}'
).encode("utf-8")

SAMPLE_YAML = (
    "paths:\n"
    "  /api/users:\n"
    "    get:\n"
    "      summary: \u67e5\u8be2\u7528\u6237\u5217\u8868\n"
    "      tags:\n"
    "        - User\n"
).encode("utf-8")


def test_chunker_json():
    chunker = OpenAPIChunker()
    chunks = chunker.parse(SAMPLE_JSON, "test.json", "doc_001")
    assert len(chunks) == 1
    assert chunks[0]["metadata"]["path"] == "/api/auth/login"
    assert chunks[0]["metadata"]["method"] == "POST"
    assert "\u7528\u6237\u767b\u5f55" in chunks[0]["text"]


def test_chunker_yaml():
    chunker = OpenAPIChunker()
    chunks = chunker.parse(SAMPLE_YAML, "test.yaml", "doc_002")
    assert len(chunks) == 1
    assert chunks[0]["metadata"]["path"] == "/api/users"
    assert chunks[0]["metadata"]["method"] == "GET"
    assert chunks[0]["metadata"]["tags"] == "User"


def test_chunker_empty():
    chunker = OpenAPIChunker()
    chunks = chunker.parse(b'{"paths": {}}', "empty.json", "doc_003")
    assert len(chunks) == 0
