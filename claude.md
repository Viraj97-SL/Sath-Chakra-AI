You're right — I shipped half the brief. Here's the complete version with all phases and the overall framing Claude Code needs to hold the whole project in its head, not just the next ticket.

# Sath-Chakra AI v2 — Complete Upgrade Brief for Claude Code

This document is the full hand-off. It has three parts: **(1) The North Star** Claude Code re-reads at the start of every session so it doesn't drift, **(2) All five phases** with tickets and acceptance criteria, **(3) Operating rules** for how you and Claude Code work together.

---

# PART 1 — The North Star (Pin This in Every Claude Code Session)

## 1.1 What This Project Is

We are upgrading the existing repo `Viraj97-SL/Sath-Chakra-AI`. It is currently deployed on Railway (FastAPI backend) and Vercel (React frontend). It currently does **one thing**: a user fills in the Wheel of Life form, gets a one-shot strategic 2026 roadmap, an identity card PNG, and an ICS calendar file. That's it. After they receive the artifacts, the system has nothing more to say.

The upgrade transforms this from a **one-shot strategic generator** into a **closed-loop personal execution companion**. The existing one-shot flow becomes the *strategic layer* of a four-loop architecture. We add weekly planning, daily Telegram reminders, end-of-day reflection capture, weekly plan-vs-actual review, three-layer memory, and an adherence-learning reasoning bank.

## 1.2 The Four-Loop Model (Memorize This)

Every feature belongs to exactly one loop. If a feature doesn't fit one of these, it doesn't get built.

| Loop | Cadence | Trigger | Output | Phase introduced |
|---|---|---|---|---|
| **Strategic** | Quarterly / on-demand | User fills Wheel of Life (existing UI) | 2026 roadmap, identity card, goal hierarchy | Already exists |
| **Tactical** | Weekly (Sunday eve) | User uploads schedule via Telegram | Constraint-respecting weekly plan, emailed | Phase 1 |
| **Operational** | Daily | Cron 7am + 9pm | Morning brief, evening reflection prompt | Phase 2 |
| **Reactive** | In-day | User chat events | Plan deltas, acknowledgements | Phase 2/4 |

## 1.3 The Three-Layer Memory (Same Pattern as Phantom Trade)

The user (Viraj) has built this pattern before in a separate repo. We're porting and adapting it. The three layers are:

- **Short-term memory** — TTL 24h, MongoDB. Conversation state, pending confirmations, current plan being executed, phase tracking.
- **Long-term memory** — bi-temporal (`valid_from`, `valid_to`). Goals (final/quarterly/monthly), knowledge facts about the user (e.g. "skips Leetcode after late shifts"), schedule snapshots.
- **Reasoning bank** — decay-scored strategies with similarity embeddings. Stores planning approaches that worked. Retrieved at PLAN time. Decayed nightly. Boosted on use. This is what makes the system *visibly improve over weeks*.

## 1.4 Hard Architectural Constraints

These are non-negotiable. Any ticket that violates them is wrong, regardless of what the ticket says.

1. **Existing `/analyze-chakra` endpoint and existing React frontend keep working unchanged.** Both are in production. After every commit, manually verifying the existing flow still produces the same artifacts is mandatory regression check.
2. **Migrate, don't replace.** `data/user_history.json` has 50+ real records. They get migrated, not deleted.
3. **Reuse existing assets.** The LangGraph `chakra_agent.py` workflow, `email_service.py`, `chakra_schema.py`, `visualizer.py` Playwright pipeline, the Vercel React UI — all stay. We extend, we don't rewrite.
4. **Single user (Viraj) for now.** Hardcoded `TELEGRAM_OWNER_CHAT_ID` is the user identifier through Phase 4. Multi-tenant comes in Phase 5 or never.
5. **Constraint solver before LLM.** Time arithmetic (sleep, shifts, commute, cooking) is deterministic Python. The LLM only writes human-readable descriptions and handles soft preferences. The LLM never does arithmetic on time budgets.
6. **Structured outputs everywhere.** Every LLM call returns Pydantic-validated JSON via structured-output mode. No regex parsing of free-form text. Retries with exponential backoff. Fallback chain: Gemini Flash → Gemini Pro → Groq Llama 70B.
7. **Idempotent scheduled jobs.** Job IDs derived from `(user_id, date, job_type)`. Railway restart must not double-fire morning brief.
8. **Audit trail.** Every agent run writes to `agent_runs` collection — input, output, latency, cost. This is debug surface and reasoning-bank training data.
9. **Quiet hours**: no Telegram messages between 22:30 and 06:30 unless user-initiated.
10. **Compassion is non-optional.** The Realigner agent's tone matters as much as its logic. After a missed day, the system never says "you're behind." It says something like: "Yesterday didn't unfold as planned. That's data, not a verdict."

## 1.5 The Five Phases at a Glance

| Phase | Name | Duration | What user gets at end |
|---|---|---|---|
| **0** | Plumbing & Migration | 2–3 days | Mongo replaces JSON, no behavior change yet |
| **1** | Sunday Loop | ~1 week | Sunday upload → weekly plan emailed + Telegram summary |
| **2** | Daily Loop | ~1 week | 7am brief + 9pm reflection capture, plan-vs-actual logging |
| **3** | Weekly Review + Memory | ~1 week | Saturday review email with adherence patterns; reasoning bank wired |
| **4** | Intelligence & Realigner | ~1–2 weeks | Adaptive plans, missed-day recovery, mood/energy tagging, knowledge fact extraction |
| **5** | Polish & Portfolio | ~1 week | Web dashboard, public write-up, optional WhatsApp |

