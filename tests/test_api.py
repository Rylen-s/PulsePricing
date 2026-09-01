from fastapi.testclient import TestClient

from app.main import app


def test_event_creates_risk_snapshot():
    with TestClient(app) as client:
        response = client.post(
            "/v1/events", json={"symbol": "spy", "headline": "Markets rally on strong growth"}
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "SPY"
    assert payload["sentiment"]["score"] > 0
    assert len(payload["distribution"]) == 99
