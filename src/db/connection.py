from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = structlog.get_logger()

_client: AsyncIOMotorClient | None = None


def _get_client() -> AsyncIOMotorClient:
    """Return the motor client, raising if not yet initialized."""
    if _client is None:
        raise RuntimeError("MongoDB client not initialized. Call db_lifespan first.")
    return _client


def get_database() -> AsyncIOMotorDatabase:
    """Return the motor database instance."""
    db_name = os.getenv("MONGODB_DB", "sath_chakra")
    return _get_client()[db_name]


async def ping_database() -> bool:
    """Ping MongoDB and return True if reachable."""
    try:
        await _get_client().admin.command("ping")
        return True
    except Exception as exc:
        logger.warning("mongo_ping_failed", error=str(exc))
        return False


@asynccontextmanager
async def db_lifespan(_app=None) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context manager for the MongoDB connection."""
    global _client

    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI environment variable is not set.")

    db_name = os.getenv("MONGODB_DB", "sath_chakra")

    _client = AsyncIOMotorClient(
        uri,
        minPoolSize=2,
        maxPoolSize=10,
        serverSelectionTimeoutMS=5000,
    )

    try:
        await _client.admin.command("ping")
        logger.info("mongo_connected", database=db_name)
    except Exception as exc:
        _client.close()
        _client = None
        raise RuntimeError(f"MongoDB connection failed: {exc}") from exc

    try:
        yield
    finally:
        if _client is not None:
            _client.close()
            _client = None
            logger.info("mongo_disconnected")