The user lives with each phase for 2–3 weeks before moving on. Building is the easy part; using it long enough to surface real bugs is the hard part.

---

# PART 2 — All Phases

## Phase 0 — Plumbing & Migration

**Goal**: replace JSON with MongoDB, set up new project structure, migrate existing data. Zero new user-visible behavior.

### Tickets

**T0.1 — Repo restructure**
- New top-level packages alongside existing: `src/db/`, `src/memory/`, `src/agents/`, `src/scheduler/`, `src/telegram_bot/`, `src/services/`, `src/templates/`
- Existing `src/agents/chakra_agent.py` stays — rename mentally as the *Strategist* (handles the Strategic Loop only)
- Update `requirements.txt`: add `motor`, `python-telegram-bot>=21`, `apscheduler`, `structlog`. Pin versions.

**T0.2 — MongoDB connection layer**
- `src/db/connection.py` — async motor client, connection pool, ping health check, FastAPI lifespan integration
- Mirror the pattern from Phantom Trade's `db/connection.py`

**T0.3 — Pydantic schemas for new collections**
- New files in `src/models/`: `user.py`, `goal.py`, `weekly_plan.py`, `daily_plan.py`, `activity_log.py`, `reflection.py`, `agent_session.py`, `knowledge_fact.py`, `reasoning_entry.py`, `agent_run.py`, `inbound_message.py`, `weekly_insight.py`
- Bi-temporal fields on `goal` and `knowledge_fact`
- Existing `chakra_schema.py` untouched

**T0.4 — MongoDB indexes**
- `src/db/indexes.py` — programmatic, idempotent index creation
- Cover all known query patterns; TTL on `agent_sessions.expires_at`

**T0.5 — JSON-to-Mongo migration script**
- `scripts/migrate_json_to_mongo.py`
- Reads `data/user_history.json`, deduplicates, creates `users` and `chakra_snapshots` records
- Idempotent — running twice doesn't duplicate
- Logs: users migrated, snapshots migrated, skipped duplicates

**T0.6 — Refactor `/analyze-chakra` to write to Mongo**
- Public behavior unchanged
- Internal: `database.py:save_user_snapshot` now writes to Mongo
- Old JSON file becomes read-only backup

**T0.7 — Structured logging**
- Replace `print()` with `structlog` throughout. JSON in production, pretty in dev.

**T0.8 — Health endpoints**
- `/healthz` (alive) and `/readyz` (Mongo ping)

### Phase 0 Acceptance Criteria
- Existing endpoint produces identical output to pre-upgrade
- Mongo collections created with all indexes
- All existing JSON records visible in Mongo
- Railway deploy works; logs show successful Mongo connection
- Zero new public endpoints

---

## Phase 1 — Sunday Loop (Tactical)

**Goal**: user uploads Sunday inputs via Telegram → receives validated weekly plan via email and Telegram summary.

### Tickets

**T1.1 — Telegram bot scaffolding**
- `src/telegram_bot/bot.py` — python-telegram-bot v21+, polling mode, runs as asyncio task in FastAPI lifespan
- Owner-only filter via `TELEGRAM_OWNER_CHAT_ID`
- Commands: `/start`, `/help`, `/plan`, `/upload`, `/today` (placeholder), `/status` (placeholder)
- All inbound logged to `inbound_messages`

