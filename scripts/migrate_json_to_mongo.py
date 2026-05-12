"""
T0.5 — Migrate data/user_history.json to MongoDB.

Idempotent: running twice does not create duplicate records.
Logs: users migrated, snapshots migrated, skipped duplicates.

Usage:
    python -m scripts.migrate_json_to_mongo
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

JSON_PATH = Path("data/user_history.json")
MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB = os.getenv("MONGODB_DB", "sath_chakra")


async def migrate() -> None:
    if not MONGO_URI:
        print("ERROR: MONGODB_URI is not set. Add it to .env and retry.")
        sys.exit(1)

    if not JSON_PATH.exists():
        print(f"ERROR: {JSON_PATH} not found.")
        sys.exit(1)

    with JSON_PATH.open() as f:
        records: list[dict] = json.load(f)

    client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    db = client[MONGO_DB]

    users_created = 0
    snapshots_created = 0
    skipped = 0

    for record in records:
        user_id = record.get("user_id")
        email = record.get("email", "")
        timestamp = record.get("timestamp", "")

        if not user_id:
            skipped += 1
            continue

        # Upsert user document
        user_result = await db["users"].update_one(
            {"user_id": user_id},
            {"$setOnInsert": {"user_id": user_id, "email": email, "created_at": timestamp}},
            upsert=True,
        )
        if user_result.upserted_id:
            users_created += 1

        # Deduplicate snapshots by (user_id, timestamp)
        existing = await db["chakra_snapshots"].find_one(
            {"user_id": user_id, "timestamp": timestamp}
        )
        if existing:
            skipped += 1
            continue

        snapshot = {
            "user_id": user_id,
            "email": email,
            "age": record.get("age"),
            "job_status": record.get("job_status"),
            "current_status": record.get("current_status", {}),
            "ideal_identity": record.get("ideal_identity", {}),
            "language": record.get("language", "sinhala"),
            "timestamp": timestamp,
        }
        await db["chakra_snapshots"].insert_one(snapshot)
        snapshots_created += 1

    client.close()

    print(f"Migration complete:")
    print(f"  Users upserted:     {users_created}")
    print(f"  Snapshots inserted: {snapshots_created}")
    print(f"  Skipped/duplicate:  {skipped}")
    print(f"  Total records read: {len(records)}")


if __name__ == "__main__":
    asyncio.run(migrate())
