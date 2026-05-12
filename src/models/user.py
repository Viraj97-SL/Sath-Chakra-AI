from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field


class UserDoc(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    collection_name: ClassVar[str] = "users"

    user_id: str
    email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    timezone: str = "Europe/London"
    telegram_chat_id: Optional[str] = None