**T1.2 — Schedule ingestion service**
- `src/services/ingestion.py`
- Accepts photo, document (xlsx/csv), or text
- For images: Gemini 2.5 Flash with vision + structured JSON output → shifts, commute, fixed appointments
- For xlsx/csv: pandas + heuristic column mapper (handle the user's existing UPSkill sheet format)
- Output: validated `RawScheduleInput` Pydantic model with per-field confidence
- Low-confidence triggers Telegram confirmation message

**T1.3 — Three-layer memory modules**
- `src/memory/short_term.py`, `long_term.py`, `reasoning_bank.py`
- Port the pattern from Phantom Trade. The user can paste those files into Claude Code as reference.

**T1.4 — Goal hierarchy seeding**
- `scripts/seed_goals.py` — one-time, populates the user's goal tree
- Final goal: "Get Data Scientist role + financial stability"
- Quarterly milestones, monthly milestones, pulled from existing UPSkill sheet activity list
- Bi-temporal: all `valid_from = now`, `valid_to = null`

**T1.5 — Constraint solver**
- `src/services/constraint_solver.py` — pure Python, no LLM
- Inputs: `RawScheduleInput`, fixed daily blocks (sleep, cooking, buffer), goal-derived activity backlog
- Outputs: per-day available slots with `start_time`, `end_time`, `energy_class` (heuristic: morning + post-commute = high; late evening = low)
- Greedy assignment by priority and energy match
- Hard rules: no two deep-work blocks back-to-back; mandatory rest day if previous week had >5 working days; max 3 commitments per day
- Unit-testable in isolation, no external deps

**T1.6 — Weekly Planner Agent**
- `src/agents/weekly_planner_agent.py` — LangGraph subgraph: PLAN → SOLVE → NARRATE → DELIVER
- PLAN: load goals, last week's adherence (empty week 1), top reasoning-bank strategies
- SOLVE: call constraint solver
- NARRATE: LLM writes activity descriptions and 3-sentence "Coach's note for the week" — Pydantic-validated
- DELIVER: write `WeeklyPlan` to Mongo, render HTML email, send via existing `email_service.py`, send Telegram summary

**T1.7 — Email template**
- `src/templates/weekly_plan_email.html` — calendar-style, mobile-friendly, no inline JS
- Reuse existing Sath-Chakra cyber-audit aesthetic (emerald, dark, monospace for time blocks)

**T1.8 — Telegram weekly summary**
- Compact: top 3 priorities, daily time-budget summary, "Full plan emailed ✉️"
- Markdown-safe escaping

**T1.9 — Conversational upload flow**
- `/upload` → ask shift screenshot → confirm parse → ask calendar screenshot → confirm → ask other commitments as text → "ready to generate? [Yes/No]" → on yes, fire planner agent
- State stored in short-term memory session
- 30-min inactivity timeout

**T1.10 — Sunday nudge job**
- APScheduler: every Sunday 18:00 → "Ready to plan next week? Send /upload."
- Idempotent

### Phase 1 Acceptance Criteria
- Shift screenshot → structured shifts within 15s
- Generated plan respects all hard constraints (no activity during shift/sleep/commute)
- Email arrives within 30s, renders on mobile
- Telegram summary arrives same time
- `WeeklyPlan` written to Mongo with full provenance
- Existing `/analyze-chakra` still works
- Sunday 18:00 nudge fires reliably

---

## Phase 2 — Daily Loop (Operational + Reactive)

**Goal**: morning brief, evening reflection, plan-vs-actual logging. The system now has eyes on what actually happens.

### Tickets

**T2.1 — Daily Planner Agent**
- `src/agents/daily_planner_agent.py` — LangGraph subgraph
- Triggered by APScheduler at user-configured morning time (default 7am London)
- PLAN: load weekly plan + yesterday's reflection + today's date
- ACT: select today's commitments (max 3), adjust if yesterday was 0/3 (scale down) or 3/3 (hold the line)
- OBSERVE: tone check, length check
- REACT: send Telegram message with "Today's commitments: [list]. Reply 'go' to confirm or 'edit' to adjust."

**T2.2 — Reflector Agent**
- `src/agents/reflector_agent.py`
- Triggered nightly at user-configured evening time (default 9pm)
- Sends prompt: "How did today go? Free-text reply works."
- Parses free-text reply via Gemini Flash with structured output → maps to scheduled activity IDs → writes `activity_logs`
- Asks max one follow-up if ambiguous
- Updates short-term memory phase to `COMPLETE`

**T2.3 — In-day chat handler**
- `src/telegram_bot/handlers.py`
- Routes inbound messages by intent (LLM-classified): completion update, reschedule request, status query, free chat
- For "did Leetcode for an hour", "skipped reading" — updates `activity_logs` immediately
- For "move project work to tomorrow" — creates a `daily_plan` delta, confirms back

**T2.4 — `/today` and `/status` commands**
- `/today` → returns today's commitments and current completion status
- `/status` → returns this week's adherence so far ("3/12 done, on track for 67%")

**T2.5 — Quiet hours enforcement**
- All outbound message functions check `QUIET_HOURS_START`/`END`
- Queued messages held until window opens (or dropped if non-critical)

**T2.6 — Activity log analytics view**
- Internal API endpoint `/api/v2/adherence/{week_start}` (auth: hardcoded API key for now)
- Returns: total planned, total completed, by-category breakdown, by-day breakdown
- Used internally; no UI yet

### Phase 2 Acceptance Criteria
- 7am brief arrives daily, content reflects yesterday's reflection
- 9pm reflection prompt arrives, free-text replies parsed correctly into `activity_logs`
- In-day "did X" message updates activity log within 5s
- Quiet hours respected — no messages 22:30–06:30
- `/today` and `/status` return accurate data
- Lived with for 2 weeks before Phase 3 starts

---

## Phase 3 — Weekly Review + Memory Wiring

**Goal**: the system starts learning. Adherence patterns surfaced. Reasoning bank populated.

### Tickets

**T3.1 — Weekly Review Agent**
- `src/agents/weekly_review_agent.py` — runs every Saturday morning at 9am
- PLAN: load full week's `activity_logs` + `daily_plans` + `weekly_plan`
- ACT: compute metrics (adherence %, by day, by category, by energy class), detect patterns ("Wed evenings are consistently broken — correlates with retail shifts"), identify systemic over-commitment (planned 90 min but typically takes 60)
- OBSERVE: confidence in pattern detection
- REACT: write `WeeklyInsight` doc, generate insight email, send Telegram summary, update reasoning bank with strategy entries

**T3.2 — Insight email template**
- `src/templates/weekly_insight_email.html`
- Sections: adherence summary with chart (matplotlib → embedded PNG, mirror existing visualizer.py approach), pattern detections, suggested adjustments for next week, encouragement framing

**T3.3 — Reasoning bank population**
- After every successful weekly plan + 7 days of execution + weekly review, write a `ReasoningEntry`
- `task_signature` = `weekly_plan_<retail_shift_count>shifts`
- `strategy_summary` = compact description of what worked
- `accuracy_delta` = adherence % minus 0.5 baseline
- Decay on, retrieval at next Sunday's PLAN

**T3.4 — Knowledge fact extraction**
- After weekly review, an LLM pass extracts persistent user facts: "Cooking takes 90 min not 60", "User over-commits on Sundays by ~40%"
- Written as bi-temporal `KnowledgeFact` documents
- Loaded at next planning cycle

**T3.5 — Reasoning bank decay job**
- APScheduler nightly: decay all entries by 0.98 multiplier, prune below 0.3 floor, boost recently used by 1.05 capped at 1.0
- Mirror Phantom Trade's `run_nightly_decay`

**T3.6 — Adherence chart generator**
- `src/services/charts.py` — matplotlib, embedded PNG for email
- Two charts: 7-day adherence bar, by-category adherence

### Phase 3 Acceptance Criteria
- Saturday 9am insight email arrives with accurate adherence data and at least one detected pattern
- Reasoning bank has populated entries after 3 full weeks
- Next Sunday's plan visibly uses prior strategy (planner's NARRATE step references it)
- Knowledge facts table has 3+ entries after 3 weeks

