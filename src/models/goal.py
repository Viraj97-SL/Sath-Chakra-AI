from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import ClassVar, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class GoalLevel(str, Enum):
    FINAL = "final"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    WEEKLY = "weekly"


class GoalDoc(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    collection_name: ClassVar[str] = "goals"

    goal_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    title: str
    description: Optional[str] = None
    level: GoalLevel
    parent_goal_id: Optional[str] = None
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_to: Optional[datetime] = None
    priority: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
