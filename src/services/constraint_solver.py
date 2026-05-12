from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Literal


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TimeBlock:
    start: time
    end: time
    label: str

    def duration_minutes(self) -> int:
        s = datetime.combine(date.today(), self.start)
        e = datetime.combine(date.today(), self.end)
        if e <= s:
            e += timedelta(days=1)
        return int((e - s).total_seconds() / 60)

    def overlaps(self, other: TimeBlock) -> bool:
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True)
class AvailableSlot:
    date: date
    start: time
    end: time
    energy_class: Literal["high", "medium", "low"]

    def duration_minutes(self) -> int:
        s = datetime.combine(self.date, self.start)
        e = datetime.combine(self.date, self.end)
        return int((e - s).total_seconds() / 60)


@dataclass
class ActivityRequest:
    goal_id: str
    title: str
    duration_minutes: int
    energy_required: Literal["high", "medium", "low"]
    priority: int           # lower = higher priority
    is_deep_work: bool = False
    max_per_week: int = 7


@dataclass
class ScheduledActivity:
    activity: ActivityRequest
    slot: AvailableSlot
    day_of_week: int        # 0 = Monday


@dataclass
class DayPlanOutput:
    date: date
    day_of_week: int
    is_shift_day: bool
    available_slots: list[AvailableSlot]
    scheduled: list[ScheduledActivity] = field(default_factory=list)


@dataclass
class SolverOutput:
    week_start: date
    days: list[DayPlanOutput]
    unscheduled: list[ActivityRequest]


# ── Constants ──────────────────────────────────────────────────────────────────

_MORNING_START = time(7, 0)
_ROUTINE_END = time(8, 0)
_LUNCH_START = time(12, 30)
_LUNCH_END = time(13, 30)
_DINNER_START = time(19, 0)
_DINNER_END = time(20, 0)
_WIND_DOWN = time(22, 0)
_COMMUTE = timedelta(hours=1)
_MAX_PER_DAY = 3
_MIN_SLOT = 30          # minutes — shorter slots ignored
_BUFFER = timedelta(minutes=15)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse_time(s: str) -> time:
    h, m = map(int, s.split(":"))
    return time(h, m)


def _energy(start: time) -> Literal["high", "medium", "low"]:
    h = start.hour
    if 8 <= h < 12:
        return "high"
    if 12 <= h < 14:
        return "medium"
    if 14 <= h < 18:
        return "high"
    if 18 <= h < 21:
        return "medium"
    return "low"


def _build_occupied(day: date, shifts: list[dict]) -> list[TimeBlock]:
    day_name = day.strftime("%A").lower()
    occupied: list[TimeBlock] = [
        TimeBlock(_MORNING_START, _ROUTINE_END, "morning_routine"),
    ]

    day_shifts = [s for s in shifts if s.get("day", "").lower() == day_name]
    for sh in day_shifts:
        s_start = _parse_time(sh["start_time"])
        s_end = _parse_time(sh["end_time"])

        commute_to_start = (datetime.combine(day, s_start) - _COMMUTE).time()
        occupied.append(TimeBlock(commute_to_start, s_start, "commute_to"))
        occupied.append(TimeBlock(s_start, s_end, "shift"))

        commute_back_end_dt = datetime.combine(day, s_end) + _COMMUTE
        commute_back_end = min(commute_back_end_dt.time(), _WIND_DOWN)
        occupied.append(TimeBlock(s_end, commute_back_end, "commute_back"))

    if not day_shifts:
        occupied.append(TimeBlock(_LUNCH_START, _LUNCH_END, "lunch"))
        occupied.append(TimeBlock(_DINNER_START, _DINNER_END, "dinner"))
    else:
        lunch = TimeBlock(_LUNCH_START, _LUNCH_END, "lunch")
        if not any(b.overlaps(lunch) for b in occupied):
            occupied.append(lunch)

    occupied.append(TimeBlock(_WIND_DOWN, time(23, 0), "wind_down"))
    occupied.sort(key=lambda b: b.start)
    return occupied


