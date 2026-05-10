# backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_empty_file():
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("", b"", "application/json")},
    )
    assert response.status_code == 400
    assert response.json()["code"] == 40001


def test_upload_unsupported_format():
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["code"] == 40001


def test_get_task_not_found():
    response = client.get("/api/v1/documents/tasks/nonexistent-task-id")
    assert response.status_code == 404
    assert response.json()["code"] == 40401


def test_chat_missing_sse_header():
    response = client.post(
        "/api/v1/chat",
        json={"session_id": "test", "message": "hello"},
    )
    assert response.status_code == 406
    assert response.json()["code"] == 40004


def test_search_empty_query():
    response = client.get("/api/v1/knowledge/search?q=")
    assert response.status_code == 400
    assert response.json()["code"] == 40005


def test_mcp_sse_missing_header():
    response = client.get("/mcp/v1/sse")
    assert response.status_code == 406
