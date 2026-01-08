import hmac
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app, db

client = TestClient(app)

@pytest.fixture(autouse=True)
def seed_data():
    conn = db._get_conn()
    conn.execute("DELETE FROM messages")
    messages = [
        ("m1", "+911", "+100", "2025-01-15T10:00:00Z", "apple", "now"),
        ("m2", "+912", "+100", "2025-01-15T11:00:00Z", "banana", "now"),
        ("m3", "+911", "+200", "2025-01-15T12:00:00Z", "cherry", "now"),
    ]
    conn.executemany("INSERT INTO messages (message_id, from_msisdn, to_msisdn, ts, text, created_at) VALUES (?,?,?,?,?,?)", messages)
    conn.commit()
    conn.close()

def test_list_all():
    response = client.get("/messages")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["data"]) == 3

def test_pagination():
    response = client.get("/messages?limit=2&offset=0")
    data = response.json()
    assert data["total"] == 3
    assert len(data["data"]) == 2
    assert data["data"][0]["message_id"] == "m1"
    
    response = client.get("/messages?limit=2&offset=2")
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["message_id"] == "m3"

def test_filter_from():
    response = client.get("/messages?from=+911")
    data = response.json()
    assert data["total"] == 2
    assert all(m["from"] == "+911" for m in data["data"])

def test_filter_since():
    response = client.get("/messages?since=2025-01-15T11:00:00Z")
    data = response.json()
    assert data["total"] == 2
    assert data["data"][0]["message_id"] == "m2"

def test_filter_q():
    response = client.get("/messages?q=ana")
    data = response.json()
    assert data["total"] == 1
    assert data["data"][0]["text"] == "banana"
