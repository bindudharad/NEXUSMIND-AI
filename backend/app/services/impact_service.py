import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.schemas.impact import EnterpriseImpactResponse, EnterpriseImpactSummary


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ROI_HISTORY = DATA_DIR / "roi_intelligence_history.jsonl"
PLATFORM_HISTORY = DATA_DIR / "complete_platform_history.jsonl"
RECRUITER_HISTORY = DATA_DIR / "recruiter_impression_history.jsonl"


class EnterpriseImpactService:
    """Fast homepage impact snapshot from persisted audit histories."""

    def summary(self) -> EnterpriseImpactResponse:
        roi = self._read_last_jsonl(ROI_HISTORY)
        platform = self._read_last_jsonl(PLATFORM_HISTORY)
        recruiter = self._read_last_jsonl(RECRUITER_HISTORY)

        roi_summary = self._dict(roi.get("summary"))
        platform_summary = self._dict(platform.get("summary"))
        recruiter_summary = self._dict(recruiter.get("summary"))
        executive_insights = roi.get("executive_insights")
        top_insight = self._first_message(executive_insights)

        net_savings = self._float(roi_summary.get("net_savings"))
        baseline_annual_loss = self._float(roi_summary.get("baseline_annual_loss"))
        roi_percent = self._float(roi_summary.get("roi_percent"))
        payback_months = self._float(roi_summary.get("payback_months"))
        capabilities_ready = self._int(platform_summary.get("ready"))
        capabilities_total = self._int(platform_summary.get("total_capabilities"))
        realtime_streams = self._int(platform_summary.get("realtime_streams"))
        platform_score = self._float(platform_summary.get("platform_score"))
        recruiter_score = self._float(recruiter_summary.get("overall_score"))
        judge_wow_score = self._float(recruiter_summary.get("judge_wow_score"))
        residual_risk = str(recruiter_summary.get("residual_risk_level") or "medium").lower()
        if residual_risk not in {"low", "medium", "high"}:
            residual_risk = "medium"

        proof_points = [
            f"${net_savings:,.0f} modeled net savings after intervention cost.",
            f"{capabilities_ready}/{capabilities_total} enterprise AI OS capabilities ready.",
            f"{realtime_streams} realtime intelligence streams available for live dashboards.",
            f"{recruiter_score:.0f}/100 recruiter-grade product quality score.",
        ]

        source_histories = [
            path.name
            for path in (ROI_HISTORY, PLATFORM_HISTORY, RECRUITER_HISTORY)
            if path.exists() and path.stat().st_size > 0
        ]

        return EnterpriseImpactResponse(
            model="Persisted Enterprise Impact Snapshot",
            generated_at=datetime.now(timezone.utc),
            summary=EnterpriseImpactSummary(
                net_savings=net_savings,
                baseline_annual_loss=baseline_annual_loss,
                roi_percent=roi_percent,
                payback_months=payback_months,
                platform_score=platform_score,
                capabilities_ready=capabilities_ready,
                capabilities_total=capabilities_total,
                realtime_streams=realtime_streams,
                recruiter_score=recruiter_score,
                judge_wow_score=judge_wow_score,
                residual_risk_level=residual_risk,  # type: ignore[arg-type]
            ),
            top_business_insight=top_insight
            or f"NEXUSMIND models ${net_savings:,.0f} net savings after intervention cost.",
            strongest_signal=str(
                recruiter_summary.get("strongest_signal")
                or "Enterprise operating risk is tied to measurable workforce, revenue, delivery, client, and security decisions."
            ),
            proof_points=proof_points,
            source_histories=source_histories,
        )

    @staticmethod
    def _read_last_jsonl(path: Path, max_bytes: int = 1_048_576) -> dict[str, Any]:
        if not path.exists() or path.stat().st_size == 0:
            return {}

        with path.open("rb") as handle:
            size = handle.seek(0, 2)
            offset = max(size - max_bytes, 0)
            handle.seek(offset)
            if offset:
                handle.readline()
            lines = [line for line in handle.read().splitlines() if line.strip()]

        for line in reversed(lines):
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        return {}

    @staticmethod
    def _dict(value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _first_message(value: Any) -> str | None:
        if not isinstance(value, list) or not value:
            return None
        first = value[0]
        if not isinstance(first, dict):
            return None
        message = first.get("message")
        return str(message) if message else None

    @staticmethod
    def _float(value: Any) -> float:
        try:
            return round(float(value), 2)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _int(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0


enterprise_impact_service = EnterpriseImpactService()
