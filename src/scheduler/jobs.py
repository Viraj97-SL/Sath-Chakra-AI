from __future__ import annotations

import os

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = structlog.get_logger()

_scheduler: AsyncIOScheduler | None = None
_TZ = os.getenv("TIMEZONE", "Europe/London")


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone=_TZ)
    return _scheduler


def start_scheduler() -> None:
    scheduler = get_scheduler()

    # Sunday 18:00 — nudge to upload schedule
    scheduler.add_job(
        _sunday_nudge,
        CronTrigger(day_of_week="sun", hour=18, minute=0, timezone=_TZ),
        id="sunday_nudge",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Nightly 02:00 — reasoning bank decay
    scheduler.add_job(
        _nightly_decay,
        CronTrigger(hour=2, minute=0, timezone=_TZ),
        id="nightly_decay",
        replace_existing=True,
        misfire_grace_time=600,
    )

    scheduler.start()
    logger.info("scheduler_started", jobs=len(scheduler.get_jobs()))


def stop_scheduler() -> None:
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")


async def _sunday_nudge() -> None:
    from src.discord_bot.bot import send_owner_dm
    msg = (
        "**Sunday planning time 📋**\n\n"
        "Ready to set up next week? Send me your shift screenshot or type your schedule.\n"
        "Use `/upload` to start."
    )
    await send_owner_dm(msg)
    logger.info("sunday_nudge_sent")


async def _nightly_decay() -> None:
    from src.memory.reasoning_bank import run_nightly_decay
    await run_nightly_decay(user_id="viraj")
