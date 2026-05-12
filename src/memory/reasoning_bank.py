from __future__ import annotations

from datetime import datetime

import structlog

from src.db.connection import get_database
from src.models.reasoning_entry import ReasoningEntryDoc

logger = structlog.get_logger()

_DECAY_FACTOR = 0.98
_BOOST_FACTOR = 1.05
_PRUNE_FLOOR = 0.30


async def get_top_strategies(
    user_id: str,
    task_signature: str,
    limit: int = 3,
) -> list[ReasoningEntryDoc]:
    db = get_database()
    cursor = db["reasoning_entries"].find(
        {"user_id": user_id, "task_signature": task_signature}
    ).sort("decay_score", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [ReasoningEntryDoc(**d) for d in docs]


async def store_strategy(entry: ReasoningEntryDoc) -> None:
    db = get_database()
    await db["reasoning_entries"].insert_one(entry.model_dump())
    logger.info("strategy_stored", entry_id=entry.entry_id, signature=entry.task_signature)


async def boost_strategy(entry_id: str) -> None:
    db = get_database()
    await db["reasoning_entries"].update_one(
        {"entry_id": entry_id},
        {
            "$mul": {"decay_score": _BOOST_FACTOR},
            "$set": {"last_used_at": datetime.utcnow()},
            "$inc": {"use_count": 1},
        },
    )
    # Cap at 1.0
    await db["reasoning_entries"].update_one(
        {"entry_id": entry_id, "decay_score": {"$gt": 1.0}},
        {"$set": {"decay_score": 1.0}},
    )


async def run_nightly_decay(user_id: str) -> None:
    db = get_database()
    await db["reasoning_entries"].update_many(
        {"user_id": user_id},
        {"$mul": {"decay_score": _DECAY_FACTOR}},
    )
    result = await db["reasoning_entries"].delete_many(
        {"user_id": user_id, "decay_score": {"$lt": _PRUNE_FLOOR}},
    )
    logger.info("nightly_decay_done", user_id=user_id, pruned=result.deleted_count)