---

## Phase 4 — Intelligence & Realigner

**Goal**: the system gets smart. Adapts to missed days without shaming. Tags energy. Surfaces high-signal correlations.

### Tickets

**T4.1 — Realigner Agent**
- `src/agents/realigner_agent.py`
- Triggered when: 2+ consecutive days at 0% adherence, OR user sends "I'm overwhelmed" / "behind", OR weekly adherence drops below 40%
- PLAN: load goals, current weekly plan, last 7 days adherence
- ACT: scale down — apply 2-minute rule (1hr Leetcode → 1 problem), identify which goals are truly behind vs nice-to-have, deprioritize explicitly
- OBSERVE: tone check (compassionate, no shame language)
- REACT: revised plan written, Telegram message acknowledging without judgment, email update

**T4.2 — Energy/mood tagging**
- Evening reflection adds 1–5 scale prompt: "Energy today? 1–5"
- Stored on `reflection`
- Used by Daily Planner: low-energy days → suggest only 1 commitment

**T4.3 — Correlation insights**
- Weekly Review extends: cross-correlate energy, retail shift days, day-of-week, adherence
- Surface findings: "On 4-shift weeks, your adherence drops 30% — recommend pre-scaling"

**T4.4 — Pattern-based pre-scaling**
- Weekly Planner reads correlation insights → automatically reduces commitment density on predicted-low weeks
- User can override with `/full_plan` command

**T4.5 — Reactive replanning via chat**
- Free-text "I have a doctor's appointment Wednesday 3pm, 90 min" → ingestion parses → updates `daily_plan` for Wednesday → Telegram confirmation

**T4.6 — Streak with freezes**
- Track consecutive days with at least 1 completed commitment
- Auto-grant 1 freeze per week (no streak break)
- Surfaced in `/status`

### Phase 4 Acceptance Criteria
- After a 2-day skip, Realigner activates automatically with revised plan
- Energy tag captured 6/7 days
- Correlation insight produces at least one actionable pattern after 4 weeks of data
- Reactive replan via chat updates plan within 10s

---

## Phase 5 — Polish & Portfolio

**Goal**: shareable. Public-grade. Becomes a portfolio artifact.

### Tickets

**T5.1 — Extend existing Vercel frontend**
- New tab in existing app: "Execution Dashboard"
- Reuses existing `App.tsx` tab structure (Dashboard / 2026 Roadmap / Share Card → adds Execution)
- Components: weekly adherence chart, current week's plan, last 4 weeks trend, knowledge facts table, reasoning bank growth chart
- Reuses existing emerald/dark aesthetic

**T5.2 — Public write-up**
- `docs/CASE_STUDY.md` — architecture, behavioral science integration, results from N weeks of dogfooding
- Numbers: starting adherence vs current, identified patterns, quote-worthy insights
- LinkedIn-ready

**T5.3 — Optional WhatsApp via Twilio Sandbox**
- Only if Telegram has been used reliably for 8+ weeks
- Mirror Telegram bot interface as much as possible
- Note: WhatsApp's 24h messaging window will fight outbound nudges. Real production WhatsApp needs template approval — out of scope.

**T5.4 — Anonymized data export**
- `/api/v2/export` (auth required) → JSON dump for portfolio screenshots without exposing personal goals

**T5.5 — README rewrite**
- Replace existing README with v2 architecture
- Diagram: four loops, three-layer memory, agent topology
- Mirror the Phantom Trade README quality bar — that one is already strong

### Phase 5 Acceptance Criteria
- Dashboard live at existing Vercel URL, no breaking changes to original UI
- Case study published or LinkedIn-shared
- README compelling enough to drive recruiter conversations

---

# PART 3 — Operating Rules for You + Claude Code

## 3.1 How to Run Each Session

