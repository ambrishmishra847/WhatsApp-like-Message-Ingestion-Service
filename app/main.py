import hmac
import hashlib
import json
import time
from typing import Optional, List
from fastapi import FastAPI, Request, HTTPException, Header, Response, Depends, Query
from pydantic import ValidationError

from app.config import get_settings
from app.models import WebhookPayload, PaginatedResponse, StatsResponse, init_sqlite_db
from app.storage import Database
from app.logging_utils import logger, StructuredLoggingMiddleware
from app.metrics import generate_latest, CONTENT_TYPE_LATEST, track_request, track_webhook_outcome

app = FastAPI()
app.add_middleware(StructuredLoggingMiddleware)

settings = get_settings()

# Fail startup if WEBHOOK_SECRET is not set (12-factor)
if not settings.WEBHOOK_SECRET:
    logger.critical("WEBHOOK_SECRET environment variable is NOT set. Exiting.")
    raise RuntimeError("WEBHOOK_SECRET must be set")

# Init DB schema
db_path = init_sqlite_db(settings.DATABASE_URL)
db = Database(db_path)

# --- Dependencies ---

async def verify_signature(request: Request, x_signature: str = Header(None)):
    if not x_signature:
        track_webhook_outcome("invalid_signature")
        logger.error("Missing X-Signature header")
        raise HTTPException(status_code=401, detail={"detail": "invalid signature"})
    
    body_bytes = await request.body()
    secret = settings.WEBHOOK_SECRET
    
    computed_sig = hmac.new(secret.encode(), body_bytes, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(computed_sig, x_signature):
        track_webhook_outcome("invalid_signature")
        logger.error("Invalid HMAC signature")
        raise HTTPException(status_code=401, detail={"detail": "invalid signature"})
    
    return body_bytes

# --- Routes ---

@app.post("/webhook")
async def webhook(request: Request, body_bytes: bytes = Depends(verify_signature)):
    start_time = time.time()
    result = "unknown"
    msg_id = None
    
    try:
        payload_dict = json.loads(body_bytes)
        payload = WebhookPayload(**payload_dict)
        msg_id = payload.message_id
        
        # Idempotent insert
        result = db.insert_message(payload.model_dump(by_alias=True))
        
        return {"status": "ok"}

    except (json.JSONDecodeError, ValidationError) as e:
        result = "validation_error"
        # Extract msg_id if possible for logging
        try:
            temp_data = json.loads(body_bytes)
            msg_id = temp_data.get("message_id")
        except:
            pass
        raise HTTPException(status_code=422, detail=json.loads(e.json()) if isinstance(e, ValidationError) else "Invalid JSON")
    except Exception as e:
        result = "server_error"
        logger.error(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Error")
    finally:
        latency = (time.time() - start_time) * 1000
        # Determine status for metrics
        if result in ["created", "duplicate"]:
            status_code = 200
        elif result == "validation_error":
            status_code = 422
        else:
            status_code = 500
        
        track_request("/webhook", status_code)
        track_webhook_outcome(result)

        # Structured JSON Logs
        log_data = {
            "request_id": getattr(request.state, "request_id", "n/a"),
            "method": "POST",
            "path": "/webhook",
            "status": status_code,
            "latency_ms": round(latency, 2),
            "result": result,
            "dup": (result == "duplicate"),
            "message_id": msg_id
        }
        logger.info("Webhook processed", extra={"extra_tags": log_data})

@app.get("/messages", response_model=PaginatedResponse)
def list_messages(
    limit: int = Query(50, ge=1, le=100), 
    offset: int = Query(0, ge=0), 
    from_param: Optional[str] = Query(None, alias="from"),
    since: Optional[str] = None, 
    q: Optional[str] = None
):
    data, total = db.get_messages(limit, offset, from_param, since, q)
    track_request("/messages", 200)
    
    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/stats", response_model=StatsResponse)
def get_stats():
    stats = db.get_stats()
    track_request("/stats", 200)
    return stats

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health/live")
def liveness():
    return {"status": "ok"}

@app.get("/health/ready")
def readiness():
    # Readiness depends on DB and secret
    if not settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="WEBHOOK_SECRET missing")
    if not db.check_health():
        raise HTTPException(status_code=503, detail="Database connection failed")
    return {"status": "ready"}
