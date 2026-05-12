from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class InboundMessageDoc(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    collection_name: ClassVar[str] = "inbound_messages"

    message_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    telegram_message_id: int
    text: Optional[str] = None
    has_photo: bool = False
    has_document: bool = False
    file_id: Optional[str] = None
    received_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
