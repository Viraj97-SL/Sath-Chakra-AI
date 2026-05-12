from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ReflectionDoc(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    collection_name: ClassVar[str] = "reflections"

    reflection_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    date: str
    free_text: str
    energy_score: Optional[int] = None
    parsed_completions: list[str] = Field(default_factory=list)
    agent_run_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
