import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_experiments():
    response = client.get("/api/v1/experiments")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # The evaluation/results folder has historical data, so this should return some
    if len(data) > 0:
        first = data[0]
        assert "id" in first
        assert "scenario" in first
        assert "status" in first

def test_get_experiment_invalid():
    response = client.get("/api/v1/experiments/invalid-id-does-not-exist")
    assert response.status_code == 404

def test_get_projects_empty():
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    assert response.json() == []

def test_get_project_invalid():
    response = client.get("/api/v1/projects/123")
    assert response.status_code == 404

def test_get_tasks_empty():
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    assert response.json() == []

def test_get_task_invalid():
    response = client.get("/api/v1/tasks/123")
    assert response.status_code == 404

def test_get_artifacts_empty():
    response = client.get("/api/v1/artifacts")
    assert response.status_code == 200
    assert response.json() == []

def test_get_qa_invalid():
    response = client.get("/api/v1/qa/123")
    assert response.status_code == 404

def test_get_delivery_invalid():
    response = client.get("/api/v1/delivery/123")
    assert response.status_code == 404

def test_get_agents_status():
    response = client.get("/api/v1/agents/status")
    assert response.status_code == 200
    assert response.json() == {"status": "idle"}

def test_get_experiment_live():
    response = client.get("/api/v1/experiments/123/live")
    assert response.status_code == 200
    data = response.json()
    assert data["experiment_id"] == "123"
    assert data["status"] == "unknown"

def test_get_experiment_tasks_live():
    response = client.get("/api/v1/experiments/123/tasks/live")
    assert response.status_code == 200
    assert response.json() == []

def test_get_experiment_events():
    response = client.get("/api/v1/experiments/123/events")
    assert response.status_code == 200
    assert response.json() == []
