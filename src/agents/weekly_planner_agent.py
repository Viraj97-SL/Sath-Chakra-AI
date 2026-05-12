from __future__ import annotations

import json
import os
import time as _time
from datetime import date, datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

import structlog
from langgraph.graph import END, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from src.db.connection import get_database
from src.memory.long_term import get_active_goals, get_active_knowledge_facts, get_last_week_adherence
from src.memory.reasoning_bank import get_top_strategies
from src.models.agent_run import AgentRunDoc
from src.models.weekly_plan import ActivityBlock, DayPlan, WeeklyPlanDoc
from src.services.constraint_solver import ActivityRequest, solve

logger = structlog.get_logger()

_USER_ID = "viraj"
_USER_EMAIL = os.getenv("USER_EMAIL", "amanthabulugahapitiya@gmail.com")


# ── Default activity backlog ───────────────────────────────────────────────────
# Used when goals collection is empty (before seed_goals.py runs)

def _default_activities() -> list[ActivityRequest]:
    return [
        ActivityRequest("g-leetcode", "Leetcode practice", 60, "high", 1, is_deep_work=True, max_per_week=5),
        ActivityRequest("g-ml", "ML/DL theory study", 90, "high", 2, is_deep_work=True, max_per_week=4),
        ActivityRequest("g-project", "Portfolio project work", 120, "high", 3, is_deep_work=True, max_per_week=3),
        ActivityRequest("g-sql", "SQL practice", 45, "medium", 4, max_per_week=3),
        ActivityRequest("g-jobs", "Job applications", 45, "medium", 5, max_per_week=3),
        ActivityRequest("g-reading", "Tech reading / articles", 30, "low", 6, max_per_week=5),
    ]


# ── LangGraph state ────────────────────────────────────────────────────────────

class PlannerState(TypedDict):
    user_id: str
    week_start: str
    schedule_input: dict
    goals: list[dict]
    knowledge_facts: list[dict]
    last_adherence: dict
    top_strategies: list[dict]
    solver_output: dict
    day_plans: list[dict]
    coach_note: str
    plan_id: str
    agent_run_id: str
    error: Optional[str]


# ── Nodes ──────────────────────────────────────────────────────────────────────

async def plan_node(state: PlannerState) -> dict:
    user_id = state["user_id"]
    goals = await get_active_goals(user_id)
    facts = await get_active_knowledge_facts(user_id)
    adherence = await get_last_week_adherence(user_id)
    shift_count = len([s for s in state["schedule_input"].get("shifts", [])])
    sig = f"weekly_plan_{shift_count}shifts"
    strategies = await get_top_strategies(user_id, sig, limit=3)

    return {
        "goals": [g.model_dump(mode="json") for g in goals],
        "knowledge_facts": [f.model_dump(mode="json") for f in facts],
        "last_adherence": adherence,
        "top_strategies": [s.model_dump(mode="json") for s in strategies],
    }


async def solve_node(state: PlannerState) -> dict:
    schedule = state["schedule_input"]
    shifts_raw = schedule.get("shifts", [])

    goals = state["goals"]
    if goals:
        activities = [
            ActivityRequest(
                goal_id=g["goal_id"],
                title=g["title"],
                duration_minutes=60,
                energy_required="high",
                priority=g.get("priority", 5),
                is_deep_work=True,
                max_per_week=3,
            )
            for g in goals[:6]
        ]
    else:
        activities = _default_activities()

    week_start = date.fromisoformat(schedule.get("week_start", date.today().isoformat()))
    output = solve(week_start, shifts_raw, activities)

    # Serialise to dict
    days_dict = []
    for d in output.days:
        days_dict.append({
            "date": d.date.isoformat(),
            "day_of_week": d.day_of_week,
            "is_shift_day": d.is_shift_day,
            "scheduled": [
                {
                    "activity_id": str(uuid4()),
                    "title": s.activity.title,
                    "goal_id": s.activity.goal_id,
                    "start_time": s.slot.start.strftime("%H:%M"),
                    "end_time": s.slot.end.strftime("%H:%M"),
                    "energy_class": s.slot.energy_class,
                    "day_of_week": d.day_of_week,
                    "description": "",
                }
                for s in d.scheduled
            ],
        })

    return {"solver_output": {"days": days_dict}}


