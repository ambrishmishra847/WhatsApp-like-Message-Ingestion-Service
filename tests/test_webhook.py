import hmac
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app, db
from app.models import init_sqlite_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    # Ensure tables exist
    init_sqlite_db(":memory:")
    # Clear between tests
    conn = db._get_conn()
    conn.execute("DELETE FROM messages")
    conn.commit()
    conn.close()

def get_signature(body: str, secret: str):
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()

def test_webhook_success():
    payload = {
        "message_id": "m1",
        "from": "+919876543210",
        "to": "+14155550100",
        "ts": "2025-01-15T10:00:00Z",
        "text": "Hello"
    }
    body = json.dumps(payload)
    sig = get_signature(body, "testsecret")
    
    response = client.post(
        "/webhook",
        content=body,
        headers={"x-signature": sig}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_webhook_idempotency():
    payload = {
        "message_id": "m-idemp",
        "from": "+1",
        "to": "+2",
        "ts": "2025-01-15T10:00:00Z"
    }
    body = json.dumps(payload)
    sig = get_signature(body, "testsecret")
    
    # First
    r1 = client.post("/webhook", content=body, headers={"x-signature": sig})
    assert r1.status_code == 200
    
    # Second
    r2 = client.post("/webhook", content=body, headers={"x-signature": sig})
    assert r2.status_code == 200 # Should still be 200
    
    # Verify only one row exists
    stats = client.get("/stats").json()
    assert stats["total_messages"] == 1

def test_webhook_invalid_signature():
    payload = {"message_id": "m2", "from": "+1", "to": "+2", "ts": "2025-01-15T10:00:00Z"}
    response = client.post(
        "/webhook",
        json=payload,
        headers={"x-signature": "wrong"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid signature"

def test_webhook_missing_signature():
    payload = {"message_id": "m3", "from": "+1", "to": "+2", "ts": "2025-01-15T10:00:00Z"}
    response = client.post("/webhook", json=payload)
    assert response.status_code == 401
