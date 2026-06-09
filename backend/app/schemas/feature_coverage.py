from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


FeatureCoverageStatus = Literal["ready", "warning", "missing", "error"]


class FeatureCoverageCheck(BaseModel):
    name: str
    category: str
    status: FeatureCoverageStatus
    details: str
    evidence: list[str] = Field(default_factory=list)
    remediation: str | None = None


class FeatureCoverageSummary(BaseModel):
    total: int
    ready: int
    warnings: int
    missing: int
    errors: int
    coverage_score: float = Field(ge=0, le=100)


class FeatureCoverageResponse(BaseModel):
    generated_at: datetime
    summary: FeatureCoverageSummary
    checks: list[FeatureCoverageCheck]
    critical_gaps: list[str]
    verdict: str
