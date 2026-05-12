"""
T1.4 — Seed Viraj's goal hierarchy into MongoDB.
Idempotent: skips goals that already exist (matched by title + user_id).

Usage:
    python -m scripts.seed_goals
"""
from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()


GOALS = [
    # ── Final goal ──────────────────────────────────────────────────────────
    {
        "title": "Get Data Scientist role + financial stability",
        "description": "Land a Data Science role (remote or London) and build financial runway.",
        "level": "final",
        "parent": None,
        "priority": 1,
    },
    # ── Quarterly Q1 2026 ───────────────────────────────────────────────────
    {
        "title": "Complete ML fundamentals + build 2 portfolio projects",
        "description": "Solid ML theory + two end-to-end projects on GitHub.",
        "level": "quarterly",
        "parent": "Get Data Scientist role + financial stability",
        "priority": 1,
    },
    # ── Monthly Jan ─────────────────────────────────────────────────────────
    {
        "title": "Finish Andrew Ng ML course + 50 Leetcode problems",
        "description": "Core ML theory locked in. Algorithmic fluency baseline.",
        "level": "monthly",
        "parent": "Complete ML fundamentals + build 2 portfolio projects",
        "priority": 1,
    },
    # ── Monthly Feb ─────────────────────────────────────────────────────────
    {
        "title": "Build end-to-end ML project (tabular prediction)",
        "description": "Full pipeline: EDA → model → evaluation → deployed demo.",
        "level": "monthly",
        "parent": "Complete ML fundamentals + build 2 portfolio projects",
        "priority": 2,
    },
    # ── Monthly Mar ─────────────────────────────────────────────────────────
    {
        "title": "Complete SQL advanced course + start applying",
        "description": "Advanced SQL + window functions. Send first 10 applications.",
        "level": "monthly",
        "parent": "Complete ML fundamentals + build 2 portfolio projects",
        "priority": 3,
    },
    # ── Quarterly Q2 2026 ───────────────────────────────────────────────────
    {
        "title": "Active job applications + DS internship/role",
        "description": "30+ applications sent, 2+ technical interviews, 1 offer.",
        "level": "quarterly",
        "parent": "Get Data Scientist role + financial stability",
        "priority": 2,
    },
    # ── Monthly Apr ─────────────────────────────────────────────────────────
    {
        "title": "Send 30 applications + improve portfolio",
        "description": "Quantity + quality of outreach. Portfolio polished for recruiters.",
        "level": "monthly",
        "parent": "Active job applications + DS internship/role",
        "priority": 1,
    },
    # ── Monthly May ─────────────────────────────────────────────────────────
    {
        "title": "2 technical interviews + revise CV",
        "description": "Interview practice, CV updated with project metrics.",
        "level": "monthly",
        "parent": "Active job applications + DS internship/role",
        "priority": 2,
    },
]


async def seed() -> None:
    from motor.motor_asyncio import AsyncIOMotorClient
    from datetime import datetime
    from uuid import uuid4

    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB", "sath_chakra")
    if not uri:
        print("ERROR: MONGODB_URI not set.")
        sys.exit(1)

    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=10000)
    db = client[db_name]

    created = 0
    skipped = 0
    title_to_id: dict[str, str] = {}

    for goal in GOALS:
        existing = await db["goals"].find_one({"user_id": "viraj", "title": goal["title"]})
        if existing:
            title_to_id[goal["title"]] = str(existing["goal_id"])
            skipped += 1
            continue

        goal_id = str(uuid4())
        parent_id = title_to_id.get(goal["parent"]) if goal["parent"] else None

        doc = {
            "goal_id": goal_id,
            "user_id": "viraj",
            "title": goal["title"],
            "description": goal["description"],
            "level": goal["level"],
            "parent_goal_id": parent_id,
            "priority": goal["priority"],
            "valid_from": datetime.utcnow(),
            "valid_to": None,
            "created_at": datetime.utcnow(),
        }
        await db["goals"].insert_one(doc)
        title_to_id[goal["title"]] = goal_id
        created += 1

    client.close()
    print(f"Goals seeded: {created} created, {skipped} already existed.")


if __name__ == "__main__":
    asyncio.run(seed())
