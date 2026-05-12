from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import structlog

from src.db.connection import get_database
from src.models.agent_session import AgentSessionDoc, SessionPhase

logger = structlog.get_logger()

_DEFAULT_USER = "viraj"


async def get_session(user_id: str = _DEFAULT_USER) -> AgentSessionDoc | None:
    db = get_database()
    doc = await db["agent_sessions"].find_one(
        {"user_id": user_id, "phase": {"$nin": [SessionPhase.EXPIRED.value, SessionPhase.COMPLETE.value]}}
    )
    if not doc:
        return None
    if doc.get("expires_at") and doc["expires_at"] < datetime.utcnow():
        await expire_session(user_id)
        return None
    return AgentSessionDoc(**doc)


async def create_session(user_id: str = _DEFAULT_USER) -> AgentSessionDoc:
    await expire_session(user_id)
    session = AgentSessionDoc(user_id=user_id, phase=SessionPhase.UPLOAD_SHIFT)
    db = get_database()
    await db["agent_sessions"].insert_one(session.model_dump())
    logger.info("session_created", user_id=user_id, session_id=session.session_id)
    return session


async def update_session(
    user_id: str,
    phase: SessionPhase,
    context_update: dict[str, Any] | None = None,
) -> None:
    db = get_database()
    set_fields: dict[str, Any] = {
        "phase": phase.value,
        "updated_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=30),
    }
    if context_update:
        for k, v in context_update.items():
            set_fields[f"context.{k}"] = v
    await db["agent_sessions"].update_one({"user_id": user_id}, {"$set": set_fields})
    logger.info("session_updated", user_id=user_id, phase=phase.value)


async def expire_session(user_id: str = _DEFAULT_USER) -> None:
    db = get_database()
    await db["agent_sessions"].update_many(
        {"user_id": user_id},
        {"$set": {"phase": SessionPhase.EXPIRED.value}},
    )
