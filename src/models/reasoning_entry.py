from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ReasoningEntryDoc(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    collection_name: ClassVar[str] = "reasoning_entries"

    entry_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    task_signature: str
    strategy_summary: str
    accuracy_delta: float
    decay_score: float = 1.0
    use_count: int = 0
    last_used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