async def narrate_node(state: PlannerState) -> dict:
    days = state["solver_output"]["days"]
    adherence = state["last_adherence"]
    facts = state["knowledge_facts"]

    activity_titles = [
        s["title"]
        for d in days
        for s in d["scheduled"]
    ]
    unique_titles = list(dict.fromkeys(activity_titles))

    facts_text = "\n".join(f"- {f['fact_text']}" for f in facts) if facts else "None yet."
    adherence_text = (
        f"{adherence['adherence_pct']}% last week ({adherence['completed']}/{adherence['planned']})"
        if adherence["week_start"] else "First week — no prior data."
    )
    strategies_text = "\n".join(
        f"- {s['strategy_summary']}" for s in state["top_strategies"]
    ) if state["top_strategies"] else "None yet."

    prompt = (
        f"You are a compassionate personal execution coach for a Data Science job seeker "
        f"(Viraj, retail worker, London).\n\n"
        f"Write a 3-sentence 'Coach's Note for the Week'. Tone: warm, direct, no shame language.\n\n"
        f"Context:\n"
        f"- Activities planned: {', '.join(unique_titles)}\n"
        f"- Last week adherence: {adherence_text}\n"
        f"- Known user facts:\n{facts_text}\n"
        f"- Past strategies that worked:\n{strategies_text}\n\n"
        f"Return ONLY the 3-sentence note. No JSON, no headers."
    )

    coach_note = _call_llm(prompt)

    # Add descriptions to scheduled activities
    updated_days = []
    for d in days:
        updated_scheduled = []
        for s in d["scheduled"]:
            desc = f"{s['title']} from {s['start_time']} to {s['end_time']}."
            updated_scheduled.append({**s, "description": desc})
        updated_days.append({**d, "scheduled": updated_scheduled})

    return {"coach_note": coach_note, "solver_output": {"days": updated_days}}


async def deliver_node(state: PlannerState) -> dict:
    db = get_database()
    run_id = str(uuid4())
    plan_id = str(uuid4())
    start_ms = int(_time.time() * 1000)

    # Build WeeklyPlanDoc
    day_plans = []
    for d in state["solver_output"]["days"]:
        blocks = [
            ActivityBlock(
                activity_id=s["activity_id"],
                title=s["title"],
                description=s["description"],
                goal_id=s["goal_id"],
                start_time=s["start_time"],
                end_time=s["end_time"],
                energy_class=s["energy_class"],
                day_of_week=s["day_of_week"],
            )
            for s in d["scheduled"]
        ]
        day_plans.append(DayPlan(
            day_of_week=d["day_of_week"],
            date=d["date"],
            blocks=blocks,
        ))

    plan = WeeklyPlanDoc(
        plan_id=plan_id,
        user_id=state["user_id"],
        week_start=state["week_start"],
        day_plans=day_plans,
        coach_note=state["coach_note"],
        agent_run_id=run_id,
    )
    await db["weekly_plans"].insert_one(plan.model_dump(mode="json"))
    logger.info("weekly_plan_saved", plan_id=plan_id, week_start=state["week_start"])

    # Send email
    try:
        from src.utils.email_service import send_reminder_email
        html = _render_email(plan, state["coach_note"])
        send_reminder_email(_USER_EMAIL, f"Your Week of {state['week_start']} — Sath-Chakra Plan", html)
    except Exception as exc:
        logger.warning("plan_email_failed", error=str(exc))

    # Send Discord DM
    try:
        from src.discord_bot.bot import send_owner_dm
        summary = _render_discord_summary(plan)
        await send_owner_dm(summary)
    except Exception as exc:
        logger.warning("plan_discord_failed", error=str(exc))

    # Audit log
    latency = int(_time.time() * 1000) - start_ms
    run_doc = AgentRunDoc(
        run_id=run_id,
        user_id=state["user_id"],
        agent_name="weekly_planner",
        input_snapshot={"week_start": state["week_start"], "shifts": state["schedule_input"].get("shifts", [])},
        output_snapshot={"plan_id": plan_id},
        latency_ms=latency,
        status="success",
        completed_at=datetime.utcnow(),
    )
    await db["agent_runs"].insert_one(run_doc.model_dump(mode="json"))

    return {"plan_id": plan_id, "agent_run_id": run_id}


# ── LLM helper ─────────────────────────────────────────────────────────────────

def _call_llm(prompt: str) -> str:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage

    for llm in [
        lambda: ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.6, google_api_key=os.getenv("GOOGLE_API_KEY")),
        lambda: ChatGroq(model="llama-3.3-70b-versatile", temperature=0.6, groq_api_key=os.getenv("GROQ_API_KEY")),
    ]:
        try:
            return llm().invoke([HumanMessage(content=prompt)]).content
        except Exception as exc:
            logger.warning("llm_call_failed", error=str(exc))
    return "This week, focus on what you can control. Progress over perfection. You've got this."