1. Start every Claude Code session by pasting **Part 1 (The North Star)**. This is non-negotiable. Without it, Claude Code will drift into "let me redesign this from scratch" mode.
2. Then paste **one ticket** from the current phase. Not the whole phase. One ticket.
3. Ask Claude Code to first state: (a) which files it will create or modify, (b) which existing files it will *not* touch, (c) what tests it will add. Approve before it writes code.
4. After implementation, run the regression check: hit the existing `/analyze-chakra` endpoint with a known input and confirm output matches pre-upgrade.
5. Commit per ticket with a message like `T1.5: constraint solver`. One ticket = one commit, ideally.

## 3.2 What to Do When Claude Code Drifts

Common drift patterns and corrections:

- **Drift**: "Let me redesign the schema..." → **Correction**: "No. Use the existing `chakra_schema.py` patterns. Extend, don't redesign."
- **Drift**: "I'll create a new project structure..." → **Correction**: "We are in `Sath-Chakra-AI`. Add new packages alongside existing ones. Don't restructure."
- **Drift**: "Let me rebuild the agent in pure LangChain..." → **Correction**: "The existing LangGraph workflow stays. We add new agents *alongside* it, not in place of it."
- **Drift**: starts implementing Phase 3 features in Phase 1 → **Correction**: "Out of scope. That's Phase 3 ticket T3.X. Defer."

## 3.3 Definition of Done for Each Phase

A phase is done when:
1. All tickets pass their acceptance criteria
2. Existing `/analyze-chakra` endpoint still produces identical output for a fixed test input
3. Railway deploy succeeds, all logs clean
4. You've used the new behavior for at least one full cycle (one Sunday for Phase 1, one full week for Phase 2, one full month for Phase 3)
5. Bugs surfaced from real usage have been logged as tickets in the next phase

## 3.4 Anti-Patterns to Watch For

- **Building features ahead of usage**. If you haven't lived with Phase 1 for 2 weeks, don't start Phase 2.
- **Refactoring "while we're here"**. Tempting and lethal. Scope creep dies projects.
- **Adding configurability for theoretical users**. Single user. Hardcode. Refactor when you have a second user, not before.
- **Building the dashboard early**. The dashboard is Phase 5 for a reason — it's only meaningful after weeks of real data exist.

## 3.5 Reference Repos to Paste Into Claude Code Context

When working on memory layers (Phase 1 T1.3) or LangGraph agent patterns (Phases 2, 3, 4), paste the relevant Phantom Trade files directly into Claude Code's context:
- `agents/base_agent.py`
- `agents/oracle/graph.py`
- `agents/oracle/material_agent.py`
- `memory/short_term.py`
- `memory/long_term.py`
- `memory/reasoning_bank.py`

Tell Claude Code: "Use these as the reference pattern. Adapt the domain (supply chain → personal execution), keep the structure."

## 3.6 First Move

You're right — I went off the rails. I was treating this like a greenfield project when it's a Sath-Chakra v2. Restarting with the correct framing.

# Sath-Chakra AI v2 — Upgrade Brief for Claude Code

This is an **evolution of the existing repo at `Viraj97-SL/Sath-Chakra-AI`** (already deployed: Railway backend, Vercel frontend). Same project, same deployment, same domain. We're extending what's there — not replacing it.

The current Sath-Chakra is a **one-shot** tool (Wheel of Life input → strategic roadmap + identity card + ICS file → done). The upgrade adds the **execution loop on top**: weekly schedule ingestion, daily reminders via Telegram, end-of-day reflection capture, weekly plan-vs-actual review, with 3-layer memory underneath. The existing one-shot strategic flow stays — it becomes the *quarterly/strategic* layer of a four-loop system.

---

# PART A — What You Set Up Manually

These are additions to your existing deployment. Don't recreate what's already running.

## A1. MongoDB Atlas (new — currently you're on JSON files)

The biggest upgrade-blocker: `data/user_history.json` cannot support a daily companion. You need real persistence.

1. Go to mongodb.com/atlas. If you don't already have an account from any prior project, sign up.
2. Create a new project: `Sath-Chakra-AI`. Free M0 cluster, region close to London (`eu-west-2` AWS).
3. Database Access → create a user with a strong password. Save it.
4. Network Access → for now add your local IP. Once Railway is connected, **also add `0.0.0.0/0`** because Railway egress IPs are dynamic. Acceptable trade-off for a personal tool.
5. Drivers → Python → copy the connection string. It looks like `mongodb+srv://<user>:<pwd>@cluster0.xxxxx.mongodb.net/`.
6. Database name: `sath_chakra`.
7. **Add to Railway environment variables** (Railway dashboard → your Sath-Chakra service → Variables):
   - `MONGODB_URI` = the full connection string with password
   - `MONGODB_DB` = `sath_chakra`
8. **Add the same to your local `.env`** for development.

**Migration note for Claude Code**: the existing `data/user_history.json` records (your 50+ entries) need to be migrated into the new `users` and `chakra_snapshots` collections. Preserve them — they're real data. Claude Code will write a migration script.

## A2. Telegram Bot

