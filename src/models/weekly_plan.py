from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ActivityBlock(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    activity_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    goal_id: str
    start_time: str
    end_time: str
    energy_class: Literal["high", "medium", "low"]
    day_of_week: int


class DayPlan(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    day_of_week: int
    date: str
    blocks: list[ActivityBlock] = Field(default_factory=list)


class WeeklyPlanDoc(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    collection_name: ClassVar[str] = "weekly_plans"

    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    week_start: str
    day_plans: list[DayPlan] = Field(default_factory=list)
    coach_note: str = ""
    agent_run_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["draft", "active", "completed"] = "active"
