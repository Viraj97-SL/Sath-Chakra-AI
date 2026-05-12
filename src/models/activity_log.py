from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import ClassVar, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class CompletionStatus(str, Enum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    DEFERRED = "deferred"


class ActivityLogDoc(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    collection_name: ClassVar[str] = "activity_logs"

    log_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    date: str
    daily_plan_id: str
    activity_id: str
    title: str
    status: CompletionStatus
    notes: Optional[str] = None
    logged_at: datetime = Field(default_factory=datetime.utcnow)
    source: Literal["telegram", "reflection", "api"] = "telegram"