1. Telegram → search `@BotFather` → `/newbot`.
2. Name: "Sath-Chakra Companion" (or whatever). Username must end in `bot` — e.g. `sath_chakra_companion_bot`.
3. BotFather gives you a token like `1234567890:ABC...`. Save as `TELEGRAM_BOT_TOKEN`.
4. Get your own chat ID:
   - Send any message to your new bot
   - Open `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser
   - Find `"chat":{"id":NUMBER}` — save as `TELEGRAM_OWNER_CHAT_ID`
5. In BotFather, set commands via `/setcommands`:
   ```
   start - Initialize
   plan - Get this week's plan
   today - Today's commitments
   reflect - End-of-day check-in
   status - Adherence summary
   ```
6. Add both vars to Railway and local `.env`.

## A3. LLM Setup (mostly already done)

You already have `GROQ_API_KEY` and `GOOGLE_API_KEY` in the codebase (`agents/chakra_agent.py`). Keep both.

**One addition**: Gemini 2.5 Flash handles image input — needed for screenshot parsing (your shifts, calendar). Same `GOOGLE_API_KEY`. No new key required.

## A4. Email — Already Configured

`email_service.py` works. Nothing to do.

## A5. Hosting — No Changes Needed

- **Railway** keeps hosting the FastAPI backend. The new agents, scheduler, and Telegram bot all run inside the existing service. One container is enough.
- **Vercel** keeps hosting the existing React frontend. The current Wheel of Life form stays — it becomes the entry point for the *strategic* loop. The new daily/weekly stuff is Telegram-driven, no new frontend pages needed in Phase 1.
- **Telegram polling vs webhook**: start with polling. Polling works fine on Railway, no public URL gymnastics. Switch to webhook only if needed later.
- **APScheduler runs in the FastAPI process**. Don't split into a worker service yet.

## A6. New Environment Variables Summary

Add to Railway and local `.env`:

```
MONGODB_URI=mongodb+srv://...
MONGODB_DB=sath_chakra
TELEGRAM_BOT_TOKEN=...
TELEGRAM_OWNER_CHAT_ID=...
TIMEZONE=Europe/London
QUIET_HOURS_START=22:30
QUIET_HOURS_END=06:30
```

Existing vars (`GROQ_API_KEY`, `GOOGLE_API_KEY`, `EMAIL_*`, `HF_TOKEN`) stay untouched.

---

# PART B — Claude Code Build Brief

Paste this into Claude Code. It's structured: master brief, then per-phase tickets with strict scope and acceptance criteria.

## B0. Master Brief (Paste First)

> **Project**: Sath-Chakra AI v2 — extending the existing repo at this codebase. The current system is a one-shot Wheel of Life → 2026 roadmap + identity card generator. We're adding an execution loop on top: weekly planning, daily Telegram reminders, end-of-day reflection capture, weekly plan-vs-actual review, with 3-layer memory.
>
> **Critical constraints**:
> - **Do NOT break the existing `/analyze-chakra` endpoint or the existing React frontend.** It is in production. Both must keep working unchanged after every commit.
> - **Migrate, don't replace.** `data/user_history.json` contains real data. Migrate it, then deprecate JSON file storage.
> - **Reuse what works**: `LangGraph` workflow pattern from `chakra_agent.py`, the SMTP `email_service.py`, Pydantic schemas in `chakra_schema.py`, Playwright card generation. Don't rewrite these.
> - **Single user (me) for now.** No multi-tenant flows, no signup. Hardcoded `TELEGRAM_OWNER_CHAT_ID` is the user identifier in Phase 1.
> - **Production hygiene**: every new LLM call returns Pydantic-validated structured output, with retries and a fallback chain (Gemini Flash → Gemini Pro → Groq). No free-form parsing.
>
> **Tech additions on top of current stack**:
> - `motor` (async MongoDB driver) — replaces JSON file storage
> - `python-telegram-bot` v21+ — Telegram interface
> - `apscheduler` — cron jobs for morning briefs, evening reflections, weekly review
> - `structlog` — structured logging (currently using print statements)
> - Optional: `langgraph` checkpointer to MongoDB (the existing agent uses in-memory)
>
> **Architectural principles to follow** (these are non-negotiable):
> 1. **Four-loop model**: Strategic (existing one-shot, quarterly), Tactical (weekly planner, Sunday), Operational (daily morning + evening), Reactive (in-day chat events). Each is its own LangGraph subgraph or scheduled job.
> 2. **Three-layer memory** (mirrors the developer's other Phantom Trade project): short-term sessions (TTL 24h), long-term bi-temporal facts and goals (`valid_from`/`valid_to`), reasoning bank (decay-scored strategies that improve over time).
> 3. **Constraint solver before LLM**: time-block math (sleep, retail shifts, commute, cooking) is computed deterministically. The LLM only writes human-readable descriptions and handles soft preferences. Never let the LLM do arithmetic on time budgets.
> 4. **Idempotent scheduled jobs**: morning brief at 7am must not double-fire if Railway restarts. Job IDs derived from `(user_id, date, job_type)`.
> 5. **Audit trail**: every agent run logs to an `agent_runs` collection — input snapshot, output snapshot, latency, cost. This is debug surface and reasoning bank source data.
> 6. **Quiet hours**: no Telegram messages between 22:30 and 06:30 unless user-initiated.

## B1. Phase 0 — Plumbing & Migration (target: 2–3 days of Claude Code work)

### Tickets

**T0.1 — Repo refactor for new structure**
- Move existing code: `src/agents/chakra_agent.py` stays but is renamed conceptually as the *Strategist agent* (the one-shot quarterly path)
- New top-level packages: `src/db/`, `src/memory/`, `src/agents/`, `src/scheduler/`, `src/telegram_bot/`, `src/services/`
- Existing `src/utils/` stays
- Update `requirements.txt` with new dependencies; pin versions

**T0.2 — MongoDB connection layer**
- `src/db/connection.py` — async `motor` client, connection pool, ping health check, graceful shutdown hook in FastAPI lifespan
- Same pattern the developer used in Phantom Trade — Claude Code can mirror that style

**T0.3 — Pydantic schemas for new collections**
- `src/models/` — split out: `user.py`, `goal.py`, `weekly_plan.py`, `daily_plan.py`, `activity_log.py`, `reflection.py`, `agent_session.py`, `knowledge_fact.py`, `reasoning_entry.py`, `agent_run.py`, `inbound_message.py`
- Bi-temporal fields (`valid_from`, `valid_to`) on `goal`, `knowledge_fact`
- Existing `chakra_schema.py` stays untouched

**T0.4 — MongoDB indexes**
- `src/db/indexes.py` — programmatic index creation, idempotent. Cover all query patterns: `(user_id, week_start)`, `(daily_plan_id, status)`, `(task_signature, decay_score)`, TTL on `agent_sessions.expires_at`, etc.

**T0.5 — Migration script**
- `scripts/migrate_json_to_mongo.py` — reads `data/user_history.json`, deduplicates by `user_id` + `timestamp`, creates `users` records, creates `chakra_snapshots` records (preserving the existing Wheel of Life data)
- Idempotent — running twice doesn't duplicate
- Logs counts: users migrated, snapshots migrated, skipped duplicates

**T0.6 — Refactor `/analyze-chakra` to write to MongoDB**
- Existing endpoint behavior unchanged from the user's perspective
- Internal: `save_user_snapshot` in `database.py` now writes to Mongo, not JSON
- Old JSON file kept as backup, not appended to anymore
- All existing tests/manual checks must still pass

**T0.7 — Structured logging**
- Replace `print()` statements with `structlog` throughout. JSON output in production, pretty in dev.

**T0.8 — Health endpoints**
- `/healthz` — basic alive check (already exists implicitly)
- `/readyz` — checks Mongo ping, returns 200/503

### Phase 0 Acceptance Criteria

- Existing `/analyze-chakra` endpoint produces identical output to before — verified by running same input through old and new
- Mongo collections created with all indexes
- All 50+ existing JSON records visible in `chakra_snapshots` collection
- Railway deploy works; logs show successful Mongo connection on boot
- No new public endpoints yet — Phase 0 is purely internal

---

## B2. Phase 1 — Sunday Loop (target: 1 week of Claude Code work)

This is where the new behavior begins. By end of Phase 1: you upload screenshots Sunday evening, you get a structured weekly plan via email + Telegram. That's the whole goal.

### Tickets

**T1.1 — Telegram bot scaffolding**
- `src/telegram_bot/bot.py` — `python-telegram-bot` v21+ application, polling mode
- Runs as an asyncio task inside the FastAPI lifespan
- Owner-only filter: ignore any message not from `TELEGRAM_OWNER_CHAT_ID` (single-user mode)
- Commands: `/start`, `/help`, `/plan`, `/upload` (initiates schedule upload flow)
- All inbound messages logged to `inbound_messages` collection (audit trail)

**T1.2 — Schedule ingestion service**
- `src/services/ingestion.py`
- Accepts: photo (Telegram file), document (xlsx/csv), or text
- For images: calls Gemini 2.5 Flash with vision + structured JSON output prompt → extracts shifts, commute blocks, fixed appointments
- For xlsx/csv: pandas read + column mapping (Claude Code: write a heuristic mapper that handles the user's existing UPSkill spreadsheet format)
- Output: a validated `RawScheduleInput` Pydantic model
- Confidence score per field; low-confidence fields trigger a Telegram confirmation message ("I read your shift as 14:00–22:00 Wed/Thu/Sat — confirm? [Yes/No]")

**T1.3 — Memory layer**
- `src/memory/short_term.py` — session creation, phase tracking, TTL — port the pattern from Phantom Trade
- `src/memory/long_term.py` — bi-temporal goals and knowledge facts — port the pattern
- `src/memory/reasoning_bank.py` — decay-scored strategies, retrieval — port the pattern
- These three modules mirror what's in the Phantom Trade repo. Claude Code should be told to use that as the reference (the developer can paste those files directly into context).

**T1.4 — Goal hierarchy seeding**
- `scripts/seed_goals.py` — one-time script to populate the user's goal tree. Final goal: "Get Data Scientist role + financial stability". Quarterly: skill milestones. Monthly: applications, project completions. Pulled from existing UPSkill sheet activities.
- Bi-temporal: `valid_from = now`, `valid_to = null`

**T1.5 — Constraint solver**
- `src/services/constraint_solver.py` — pure-Python, no LLM
- Inputs: `RawScheduleInput`, user's fixed daily blocks (sleep window, cooking, buffer), goal-derived activity backlog
- Outputs: per-day available slots with `start_time`, `end_time`, `energy_class` (high/med/low — heuristic: morning + post-commute = high, late evening = low)
- Greedy assignment: high-priority deep-work activities go to high-energy slots first
- Hard rules: no two deep-work blocks back-to-back, mandatory rest day if previous week had >5 working days, max 3 commitments per day
- Unit-testable in isolation — no external dependencies

**T1.6 — Weekly Planner Agent**
- `src/agents/weekly_planner_agent.py` — LangGraph subgraph: PLAN → SOLVE → NARRATE → DELIVER
  - PLAN: load goals, last week's adherence (empty in week 1), top reasoning-bank strategies (also empty initially)
  - SOLVE: call constraint solver
  - NARRATE: pass solver output to LLM for human-readable activity descriptions and a 3-sentence "Coach's note for the week" — Pydantic-validated output
  - DELIVER: write `WeeklyPlan` doc, render HTML email, send via existing `email_service.py`, send Telegram summary card
- Structured output enforced via Pydantic
- Fallback chain: Gemini Flash → Gemini Pro → Groq Llama 70B

**T1.7 — Email template for weekly plan**
- `src/templates/weekly_plan_email.html` — clean calendar-style HTML, day-by-day blocks, no inline JS, mobile-friendly
- Reuse the visual language of the existing Sath-Chakra "cyber-audit" aesthetic — emerald accents, dark mode, JetBrains Mono for time blocks
- Test by sending to yourself and checking on phone

**T1.8 — Telegram weekly summary message**
- Compact: top 3 priorities for the week, daily-time-budget summary, "Full plan emailed to you ✉️"
- Markdown-formatted, Telegram-safe escaping

**T1.9 — Sunday upload flow (conversational state machine)**
- User sends `/upload` → bot asks for shift screenshot → user sends → bot confirms parse → asks for calendar screenshot → user sends → bot confirms → asks for any other commitments as text → user replies → bot asks "ready to generate weekly plan? [Yes/No]" → on yes, fires Weekly Planner Agent
- Conversation state stored in short-term memory (session)
- Timeout: 30 min of inactivity → session expires, bot says "session expired, send /upload to restart"

**T1.10 — Manual Sunday trigger**
- For Phase 1, Sunday upload is **user-initiated** via `/upload`. No scheduled trigger yet.
- APScheduler job `weekly_review_reminder` fires every Sunday 18:00 with a Telegram nudge: "Sunday evening — ready to plan next week? Send me your shift screenshot."

### Phase 1 Acceptance Criteria

- User sends shift screenshot via Telegram → bot extracts structured shifts within 15 seconds
- User confirms → bot generates weekly plan respecting all constraints (no activity scheduled during shifts, sleep, or commute)
- Email arrives within 30 seconds of confirmation, renders correctly on mobile
- Telegram summary arrives at the same time
- `WeeklyPlan` document written to MongoDB with full provenance (which agent run produced it, which inputs were used)
- Existing `/analyze-chakra` endpoint still works identically
- Sunday 18:00 nudge fires reliably

---

## B3. What's Out of Scope for Phases 0+1 (Tell Claude Code Explicitly)

Defer ruthlessly. These are tempting but premature:

- Daily morning briefs and evening reflection — **Phase 2**
- Weekly plan-vs-actual review — **Phase 3**
- Realigner agent (missed-day recovery) — **Phase 4**
- Energy/mood tagging — **Phase 4**
- Knowledge-fact extraction from reflections — **Phase 4**
- WhatsApp integration — **Phase 5+**
- Multi-user, signup, auth — **Phase 5+**
- New frontend dashboard for the daily/weekly stuff — **Phase 5+**

If Claude Code starts building these, push back. The point of Phase 1 is to live with the Sunday loop for 2–3 weeks before committing to the rest.

---

## B4. Testing Requirements

For every new module, Claude Code must add:

- **Pydantic round-trip tests** — every model serialized + deserialized round-trips cleanly
- **Constraint solver tests** — golden test cases: "given retail shifts Wed/Thu/Sat 14–22, sleep 23–07, commute 1h each way, output must show no scheduled activity in those blocks" — pure deterministic, no LLM mocking needed
- **Telegram bot tests** — mock the bot, simulate inbound messages, assert correct state transitions
- **Migration script test** — runs against a fresh test DB and produces expected counts

---

## B5. How to Use This With Claude Code in PyCharm

1. Open the existing Sath-Chakra repo in PyCharm.
2. Open the Claude Code panel.
3. Paste **B0 (Master Brief)** as the first message. Confirm Claude Code understood by asking it to summarize the four-loop model and the constraints.
4. Then paste **Phase 0 tickets one at a time** — don't dump all of Phase 0 at once. One ticket per session (or per major task). Review the diff in PyCharm before accepting.
5. After each ticket: run the existing `/analyze-chakra` endpoint manually as a regression check. If it broke, revert.
6. Only move to Phase 1 once Phase 0 acceptance criteria all pass.
7. **Memory anchors**: every few sessions, remind Claude Code: "We're upgrading Sath-Chakra (existing repo, deployed on Railway+Vercel), not building from scratch. Don't rename or replace files unless the ticket explicitly says so."

---
