import logging
import os
import time
from collections import Counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from finance_analyzer.api.routes import upload, analysis, forecast

logger = logging.getLogger("finance_analyzer.api")

request_metrics = {
    "total": 0,
    "success": 0,
    "failure": 0,
    "status_counts": Counter(),
    "path_counts": Counter(),
}

app = FastAPI(
    title="Finance Analyzer API",
    description = "Personal Finance analysis with ML",
    version="1.0.0",
)

cors_origins_raw = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000")
cors_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],   # allow all HTTP methods
    allow_headers=["*"],   # allow all headers
)

app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(forecast.router)


@app.middleware("http")
async def request_observability(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    started_at = time.perf_counter()
    path = request.url.path
    request_metrics["total"] += 1
    request_metrics["path_counts"][path] += 1

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        request_metrics["failure"] += 1
        request_metrics["status_counts"]["500"] += 1
        logger.exception(
            "request_failed method=%s path=%s request_id=%s duration_ms=%.2f",
            request.method,
            path,
            request_id,
            duration_ms,
        )
        raise

    if response.status_code >= 400:
        request_metrics["failure"] += 1
    else:
        request_metrics["success"] += 1
    request_metrics["status_counts"][str(response.status_code)] += 1

    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    logger.info(
        "request_completed method=%s path=%s status=%s request_id=%s duration_ms=%.2f",
        request.method,
        path,
        response.status_code,
        request_id,
        duration_ms,
    )
    response.headers["x-request-id"] = request_id
    return response

@app.get("/")
async def root():
    return {"message": "Finance Analyzer API is running"}


@app.get("/ops/metrics")
async def metrics():
    return {
        "requests": {
            "total": request_metrics["total"],
            "success": request_metrics["success"],
            "failure": request_metrics["failure"],
        },
        "status_counts": dict(request_metrics["status_counts"]),
        "path_counts": dict(request_metrics["path_counts"]),
    }