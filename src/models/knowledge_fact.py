from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeFactDoc(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    collection_name: ClassVar[str] = "knowledge_facts"

    fact_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    fact_text: str
    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_to: Optional[datetime] = None
    source_week: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
