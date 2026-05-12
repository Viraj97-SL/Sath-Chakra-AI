from __future__ import annotations

import os
from typing import Optional

import discord
from discord import app_commands
import structlog

logger = structlog.get_logger()

_USER_ID = "viraj"
_bot: Optional[SathChakraBot] = None


# ── Bot class ──────────────────────────────────────────────────────────────────

class SathChakraBot(discord.Client):
    def __init__(self, owner_id: int) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.owner_id = owner_id

    async def setup_hook(self) -> None:
        _register_commands(self.tree)
        await self.tree.sync()
        logger.info("discord_commands_synced")

    async def on_ready(self) -> None:
        logger.info("discord_bot_ready", user=str(self.user))

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if message.author.id != self.owner_id:
            return
        if message.guild is not None:
            return   # DMs only
        await _route_dm(self, message)


# ── Public helpers ─────────────────────────────────────────────────────────────

async def send_owner_dm(text: str) -> None:
    """Send a DM to the owner. Called from other agents/schedulers."""
    if _bot is None:
        logger.warning("discord_bot_not_running", msg="DM skipped")
        return
    try:
        user = await _bot.fetch_user(_bot.owner_id)
        # Discord message limit is 2000 chars
        for chunk in _chunk(text, 1990):
            await user.send(chunk)
    except Exception as exc:
        logger.warning("discord_dm_failed", error=str(exc))


async def start_bot() -> None:
    """Start the Discord bot. Raises if DISCORD_BOT_TOKEN is not set."""
    global _bot
    token = os.getenv("DISCORD_BOT_TOKEN")
    owner_id_str = os.getenv("DISCORD_OWNER_USER_ID")
    if not token or not owner_id_str:
        logger.info("discord_bot_skipped", reason="DISCORD_BOT_TOKEN or DISCORD_OWNER_USER_ID not set")
        return
    owner_id = int(owner_id_str)
    _bot = SathChakraBot(owner_id=owner_id)
    await _bot.start(token)


# ── Slash commands ─────────────────────────────────────────────────────────────

def _register_commands(tree: app_commands.CommandTree) -> None:

    @tree.command(name="upload", description="Start the weekly schedule upload flow")
    async def upload(interaction: discord.Interaction) -> None:
        if not _is_owner(interaction):
            await interaction.response.send_message("Not authorised.", ephemeral=True)
            return
        from src.memory.short_term import create_session
        await create_session(user_id=_USER_ID)
        await interaction.response.send_message(
            "**Week Planning — Step 1 of 3**\n\n"
            "Send me your shift schedule for next week.\n"
            "You can:\n"
            "• **Screenshot** of your rota / schedule\n"
            "• **Type it**: `Mon 14:00-22:00, Thu 14:00-22:00, Sat 14:00-22:00`\n"
            "• Or say **`no shifts`** if you have no work shifts next week"
        )

    @tree.command(name="today", description="See today's commitments")
    async def today(interaction: discord.Interaction) -> None:
        if not _is_owner(interaction):
            await interaction.response.send_message("Not authorised.", ephemeral=True)
            return
        await interaction.response.send_message(
            "Daily loop starts in Phase 2 — not active yet.\nUse `/upload` to plan next week."
        )

    @tree.command(name="status", description="See this week's adherence")
    async def status(interaction: discord.Interaction) -> None:
        if not _is_owner(interaction):
            await interaction.response.send_message("Not authorised.", ephemeral=True)
            return
        await interaction.response.send_message(
            "Activity tracking starts in Phase 2 — not active yet."
        )

    @tree.command(name="plan", description="See this week's plan summary")
    async def plan(interaction: discord.Interaction) -> None:
        if not _is_owner(interaction):
            await interaction.response.send_message("Not authorised.", ephemeral=True)
            return
        await interaction.response.defer()
        try:
            from src.db.connection import get_database
            db = get_database()
            doc = await db["weekly_plans"].find_one(
                {"user_id": _USER_ID, "status": "active"},
                sort=[("week_start", -1)],
            )
            if not doc:
                await interaction.followup.send("No active weekly plan. Use `/upload` to create one.")
                return
            lines = [f"**Week of {doc['week_start']}**\n"]
            for dp in doc.get("day_plans", []):
                blocks = dp.get("blocks", [])
                if blocks:
                    lines.append(f"**{dp['date']}**")
                    for b in blocks:
                        lines.append(f"  • {b['start_time']}–{b['end_time']} {b['title']}")
                else:
                    lines.append(f"**{dp['date']}** — rest day")
            await interaction.followup.send("\n".join(lines)[:1990])
        except Exception as exc:
            logger.warning("plan_command_failed", error=str(exc))
            await interaction.followup.send("Could not load plan. Try again later.")


# ── DM routing state machine ───────────────────────────────────────────────────

async def _route_dm(bot: SathChakraBot, message: discord.Message) -> None:
    from src.memory.short_term import get_session, update_session, expire_session
    from src.models.agent_session import SessionPhase

    session = await get_session(user_id=_USER_ID)
    if session is None:
        await message.channel.send(
            "No active session. Use `/upload` to start planning your week."
        )
        return

    phase = session.phase

    if phase == SessionPhase.UPLOAD_SHIFT:
        await _handle_shift_input(message)
    elif phase == SessionPhase.UPLOAD_CALENDAR:
        await _handle_other_commitments(message)
    elif phase == SessionPhase.CONFIRM:
        await _handle_confirm(message)
    elif phase == SessionPhase.GENERATING:
        await message.channel.send("⏳ Still generating your plan, hang tight…")
    else:
        await message.channel.send("Session expired. Use `/upload` to restart.")


