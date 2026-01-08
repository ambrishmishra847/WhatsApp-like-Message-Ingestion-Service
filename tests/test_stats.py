import pytest
from fastapi.testclient import TestClient
from app.main import app, db

client = TestClient(app)

@pytest.fixture(autouse=True)
def seed_data():
    conn = db._get_conn()
    conn.execute("DELETE FROM messages")
    messages = [
        ("m1", "+911", "+100", "2025-01-10T10:00:00Z", "hi", "now"),
        ("m2", "+911", "+100", "2025-01-12T10:00:00Z", "hi", "now"),
        ("m3", "+912", "+100", "2025-01-15T10:00:00Z", "hi", "now"),
    ]
    conn.executemany("INSERT INTO messages (message_id, from_msisdn, to_msisdn, ts, text, created_at) VALUES (?,?,?,?,?,?)", messages)
    conn.commit()
    conn.close()

def test_stats_correctness():
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_messages"] == 3
    assert data["senders_count"] == 2
    assert len(data["messages_per_sender"]) == 2
    
    # Check top sender
    assert data["messages_per_sender"][0]["from"] == "+911"
    assert data["messages_per_sender"][0]["count"] == 2
    
    # Check timing
    assert data["first_message_ts"] == "2025-01-10T10:00:00Z"
    assert data["last_message_ts"] == "2025-01-15T10:00:00Z"

def test_stats_empty():
    conn = db._get_conn()
    conn.execute("DELETE FROM messages")
    conn.commit()
    conn.close()
    
    response = client.get("/stats")
    data = response.json()
    assert data["total_messages"] == 0
    assert data["first_message_ts"] is None
    assert data["last_message_ts"] is None
