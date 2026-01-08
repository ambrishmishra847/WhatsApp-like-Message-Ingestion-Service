import logging
import json
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import os

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_tags"):
            log_obj.update(record.extra_tags)
        return json.dumps(log_obj)

logger = logging.getLogger("app")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            # We log generic requests here. 
            # /webhook specific details (dups/results) are logged in the route handler.
            if request.url.path != "/webhook":
                latency = (time.time() - start_time) * 1000
                log_data = {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "latency_ms": round(latency, 2)
                }
                logger.info("Request processed", extra={"extra_tags": log_data})
        return response