def _free_slots(day: date, occupied: list[TimeBlock]) -> list[AvailableSlot]:
    slots: list[AvailableSlot] = []
    cursor = _ROUTINE_END

    for block in sorted(occupied, key=lambda b: b.start):
        if block.start > cursor:
            dur = int(
                (datetime.combine(day, block.start) - datetime.combine(day, cursor)).total_seconds() / 60
            )
            if dur >= _MIN_SLOT:
                slots.append(AvailableSlot(day, cursor, block.start, _energy(cursor)))
        if block.end > cursor:
            cursor = block.end

    if cursor < _WIND_DOWN:
        dur = int(
            (datetime.combine(day, _WIND_DOWN) - datetime.combine(day, cursor)).total_seconds() / 60
        )
        if dur >= _MIN_SLOT:
            slots.append(AvailableSlot(day, cursor, _WIND_DOWN, _energy(cursor)))

    return slots


def _energy_ok(required: str, available: str) -> bool:
    order = {"low": 0, "medium": 1, "high": 2}
    return order[available] >= order[required]


# ── Public API ─────────────────────────────────────────────────────────────────

def solve(
    week_start_date: date,
    shifts: list[dict],
    activities: list[ActivityRequest],
) -> SolverOutput:
    """
    Greedy constraint solver — pure Python, no LLM.

    Hard rules:
    - No activity during shift / commute / sleep / meals
    - Max 3 commitments per day
    - No two deep-work blocks on the same day
    - Slots shorter than 30 minutes are skipped
    - 15-minute buffer inserted after each assigned activity
    """
    queue = sorted(activities, key=lambda a: a.priority)
    weekly_count: dict[str, int] = {a.title: 0 for a in activities}
    days_output: list[DayPlanOutput] = []
    unscheduled: list[ActivityRequest] = []

    for offset in range(7):
        day = week_start_date + timedelta(days=offset)
        day_name = day.strftime("%A").lower()
        is_shift = any(s.get("day", "").lower() == day_name for s in shifts)

        occupied = _build_occupied(day, shifts)
        slots = _free_slots(day, occupied)

        scheduled: list[ScheduledActivity] = []
        deep_work_today = 0

        for act in queue:
            if len(scheduled) >= _MAX_PER_DAY:
                break
            if weekly_count[act.title] >= act.max_per_week:
                continue
            if act.is_deep_work and deep_work_today >= 1:
                continue

            for slot in list(slots):
                if slot.duration_minutes() < act.duration_minutes:
                    continue
                if not _energy_ok(act.energy_required, slot.energy_class):
                    continue

                use_end = (
                    datetime.combine(slot.date, slot.start)
                    + timedelta(minutes=act.duration_minutes)
                ).time()

                assigned_slot = AvailableSlot(slot.date, slot.start, use_end, slot.energy_class)
                scheduled.append(ScheduledActivity(act, assigned_slot, offset))
                weekly_count[act.title] += 1
                if act.is_deep_work:
                    deep_work_today += 1

                # Shrink slot: remove used portion + buffer
                slots.remove(slot)
                next_start_dt = datetime.combine(slot.date, use_end) + _BUFFER
                remaining = int(
                    (datetime.combine(slot.date, slot.end) - next_start_dt).total_seconds() / 60
                )
                if remaining >= _MIN_SLOT:
                    slots.append(
                        AvailableSlot(slot.date, next_start_dt.time(), slot.end, _energy(next_start_dt.time()))
                    )
                break

        days_output.append(
            DayPlanOutput(day, offset, is_shift, slots, scheduled)
        )

    for act in activities:
        if weekly_count[act.title] == 0:
            unscheduled.append(act)

    return SolverOutput(week_start_date, days_output, unscheduled)
