from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

import structlog
from src.db.connection import ping_database

logger = structlog.get_logger()


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/healthz")
    async def liveness():
        return {"status": "ok"}

    @router.get("/readyz")
    async def readiness():
        connected = await ping_database()
        if connected:
            return {"status": "ready", "mongo": "connected"}
        logger.warning("readiness_check_failed")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "mongo": "disconnected"},
        )

    return router