# ── Renderers ──────────────────────────────────────────────────────────────────

def _render_email(plan: WeeklyPlanDoc, coach_note: str) -> str:
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    rows = ""
    for dp in plan.day_plans:
        if not dp.blocks:
            rows += f"""
            <tr>
              <td style="padding:8px 12px;color:#6b7280;font-family:monospace;">{dp.date}</td>
              <td style="padding:8px 12px;color:#4b5563;">Rest / recovery day</td>
            </tr>"""
            continue
        for b in dp.blocks:
            rows += f"""
            <tr>
              <td style="padding:8px 12px;color:#10b981;font-family:'JetBrains Mono',monospace;font-size:13px;">
                {dp.date}<br><span style="color:#6b7280;font-size:11px;">{b.start_time}–{b.end_time}</span>
              </td>
              <td style="padding:8px 12px;color:#e5e7eb;">{b.title}</td>
            </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0d1117;font-family:sans-serif;">
  <div style="max-width:600px;margin:0 auto;padding:24px;">
    <h1 style="color:#10b981;font-size:20px;margin:0 0 4px;">Sath-Chakra — Week of {plan.week_start}</h1>
    <p style="color:#6b7280;font-size:13px;margin:0 0 24px;">Your execution plan is ready.</p>

    <div style="background:#161b22;border:1px solid #21262d;border-radius:8px;padding:16px;margin-bottom:20px;">
      <p style="color:#10b981;font-size:12px;font-weight:bold;margin:0 0 8px;text-transform:uppercase;">Coach's Note</p>
      <p style="color:#e5e7eb;font-size:14px;line-height:1.6;margin:0;">{coach_note}</p>
    </div>

    <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;background:#161b22;border:1px solid #21262d;border-radius:8px;overflow:hidden;">
      <thead>
        <tr style="background:#10b981;">
          <th style="padding:10px 12px;text-align:left;color:#0d1117;font-size:12px;font-weight:bold;">DATE / TIME</th>
          <th style="padding:10px 12px;text-align:left;color:#0d1117;font-size:12px;font-weight:bold;">ACTIVITY</th>
        </tr>
      </thead>
      <tbody>{rows}
      </tbody>
    </table>

    <p style="color:#374151;font-size:11px;margin:20px 0 0;text-align:center;">
      Sath-Chakra AI · Personal Execution Companion
    </p>
  </div>
</body>
</html>"""


def _render_discord_summary(plan: WeeklyPlanDoc) -> str:
    lines = [f"**Week of {plan.week_start} — Your Plan**\n"]

    top_titles: list[str] = []
    for dp in plan.day_plans:
        for b in dp.blocks:
            if b.title not in top_titles:
                top_titles.append(b.title)
            if len(top_titles) >= 3:
                break
        if len(top_titles) >= 3:
            break

    if top_titles:
        lines.append("**Top priorities this week:**")
        for i, t in enumerate(top_titles, 1):
            lines.append(f"{i}. {t}")
        lines.append("")

    lines.append("**Daily breakdown:**")
    for dp in plan.day_plans:
        count = len(dp.blocks)
        status = f"{count} commitment{'s' if count != 1 else ''}" if count else "Rest day"
        lines.append(f"• {dp.date}: {status}")

    lines.append(f"\n_{plan.coach_note}_")
    lines.append(f"\nFull plan emailed ✉️")
    return "\n".join(lines)


# ── Compile graph ──────────────────────────────────────────────────────────────

_wf = StateGraph(PlannerState)
_wf.add_node("plan", plan_node)
_wf.add_node("solve", solve_node)
_wf.add_node("narrate", narrate_node)
_wf.add_node("deliver", deliver_node)
_wf.set_entry_point("plan")
_wf.add_edge("plan", "solve")
_wf.add_edge("solve", "narrate")
_wf.add_edge("narrate", "deliver")
_wf.add_edge("deliver", END)

weekly_planner = _wf.compile()


async def run_weekly_planner(user_id: str, schedule_input: dict, week_start: str) -> str:
    """Entry point called from Discord bot and scheduler."""
    run_id = str(uuid4())
    initial: PlannerState = {
        "user_id": user_id,
        "week_start": week_start,
        "schedule_input": schedule_input,
        "goals": [],
        "knowledge_facts": [],
        "last_adherence": {},
        "top_strategies": [],
        "solver_output": {},
        "day_plans": [],
        "coach_note": "",
        "plan_id": "",
        "agent_run_id": run_id,
        "error": None,
    }
    result = await weekly_planner.ainvoke(initial)
    return result.get("plan_id", "")
