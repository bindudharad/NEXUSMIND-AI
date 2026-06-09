from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


StackStatus = Literal["ready", "configured", "missing", "error"]


class TechnologyCheck(BaseModel):
    name: str
    category: str
    status: StackStatus
    details: str
    evidence: list[str] = Field(default_factory=list)


class TechnologyStackSummary(BaseModel):
    total: int
    ready: int
    configured: int
    missing: int
    errors: int
    production_ready_score: float = Field(ge=0, le=100)


class TechnologyStackResponse(BaseModel):
    generated_at: datetime
    environment: str
    summary: TechnologyStackSummary
    checks: list[TechnologyCheck]
    recommendations: list[str]
