from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

HTTP_REQUESTS_TOTAL = Counter("http_requests_total", "Total HTTP requests", ["path", "status"])
WEBHOOK_REQUESTS_TOTAL = Counter("webhook_requests_total", "Webhook outcomes", ["result"])
REQUEST_LATENCY = Histogram("request_latency_ms", "Latency ms", buckets=[100, 500, float("inf")])

def track_request(path: str, status: int):
    HTTP_REQUESTS_TOTAL.labels(path=path, status=str(status)).inc()

def track_webhook_outcome(result: str):
    WEBHOOK_REQUESTS_TOTAL.labels(result=result).inc()
