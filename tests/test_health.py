from fastapi.testclient import TestClient

from app.api import app


def test_health_answers_ok() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
