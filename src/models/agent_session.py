from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, ClassVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class SessionPhase(str, Enum):
    UPLOAD_SHIFT = "upload_shift"
    UPLOAD_CALENDAR = "upload_calendar"
    UPLOAD_OTHER = "upload_other"
    CONFIRM = "confirm"
    GENERATING = "generating"
    COMPLETE = "complete"
    EXPIRED = "expired"


def _default_expires_at() -> datetime:
    return datetime.utcnow() + timedelta(minutes=30)


class AgentSessionDoc(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    collection_name: ClassVar[str] = "agent_sessions"

    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    phase: SessionPhase = SessionPhase.UPLOAD_SHIFT
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=_default_expires_at)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
