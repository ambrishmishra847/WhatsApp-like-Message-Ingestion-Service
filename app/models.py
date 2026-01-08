from pydantic import BaseModel, Field
from typing import Optional, List
import sqlite3
import os

# E.164-like regex: starts with +, then digits only
PHONE_REGEX = r"^\+\d+$"
# ISO-8601 UTC with Z suffix: e.g. 2025-01-15T10:00:00Z
ISO_Z_REGEX = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"

class WebhookPayload(BaseModel):
    message_id: str = Field(..., min_length=1)
    from_msisdn: str = Field(..., alias="from", pattern=PHONE_REGEX)
    to_msisdn: str = Field(..., alias="to", pattern=PHONE_REGEX)
    ts: str = Field(..., pattern=ISO_Z_REGEX)
    text: Optional[str] = Field(None, max_length=4096)

class MessageResponse(BaseModel):
    message_id: str
    from_msisdn: str = Field(..., alias="from")
    to_msisdn: str = Field(..., alias="to")
    ts: str
    text: Optional[str] = None

class PaginatedResponse(BaseModel):
    data: List[MessageResponse]
    total: int
    limit: int
    offset: int

class StatsResponse(BaseModel):
    total_messages: int
    senders_count: int
    messages_per_sender: List[dict]
    first_message_ts: Optional[str]
    last_message_ts: Optional[str]

def init_sqlite_db(db_path: str):
    """
    SQLite init: create tables and indexes
    """
    # SQLite URL might be sqlite:////data/app.db
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")
    
    if db_path != ":memory:":
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            from_msisdn TEXT NOT NULL,
            to_msisdn TEXT NOT NULL,
            ts TEXT NOT NULL,
            text TEXT,
            created_at TEXT NOT NULL
        );
    """)
    # Index for filtering/ordering
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_from ON messages(from_msisdn);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_ts ON messages(ts);")
    conn.commit()
    conn.close()
    return db_path
