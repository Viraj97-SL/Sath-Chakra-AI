from __future__ import annotations

from datetime import datetime
from typing import ClassVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class PatternDetection(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    description: str
    category: str
    confidence: float


class WeeklyInsightDoc(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    collection_name: ClassVar[str] = "weekly_insights"

    insight_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    week_start: str
    adherence_pct: float
    by_day: dict[str, float] = Field(default_factory=dict)
    by_category: dict[str, float] = Field(default_factory=dict)
    patterns: list[PatternDetection] = Field(default_factory=list)
    agent_run_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
