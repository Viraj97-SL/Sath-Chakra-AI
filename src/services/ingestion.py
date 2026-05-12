from __future__ import annotations

import json
import os
import re
from datetime import date, timedelta
from typing import Literal

import structlog
from pydantic import BaseModel

logger = structlog.get_logger()

_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_DAY_ABBR = {
    "mon": "Monday", "tue": "Tuesday", "wed": "Wednesday",
    "thu": "Thursday", "fri": "Friday", "sat": "Saturday", "sun": "Sunday",
}


class ShiftBlock(BaseModel):
    day: str
    start_time: str   # "HH:MM" 24h
    end_time: str     # "HH:MM" 24h


class RawScheduleInput(BaseModel):
    shifts: list[ShiftBlock]
    fixed_appointments: list[ShiftBlock]
    other_commitments: str
    week_start: str           # ISO date of next Monday
    parse_confidence: float   # 0.0–1.0


def _next_monday() -> str:
    today = date.today()
    days_ahead = 7 - today.weekday()  # 0=Monday
    if days_ahead == 7:
        days_ahead = 7
    return (today + timedelta(days=days_ahead)).isoformat()


async def parse_image(image_bytes: bytes, week_start: str | None = None) -> RawScheduleInput:
    """Parse a shift schedule screenshot using Gemini 2.5 Flash vision."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        prompt = (
            "Extract all work shifts from this schedule image.\n\n"
            "Return ONLY a JSON object — no markdown, no explanation:\n"
            "{\n"
            '  "shifts": [\n'
            '    {"day": "Monday", "start_time": "14:00", "end_time": "22:00"},\n'
            '    ...\n'
            "  ],\n"
            '  "fixed_appointments": [],\n'
            '  "parse_confidence": 0.95\n'
            "}\n\n"
            "Rules:\n"
            "- day must be the full English day name (Monday, Tuesday, etc.)\n"
            "- times must be HH:MM in 24-hour format\n"
            "- if no shifts are visible, return shifts as empty array\n"
            "- parse_confidence: 1.0 = perfectly clear, 0.5 = guessed some details"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                prompt,
            ],
        )

        raw = response.text.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)
        return RawScheduleInput(
            shifts=[ShiftBlock(**s) for s in parsed.get("shifts", [])],
            fixed_appointments=[ShiftBlock(**a) for a in parsed.get("fixed_appointments", [])],
            other_commitments="",
            week_start=week_start or _next_monday(),
            parse_confidence=float(parsed.get("parse_confidence", 0.8)),
        )

    except Exception as exc:
        logger.warning("image_parse_failed", error=str(exc))
        return RawScheduleInput(
            shifts=[],
            fixed_appointments=[],
            other_commitments="",
            week_start=week_start or _next_monday(),
            parse_confidence=0.0,
        )


async def parse_text(text: str, week_start: str | None = None) -> RawScheduleInput:
    """
    Parse typed shift text, e.g. 'Mon 14:00-22:00, Thu 14:00-22:00'
    Falls back to Gemini for natural language inputs.
    """
    shifts = _try_regex_parse(text)
    if shifts:
        return RawScheduleInput(
            shifts=shifts,
            fixed_appointments=[],
            other_commitments="",
            week_start=week_start or _next_monday(),
            parse_confidence=0.95,
        )

    # Gemini fallback for natural language
    return await _gemini_text_parse(text, week_start or _next_monday())


def _try_regex_parse(text: str) -> list[ShiftBlock]:
    """Extract shifts from patterns like 'Mon 14:00-22:00' or 'Monday 2pm-10pm'."""
    pattern = re.compile(
        r"(mon|tue|wed|thu|fri|sat|sun)\w*\s+"
        r"(\d{1,2}(?::\d{2})?(?:am|pm)?)\s*[-–]\s*(\d{1,2}(?::\d{2})?(?:am|pm)?)",
        re.IGNORECASE,
    )
    shifts = []
    for m in pattern.finditer(text):
        day_abbr = m.group(1).lower()[:3]
        day_full = _DAY_ABBR.get(day_abbr)
        if not day_full:
            continue
        start = _normalise_time(m.group(2))
        end = _normalise_time(m.group(3))
        if start and end:
            shifts.append(ShiftBlock(day=day_full, start_time=start, end_time=end))
    return shifts


def _normalise_time(raw: str) -> str | None:
    raw = raw.strip().lower()
    ampm = None
    if raw.endswith("am"):
        ampm, raw = "am", raw[:-2]
    elif raw.endswith("pm"):
        ampm, raw = "pm", raw[:-2]
    parts = raw.split(":")
    try:
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
    except ValueError:
        return None
    if ampm == "pm" and h != 12:
        h += 12
    if ampm == "am" and h == 12:
        h = 0
    return f"{h:02d}:{m:02d}"


async def _gemini_text_parse(text: str, week_start: str) -> RawScheduleInput:
    try:
        from google import genai

        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        prompt = (
            f"The user described their work schedule: \"{text}\"\n\n"
            "Extract all work shifts. Return ONLY JSON:\n"
            '{"shifts": [{"day": "Monday", "start_time": "14:00", "end_time": "22:00"}], '
            '"fixed_appointments": [], "parse_confidence": 0.9}'
        )
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.text.strip())
        parsed = json.loads(raw)
        return RawScheduleInput(
            shifts=[ShiftBlock(**s) for s in parsed.get("shifts", [])],
            fixed_appointments=[ShiftBlock(**a) for a in parsed.get("fixed_appointments", [])],
            other_commitments="",
            week_start=week_start,
            parse_confidence=float(parsed.get("parse_confidence", 0.7)),
        )
    except Exception as exc:
        logger.warning("gemini_text_parse_failed", error=str(exc))
        return RawScheduleInput(
            shifts=[], fixed_appointments=[], other_commitments="",
            week_start=week_start, parse_confidence=0.0,
        )