async def _handle_shift_input(message: discord.Message) -> None:
    from src.memory.short_term import update_session
    from src.models.agent_session import SessionPhase
    from src.services.ingestion import parse_image, parse_text

    text = message.content.strip().lower()

    if message.attachments:
        await message.channel.send("📷 Got your screenshot. Parsing shifts…")
        image_bytes = await message.attachments[0].read()
        result = await parse_image(image_bytes)
    elif text in ("no shifts", "none", "no shift"):
        from src.services.ingestion import RawScheduleInput
        from src.services.ingestion import _next_monday
        result = RawScheduleInput(
            shifts=[], fixed_appointments=[],
            other_commitments="", week_start=_next_monday(), parse_confidence=1.0,
        )
    else:
        result = await parse_text(message.content)

    if result.parse_confidence < 0.5:
        await message.channel.send(
            "⚠️ I couldn't read that clearly. Try typing your shifts like:\n"
            "`Mon 14:00-22:00, Thu 14:00-22:00, Sat 14:00-22:00`\n"
            "or send a clearer screenshot."
        )
        return

    shifts_text = _format_shifts(result.shifts)
    confidence_note = "" if result.parse_confidence >= 0.85 else " _(low confidence — double check)_"

    await update_session(
        user_id=_USER_ID,
        phase=SessionPhase.UPLOAD_CALENDAR,
        context_update={"schedule_input": result.model_dump()},
    )

    await message.channel.send(
        f"✅ Shifts parsed{confidence_note}:\n{shifts_text}\n\n"
        f"**Step 2 of 3** — Any other fixed commitments next week?\n"
        f"(doctor's appointment, gym class, family event…)\n"
        f"Or say **`none`** to continue."
    )


async def _handle_other_commitments(message: discord.Message) -> None:
    from src.memory.short_term import get_session, update_session
    from src.models.agent_session import SessionPhase

    session = await get_session(user_id=_USER_ID)
    if not session:
        return

    other = "" if message.content.strip().lower() in ("none", "no", "nothing") else message.content.strip()
    schedule_input = session.context.get("schedule_input", {})
    schedule_input["other_commitments"] = other

    await update_session(
        user_id=_USER_ID,
        phase=SessionPhase.CONFIRM,
        context_update={"schedule_input": schedule_input},
    )

    shifts_text = _format_shifts(schedule_input.get("shifts", []))
    other_text = f"\n**Other:** {other}" if other else ""
    await message.channel.send(
        f"**Step 3 of 3 — Confirm and generate**\n\n"
        f"**Shifts:** {shifts_text or 'None'}{other_text}\n"
        f"**Week:** {schedule_input.get('week_start', 'next week')}\n\n"
        f"Ready to generate your weekly plan? Reply **`yes`** or **`no`**."
    )


async def _handle_confirm(message: discord.Message) -> None:
    from src.memory.short_term import get_session, update_session, expire_session
    from src.models.agent_session import SessionPhase

    answer = message.content.strip().lower()
    if answer not in ("yes", "y", "go", "ok", "yeah", "yep"):
        if answer in ("no", "n", "cancel", "stop"):
            await expire_session(_USER_ID)
            await message.channel.send("Cancelled. Use `/upload` to start again.")
        else:
            await message.channel.send("Reply **`yes`** to generate or **`no`** to cancel.")
        return

    session = await get_session(user_id=_USER_ID)
    if not session:
        return

    await update_session(user_id=_USER_ID, phase=SessionPhase.GENERATING)
    await message.channel.send("⚙️ Generating your weekly plan… (this takes ~15 seconds)")

    try:
        from src.agents.weekly_planner_agent import run_weekly_planner
        schedule_input = session.context.get("schedule_input", {})
        week_start = schedule_input.get("week_start", "")
        plan_id = await run_weekly_planner(_USER_ID, schedule_input, week_start)
        await expire_session(_USER_ID)
        await message.channel.send(
            f"✅ Done! Plan `{plan_id[:8]}` saved.\nFull plan emailed to you. Check above for the Discord summary."
        )
    except Exception as exc:
        logger.error("weekly_planner_failed", error=str(exc))
        await expire_session(_USER_ID)
        await message.channel.send(
            "❌ Something went wrong generating the plan. Try again with `/upload`."
        )


# ── Utils ──────────────────────────────────────────────────────────────────────

def _is_owner(interaction: discord.Interaction) -> bool:
    owner_id_str = os.getenv("DISCORD_OWNER_USER_ID")
    if not owner_id_str:
        return True   # no restriction if not configured
    return str(interaction.user.id) == owner_id_str


def _format_shifts(shifts: list) -> str:
    if not shifts:
        return "None"
    lines = []
    for s in shifts:
        if isinstance(s, dict):
            lines.append(f"{s.get('day', '?')} {s.get('start_time', '?')}–{s.get('end_time', '?')}")
        else:
            lines.append(f"{s.day} {s.start_time}–{s.end_time}")
    return ", ".join(lines)


def _chunk(text: str, size: int) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)]
