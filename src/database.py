from __future__ import annotations

import json
import os
from datetime import datetime

import structlog

logger = structlog.get_logger()

_LEGACY_JSON_PATH = "data/user_history.json"


async def save_user_snapshot(user_data: dict) -> str:
    """
    Save a Wheel of Life snapshot to MongoDB (or JSON fallback if Mongo unavailable).
    Must be awaited — called from the async FastAPI route.
    """
    user_data = {**user_data, "timestamp": datetime.utcnow().isoformat()}

    if await _try_save_to_mongo(user_data):
        return "Snapshot saved to MongoDB."

    _save_to_json_fallback(user_data)
    return "Snapshot saved to JSON (MongoDB not configured)."


async def _try_save_to_mongo(user_data: dict) -> bool:
    """Return True if save to Mongo succeeded, False otherwise."""
    try:
        from src.db.connection import get_database

        db = get_database()
        snapshot = {
            "user_id": user_data.get("user_id"),
            "email": user_data.get("email", ""),
            "age": user_data.get("age"),
            "job_status": user_data.get("job_status"),
            "current_status": user_data.get("current_status", {}),
            "ideal_identity": user_data.get("ideal_identity", {}),
            "language": user_data.get("language", "sinhala"),
            "timestamp": user_data["timestamp"],
        }
        await db["chakra_snapshots"].insert_one(snapshot)
        logger.info("snapshot_saved_mongo", user_id=user_data.get("user_id"))
        return True

    except RuntimeError:
        # Motor client not initialised yet
        return False
    except Exception as exc:
        logger.warning("mongo_snapshot_failed", error=str(exc))
        return False


def _save_to_json_fallback(user_data: dict) -> None:
    os.makedirs(os.path.dirname(_LEGACY_JSON_PATH), exist_ok=True)

    history: list = []
    if os.path.exists(_LEGACY_JSON_PATH):
        with open(_LEGACY_JSON_PATH, "r") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []

    history.append(user_data)

    with open(_LEGACY_JSON_PATH, "w") as f:
        json.dump(history, f, indent=4)

    logger.info("snapshot_saved_json_fallback", user_id=user_data.get("user_id"))
