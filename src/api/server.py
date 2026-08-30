"""
RecoverAI: Track 03 AI Revenue Recovery
Step 7A: REST API Service (FastAPI / Uvicorn) - Audited & Hardened

This module implements the production-grade REST API service wrapping the frozen
Step 6D RecoverAI agent (`src.recoverai_agent.RecoverAI`).

Hardening Fixes Included:
1. Bounded streaming request payload limit (2 MB max cap, HTTP 413, no unbounded memory buffering)
2. Asyncio-compatible rate limiter synchronization (asyncio.Lock, 100 req/min, HTTP 429)
3. Application-level global exception handler (@app.exception_handler(Exception), sanitized HTTP 500)
"""

import os
import sys
import json
import time
import hashlib
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, Request, Response, HTTPException, status, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Import frozen Step 6D RecoverAI Agent
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.recoverai_agent import RecoverAI, PROHIBITED_SENSITIVE_CREDENTIALS, FORBIDDEN_FIELDS, get_file_checksum

# Configure server logger (stderr only for internal stack traces)
logger = logging.getLogger("recoverai_api")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
logger.addHandler(handler)

# Initialize FastAPI application
app = FastAPI(
    title="RecoverAI REST API",
    description="Track 03 AI Revenue Recovery Decision Engine API",
    version="1.0.0"
)

# Enable CORS for local UI dashboard development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RecoverAI Agent Instance (Loaded once at startup)
agent_instance = RecoverAI()

# Asyncio-compatible rate limiting state (100 requests per minute per IP)
RATE_LIMIT_CAP = 100
RATE_LIMIT_WINDOW = 60  # seconds
ip_request_history: Dict[str, list] = {}
rate_limit_lock = asyncio.Lock()


class RequestPayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    FIX 1: Bounded streaming request body middleware enforcing a strict 2 MB cap (HTTP 413).
    Prevents memory allocation denial-of-service by aborting as soon as accumulated bytes exceed 2 MB.
    """

    MAX_PAYLOAD_BYTES = 2 * 1024 * 1024  # 2 MB

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.MAX_PAYLOAD_BYTES:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "status": "INVALID_INPUT",
                            "error_code": "PAYLOAD_TOO_LARGE",
                            "message": "Request payload size exceeds maximum allowed limit of 2 MB."
                        }
                    )
            except ValueError:
                pass

        # Stream body chunk-by-chunk to prevent buffering an unbounded request payload
        body_chunks = []
        total_bytes = 0

        async for chunk in request.stream():
            total_bytes += len(chunk)
            if total_bytes > self.MAX_PAYLOAD_BYTES:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "status": "INVALID_INPUT",
                        "error_code": "PAYLOAD_TOO_LARGE",
                        "message": "Request payload size exceeds maximum allowed limit of 2 MB."
                    }
                )
            body_chunks.append(chunk)

        # Store accumulated body for downstream route consumption
        full_body = b"".join(body_chunks)
        request._body = full_body

        async def receive():
            return {"type": "http.request", "body": full_body}

        request._receive = receive
        return await call_next(request)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    FIX 2: Asyncio-compatible rate limiter middleware enforcing 100 requests per minute per client IP (HTTP 429).
    Uses asyncio.Lock to avoid blocking the main event loop.
    """

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()

        async with rate_limit_lock:
            if client_ip not in ip_request_history:
                ip_request_history[client_ip] = []

            # Prune requests outside the sliding window
            ip_request_history[client_ip] = [
                t for t in ip_request_history[client_ip] if now - t < RATE_LIMIT_WINDOW
            ]

            if len(ip_request_history[client_ip]) >= RATE_LIMIT_CAP:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "status": "TOO_MANY_REQUESTS",
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded (maximum 100 requests per minute per IP)."
                    }
                )

            ip_request_history[client_ip].append(now)

        return await call_next(request)


# Register Middlewares
app.add_middleware(RequestPayloadSizeLimitMiddleware)
app.add_middleware(RateLimiterMiddleware)


# FIX 3: FastAPI Application-Level Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Application-level global exception handler catching any unexpected internal errors.
    Returns a sanitized HTTP 500 response while writing diagnostic stack traces strictly to server stderr.
    """
    logger.exception("Sanitized unhandled global exception caught by FastAPI exception handler")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "SYSTEM_ERROR",
            "request_id": "UNKNOWN",
            "error_code": "INTERNAL_ORCHESTRATION_ERROR",
            "message": "Internal orchestration error."
        }
    )


@app.get("/api/v1/health", status_code=status.HTTP_200_OK)
def health_endpoint():
    """
    Health & Provenance Check Endpoint (GET /api/v1/health)
    Returns system status, active audit logger indicator, and SHA-256 provenance hashes.
    """
    return {
        "status": "HEALTHY",
        "service": "RecoverAI REST API",
        "version": "1.0.0",
        "model_artifact_hash": agent_instance.model_artifact_hash,
        "calibrator_artifact_hash": agent_instance.calibrator_artifact_hash,
        "audit_log_active": True
    }


@app.post("/api/v1/recommend", status_code=status.HTTP_200_OK)
def recommend_endpoint(payload: Dict[str, Any] = Body(...), request_id: Optional[str] = None):
    """
    Synchronous Recommendation Endpoint (POST /api/v1/recommend)
    Delegates all recommendation logic directly to RecoverAI.recommend() from Step 6D.
    Executed as a synchronous `def` route so FastAPI handles CPU-bound model inference
    inside its default threadpool executor without blocking the asyncio main event loop.
    """
    try:
        # Pre-check for sensitive payment credentials to return HTTP 400 Bad Request
        for sens in PROHIBITED_SENSITIVE_CREDENTIALS:
            if sens in payload:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "status": "INVALID_INPUT",
                        "error_code": "SENSITIVE_FIELD_REJECTED",
                        "message": f"Prohibited sensitive credential field '{sens}' detected in context."
                    }
                )

        # Pre-check for forbidden leakage fields to return HTTP 400 Bad Request
        for forbidden_key in FORBIDDEN_FIELDS:
            if forbidden_key in payload:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "status": "INVALID_INPUT",
                        "error_code": "LEAKAGE_FIELD_REJECTED",
                        "message": f"Forbidden post-decision leakage field '{forbidden_key}' detected in context."
                    }
                )

        # Delegate recommendation to frozen Step 6D Agent Engine
        result = agent_instance.recommend(payload, request_id=request_id)

        if result.get("status") == "INVALID_INPUT":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=result
            )

        if result.get("status") == "SYSTEM_ERROR":
            logger.error(f"Internal orchestration system error in recommend(): {result}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": "SYSTEM_ERROR",
                    "request_id": result.get("request_id", "UNKNOWN"),
                    "error_code": "INTERNAL_ORCHESTRATION_ERROR",
                    "message": "Internal orchestration error."
                }
            )

        # Attach SHA-256 provenance hashes to output payload
        result["model_artifact_hash"] = agent_instance.model_artifact_hash
        result["calibrator_artifact_hash"] = agent_instance.calibrator_artifact_hash

        return result

    except Exception as e:
        # Log raw stack trace to stderr ONLY
        logger.exception("Sanitized unhandled exception in REST API endpoint POST /api/v1/recommend")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "SYSTEM_ERROR",
                "request_id": "UNKNOWN",
                "error_code": "INTERNAL_ORCHESTRATION_ERROR",
                "message": "Internal orchestration error."
            }
        )


if __name__ == "__main__":
    import uvicorn
    print("Starting RecoverAI REST API server on http://127.0.0.1:8000 ...")
    uvicorn.run("src.api.server:app", host="127.0.0.1", port=8000, reload=False)
