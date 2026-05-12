from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog

from src.db.connection import get_database
from src.models.goal import GoalDoc
from src.models.knowledge_fact import KnowledgeFactDoc

logger = structlog.get_logger()


async def get_active_goals(user_id: str) -> list[GoalDoc]:
    db = get_database()
    now = datetime.utcnow()
    cursor = db["goals"].find(
        {
            "user_id": user_id,
            "valid_from": {"$lte": now},
            "$or": [{"valid_to": None}, {"valid_to": {"$gt": now}}],
        }
    ).sort("priority", 1)
    docs = await cursor.to_list(length=100)
    return [GoalDoc(**d) for d in docs]


async def get_active_knowledge_facts(user_id: str) -> list[KnowledgeFactDoc]:
    db = get_database()
    now = datetime.utcnow()
    cursor = db["knowledge_facts"].find(
        {
            "user_id": user_id,
            "valid_from": {"$lte": now},
            "$or": [{"valid_to": None}, {"valid_to": {"$gt": now}}],
        }
    ).sort("confidence", -1)
    docs = await cursor.to_list(length=50)
    return [KnowledgeFactDoc(**d) for d in docs]


async def get_last_week_adherence(user_id: str) -> dict[str, Any]:
    db = get_database()
    plan = await db["weekly_plans"].find_one(
        {"user_id": user_id, "status": "completed"},
        sort=[("week_start", -1)],
    )
    if not plan:
        return {"planned": 0, "completed": 0, "adherence_pct": 0.0, "week_start": None}

    week_start = plan["week_start"]
    logs = await db["activity_logs"].find(
        {"user_id": user_id, "week_start": week_start}
    ).to_list(length=500)

    planned = sum(len(day.get("blocks", [])) for day in plan.get("day_plans", []))
    completed = sum(1 for log in logs if log.get("completed"))
    adherence = round(completed / planned * 100, 1) if planned > 0 else 0.0

    return {
        "planned": planned,
        "completed": completed,
        "adherence_pct": adherence,
        "week_start": week_start,
    }
