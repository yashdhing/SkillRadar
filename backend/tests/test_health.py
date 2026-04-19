from fastapi.testclient import TestClient

from skillradar_api.main import app


client = TestClient(app)


def test_healthcheck_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_root_returns_ready_message() -> None:
    response = client.get("/api/v1")

    assert response.status_code == 200
    assert response.json() == {"message": "SkillRadar backend is ready."}
