from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class AgentRunDoc(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    collection_name: ClassVar[str] = "agent_runs"

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    agent_name: str
    input_snapshot: dict[str, Any]
    output_snapshot: Optional[dict[str, Any]] = None
    latency_ms: Optional[int] = None
    llm_cost_usd: Optional[float] = None
    status: Literal["running", "success", "failed"] = "running"
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
