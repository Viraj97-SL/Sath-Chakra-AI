from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from src.models.weekly_plan import ActivityBlock


class DailyPlanDoc(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    collection_name: ClassVar[str] = "daily_plans"

    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    date: str
    weekly_plan_id: str
    commitments: list[ActivityBlock] = Field(default_factory=list)
    confirmed: bool = False
    confirmation_sent_at: Optional[datetime] = None
    agent_run_id: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
