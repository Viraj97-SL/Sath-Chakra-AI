from __future__ import annotations

import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

logger = structlog.get_logger()


async def create_all_indexes(db: AsyncIOMotorDatabase) -> None:
    """Idempotently create all MongoDB indexes for Sath-Chakra AI v2."""

    await db["users"].create_indexes([
        IndexModel([("user_id", ASCENDING)], unique=True, name="users_user_id_unique"),
    ])

    await db["goals"].create_indexes([
        IndexModel([("user_id", ASCENDING), ("level", ASCENDING)], name="goals_user_level"),
        IndexModel([("user_id", ASCENDING), ("valid_to", ASCENDING)], name="goals_user_valid_to"),
    ])

    await db["weekly_plans"].create_indexes([
        IndexModel(
            [("user_id", ASCENDING), ("week_start", ASCENDING)],
            unique=True,
            name="weekly_plans_user_week_unique",
        ),
    ])

    await db["daily_plans"].create_indexes([
        IndexModel([("user_id", ASCENDING), ("date", ASCENDING)], name="daily_plans_user_date"),
    ])

    await db["activity_logs"].create_indexes([
        IndexModel([("user_id", ASCENDING), ("date", ASCENDING)], name="activity_logs_user_date"),
        IndexModel([("user_id", ASCENDING), ("daily_plan_id", ASCENDING)], name="activity_logs_user_plan"),
    ])

    await db["agent_sessions"].create_indexes([
        IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="agent_sessions_ttl"),
        IndexModel([("user_id", ASCENDING)], name="agent_sessions_user"),
    ])

    await db["reasoning_entries"].create_indexes([
        IndexModel([("user_id", ASCENDING), ("task_signature", ASCENDING)], name="reasoning_user_sig"),
        IndexModel([("decay_score", DESCENDING)], name="reasoning_decay_score"),
    ])

    await db["knowledge_facts"].create_indexes([
        IndexModel([("user_id", ASCENDING), ("valid_to", ASCENDING)], name="knowledge_facts_user_valid_to"),
    ])

    await db["agent_runs"].create_indexes([
        IndexModel(
            [("user_id", ASCENDING), ("agent_name", ASCENDING), ("created_at", DESCENDING)],
            name="agent_runs_user_agent_time",
        ),
    ])

    await db["inbound_messages"].create_indexes([
        IndexModel([("user_id", ASCENDING), ("processed", ASCENDING)], name="inbound_messages_user_processed"),
    ])

    logger.info("mongo_indexes_created")
