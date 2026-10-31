from fastapi.testclient import TestClient

from app.main import app


def test_health():
    r = TestClient(app).get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_cors_allows_configured_origin():
    r = TestClient(app).get("/api/v1/health", headers={"Origin": "http://localhost:3000"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"
