from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from threading import Lock

import numpy as np

from app.schemas.employee_dashboard import EmployeeDashboardRequest
from app.schemas.nlp import NLPAnalyzeRequest, NLPBatchRequest
from app.schemas.voice import VoiceStressAnalyzeRequest
from app.schemas.wellness import (
    TypingBehaviorAnalytics,
    TypingTelemetryPoint,
    WellnessAnalysisResponse,
    WellnessAnalyzeRequest,
    WellnessHeatmapCell,
    WellnessMessage,
    WellnessRecommendation,
    WellnessRiskAlert,
    WellnessSummary,
    WellnessTeamMember,
    WorkPatternWellnessAnalytics,
)
from app.services.employee_dashboard_service import employee_dashboard_service
from app.services.nlp_service import nlp_service
from app.services.voice_service import voice_stress_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "wellness_analysis_history.jsonl"


class WellnessIntelligenceService:
    model_name = "PyTorch NLP + RandomForest Voice + Burnout Ensemble Wellness AI"
    behavioral_model = "Typing Rhythm Behavioral Stress Model + Work Pattern Burnout Forecaster"

    def __init__(self) -> None:
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def analyze(self, payload: WellnessAnalyzeRequest | None = None) -> WellnessAnalysisResponse:
        request = payload or self.default_request()
        messages = request.messages or self.default_request().messages
        typing_samples = request.typing_samples or self.default_request().typing_samples
        work_pattern = request.work_pattern or employee_dashboard_service.default_current()
        work_history = request.work_history or employee_dashboard_service.default_history(work_pattern)
        voice_payload = request.voice or self._voice_request(request, messages)

        nlp_batch = nlp_service.batch(
            NLPBatchRequest(
                messages=[
                    NLPAnalyzeRequest(
                        employee_id=request.employee_id,
                        department=request.department,
                        channel=message.channel,
                        text=message.text,
                    )
                    for message in messages
                ]
            )
        )
        voice = voice_stress_service.analyze(voice_payload)
        employee = employee_dashboard_service.analyze(
            EmployeeDashboardRequest(
                employee_id=request.employee_id,
                employee_name=request.employee_name,
                department=request.department,
                role=request.role,
                current=work_pattern,
                history=work_history,
            )
        )
        typing = self._typing_analytics(typing_samples)
        work = self._work_pattern_analytics(work_pattern, employee)
        summary = self._summary(nlp_batch, voice, employee, typing, work)
        heatmap = self._heatmap(request, summary)
        recommendations = self._recommendations(summary, typing, work, voice.recommendations, employee.recommendations)
        alerts = self._risk_alerts(summary, typing, work, nlp_batch, voice)
        insights = self._executive_insights(request, summary, heatmap, recommendations)
        response = WellnessAnalysisResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            employee_id=request.employee_id,
            employee_name=request.employee_name,
            department=request.department,
            role=request.role,
            nlp_model=nlp_batch.results[0].model if nlp_batch.results else "PyTorch TextEmotionNet",
            voice_model=voice.model,
            behavioral_model=self.behavioral_model,
            summary=summary.model_copy(update={"high_risk_team_count": sum(1 for cell in heatmap if cell.burnout_probability >= 70)}),
            sentiment_summary=self._sentiment_summary(nlp_batch),
            typing_analytics=typing,
            work_pattern_analytics=work,
            emotional_heatmap=heatmap,
            recommendations=recommendations,
            risk_alerts=alerts,
            executive_insights=insights,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: WellnessAnalyzeRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, stress_delta=0.12, negative_delta=0.08, overtime_delta=3.5),
            self._scenario_variant(base, stress_delta=0.24, negative_delta=0.18, overtime_delta=7.5),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: wellness\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> WellnessAnalyzeRequest:
        current = employee_dashboard_service.default_current()
        return WellnessAnalyzeRequest(
            employee_id="emp-wellness-001",
            employee_name="Aarav Mehta",
            department="Engineering",
            role="Senior Backend Engineer",
            messages=[
                WellnessMessage(text="I am exhausted and working late every night because the escalation keeps coming back.", channel="chat"),
                WellnessMessage(text="The handoff is unclear, the meeting load is heavy, and I am losing focus.", channel="email"),
                WellnessMessage(text="I want to help the team, but the sprint pressure is getting worse.", channel="slack"),
            ],
            voice=voice_stress_service.default_request(),
            work_pattern=current,
            work_history=employee_dashboard_service.default_history(current),
            typing_samples=[
                TypingTelemetryPoint(typing_speed_cpm=335, backspace_rate=0.18, error_rate=0.14, pause_ratio=0.38, burstiness=0.72, after_hours=True),
                TypingTelemetryPoint(typing_speed_cpm=318, backspace_rate=0.16, error_rate=0.11, pause_ratio=0.41, burstiness=0.68, after_hours=True),
                TypingTelemetryPoint(typing_speed_cpm=292, backspace_rate=0.14, error_rate=0.09, pause_ratio=0.34, burstiness=0.6),
            ],
            team_members=[
                WellnessTeamMember(employee_id="eng-1", name="Aarav Mehta", department="Engineering", stress_score=78, burnout_probability=72, sentiment_score=-0.45, meeting_hours=12, overtime_hours=14),
                WellnessTeamMember(employee_id="eng-2", name="Maya Iyer", department="Engineering", stress_score=64, burnout_probability=55, sentiment_score=-0.18, meeting_hours=9, overtime_hours=8),
                WellnessTeamMember(employee_id="cs-1", name="Rina Shah", department="Customer Success", stress_score=58, burnout_probability=49, sentiment_score=-0.12, meeting_hours=11, overtime_hours=5),
                WellnessTeamMember(employee_id="fin-1", name="Omar Khan", department="Finance", stress_score=34, burnout_probability=22, sentiment_score=0.25, meeting_hours=4, overtime_hours=2),
            ],
        )

    @staticmethod
    def _voice_request(request: WellnessAnalyzeRequest, messages: list[WellnessMessage]) -> VoiceStressAnalyzeRequest:
        transcript = " ".join(message.text for message in messages[:3])
        base = voice_stress_service.default_request()
        return base.model_copy(
            update={
                "employee_id": request.employee_id,
                "speaker": request.employee_name,
                "department": request.department,
                "transcript": transcript,
            }
        )

    @staticmethod
    def _typing_analytics(samples: list[TypingTelemetryPoint]) -> TypingBehaviorAnalytics:
        speeds = [sample.typing_speed_cpm for sample in samples]
        backspace = mean([sample.backspace_rate for sample in samples]) if samples else 0
        errors = mean([sample.error_rate for sample in samples]) if samples else 0
        pauses = mean([sample.pause_ratio for sample in samples]) if samples else 0
        burstiness = mean([sample.burstiness for sample in samples]) if samples else 0
        speed_instability = pstdev(speeds) / max(mean(speeds), 1) if len(speeds) > 1 else 0
        after_hours_ratio = sum(1 for sample in samples if sample.after_hours) / max(len(samples), 1)
        stress = np.clip(backspace * 155 + errors * 180 + pauses * 54 + burstiness * 38 + after_hours_ratio * 18 + speed_instability * 120, 0, 100)
        instability = np.clip(speed_instability * 180 + burstiness * 60 + pauses * 30, 0, 100)
        cognitive = np.clip(errors * 210 + pauses * 80 + after_hours_ratio * 20, 0, 100)
        fatigue = np.clip(pauses * 95 + after_hours_ratio * 28 + max(0, 280 - mean(speeds or [280])) * 0.08, 0, 100)
        aggressive = np.clip(backspace * 190 + burstiness * 70 + errors * 90, 0, 100)
        evidence = [
            f"backspace_rate={round(backspace, 3)}",
            f"error_rate={round(errors, 3)}",
            f"pause_ratio={round(pauses, 3)}",
            f"after_hours_ratio={round(after_hours_ratio, 2)}",
            f"speed_instability={round(speed_instability, 3)}",
        ]
        return TypingBehaviorAnalytics(
            stress_score=round(float(stress), 2),
            instability_score=round(float(instability), 2),
            cognitive_load_score=round(float(cognitive), 2),
            fatigue_score=round(float(fatigue), 2),
            aggressive_typing_score=round(float(aggressive), 2),
            evidence=evidence,
        )

    @staticmethod
    def _work_pattern_analytics(work_pattern, employee) -> WorkPatternWellnessAnalytics:
        overtime = min(100, work_pattern.overtime_hours * 5.2)
        meeting = min(100, work_pattern.meeting_hours * 6.4)
        productivity_decline = max(0, 1 - work_pattern.task_completion_ratio) * 100
        focus_deficit = max(0, 6 - work_pattern.focus_hours) / 6 * 100
        collaboration = max(0, 0.78 - work_pattern.collaboration_score) / 0.78 * 100
        forecast_pressure = round(mean([overtime, meeting, productivity_decline, focus_deficit, employee.burnout_probability.value]), 2)
        return WorkPatternWellnessAnalytics(
            overtime_pressure=round(overtime, 2),
            meeting_overload=round(meeting, 2),
            productivity_decline=round(productivity_decline, 2),
            focus_deficit=round(focus_deficit, 2),
            collaboration_risk=round(collaboration, 2),
            forecast=(
                f"Work-pattern wellness pressure is {forecast_pressure}%; overtime, meeting load, and focus deficit "
                "are the strongest near-term burnout accelerators."
            ),
        )

    @staticmethod
    def _summary(nlp_batch, voice, employee, typing: TypingBehaviorAnalytics, work: WorkPatternWellnessAnalytics) -> WellnessSummary:
        nlp_stress = mean([result.emotion_scores.stress for result in nlp_batch.results]) * 100 if nlp_batch.results else 0
        nlp_burnout = mean([result.emotion_scores.burnout for result in nlp_batch.results]) * 100 if nlp_batch.results else 0
        nlp_exhaustion = mean([result.emotion_scores.emotional_exhaustion for result in nlp_batch.results]) * 100 if nlp_batch.results else 0
        nlp_frustration = mean([result.emotion_scores.frustration for result in nlp_batch.results]) * 100 if nlp_batch.results else 0
        nlp_motivation = mean([result.emotion_scores.motivation for result in nlp_batch.results]) * 100 if nlp_batch.results else 50
        stress = np.clip(nlp_stress * 0.28 + voice.stress_score * 0.24 + employee.stress.value * 0.24 + typing.stress_score * 0.14 + work.overtime_pressure * 0.1, 0, 100)
        burnout = np.clip(employee.burnout_probability.value * 0.34 + voice.burnout_risk * 0.24 + nlp_burnout * 0.22 + typing.fatigue_score * 0.1 + work.meeting_overload * 0.1, 0, 100)
        exhaustion = np.clip(nlp_exhaustion * 0.36 + voice.emotion_scores.fatigue * 100 * 0.24 + burnout * 0.2 + typing.fatigue_score * 0.12 + work.focus_deficit * 0.08, 0, 100)
        frustration = np.clip(nlp_frustration * 0.42 + voice.emotion_scores.frustration * 100 * 0.26 + typing.aggressive_typing_score * 0.18 + voice.conflict_intensity * 0.14, 0, 100)
        anxiety = np.clip(voice.emotion_scores.anxiety * 100 * 0.42 + nlp_stress * 0.26 + typing.instability_score * 0.18 + work.overtime_pressure * 0.14, 0, 100)
        motivation_decline = np.clip((100 - nlp_motivation) * 0.46 + max(0, 78 - employee.productivity.value) * 0.34 + work.focus_deficit * 0.2, 0, 100)
        communication_fatigue = np.clip(voice.communication_pressure * 0.32 + work.meeting_overload * 0.26 + typing.cognitive_load_score * 0.18 + max(0, -nlp_batch.team_sentiment_score) * 100 * 0.24, 0, 100)
        overload = np.clip(stress * 0.24 + burnout * 0.25 + exhaustion * 0.19 + work.overtime_pressure * 0.14 + work.meeting_overload * 0.1 + typing.cognitive_load_score * 0.08, 0, 100)
        wellness = np.clip(100 - stress * 0.18 - burnout * 0.22 - exhaustion * 0.18 - frustration * 0.1 - anxiety * 0.1 - communication_fatigue * 0.1 - overload * 0.12, 0, 100)
        return WellnessSummary(
            wellness_score=round(float(wellness), 2),
            stress_score=round(float(stress), 2),
            burnout_probability=round(float(burnout), 2),
            emotional_exhaustion_probability=round(float(exhaustion), 2),
            frustration_score=round(float(frustration), 2),
            anxiety_score=round(float(anxiety), 2),
            motivation_decline=round(float(motivation_decline), 2),
            communication_fatigue=round(float(communication_fatigue), 2),
            mental_overload=round(float(overload), 2),
            high_risk_team_count=0,
        )

    @staticmethod
    def _heatmap(request: WellnessAnalyzeRequest, summary: WellnessSummary) -> list[WellnessHeatmapCell]:
        members = request.team_members or WellnessIntelligenceService.default_request().team_members
        grouped: dict[str, list[WellnessTeamMember]] = defaultdict(list)
        for member in members:
            grouped[member.department].append(member)
        cells = []
        for department, rows in grouped.items():
            stress = mean([row.stress_score for row in rows])
            burnout = mean([row.burnout_probability for row in rows])
            sentiment = mean([row.sentiment_score for row in rows])
            meeting = mean([row.meeting_hours for row in rows])
            overtime = mean([row.overtime_hours for row in rows])
            exhaustion = np.clip(stress * 0.38 + burnout * 0.34 + meeting * 1.4 + overtime * 1.1 + max(0, -sentiment) * 28, 0, 100)
            morale = np.clip(72 + sentiment * 28 - burnout * 0.22 - stress * 0.14, 0, 100)
            recommendation = "Maintain current cadence."
            if burnout >= 68 or exhaustion >= 70:
                recommendation = "Reduce workload, protect focus blocks, and schedule manager wellness check-ins."
            elif meeting >= 10:
                recommendation = "Move recurring updates async and lower meeting density."
            cells.append(
                WellnessHeatmapCell(
                    department=department,
                    stress_score=round(float(stress), 2),
                    burnout_probability=round(float(burnout), 2),
                    emotional_exhaustion=round(float(exhaustion), 2),
                    morale_score=round(float(morale), 2),
                    headcount=len(rows),
                    recommendation=recommendation,
                )
            )
        if request.department not in grouped:
            cells.append(
                WellnessHeatmapCell(
                    department=request.department,
                    stress_score=summary.stress_score,
                    burnout_probability=summary.burnout_probability,
                    emotional_exhaustion=summary.emotional_exhaustion_probability,
                    morale_score=max(0, 100 - summary.mental_overload),
                    headcount=1,
                    recommendation="Immediate individual wellness intervention recommended." if summary.burnout_probability >= 70 else "Continue monitoring individual wellness.",
                )
            )
        return sorted(cells, key=lambda cell: cell.emotional_exhaustion, reverse=True)

    @staticmethod
    def _sentiment_summary(nlp_batch) -> dict[str, float | int | str]:
        if not nlp_batch.results:
            return {"average_sentiment": 0.0, "messages_analyzed": 0, "dominant_emotion": "neutral", "high_risk_messages": 0}
        emotion_totals = defaultdict(float)
        for result in nlp_batch.results:
            for label, value in result.emotion_scores.model_dump().items():
                emotion_totals[label] += float(value)
        dominant = max(emotion_totals, key=emotion_totals.get)
        return {
            "average_sentiment": round(nlp_batch.team_sentiment_score, 3),
            "messages_analyzed": len(nlp_batch.results),
            "dominant_emotion": dominant,
            "high_risk_messages": nlp_batch.high_risk_count,
        }

    @staticmethod
    def _recommendations(summary: WellnessSummary, typing: TypingBehaviorAnalytics, work: WorkPatternWellnessAnalytics, voice_recommendations: list[str], employee_recommendations: list[str]) -> list[WellnessRecommendation]:
        recommendations: list[WellnessRecommendation] = []
        if summary.burnout_probability >= 76 or summary.emotional_exhaustion_probability >= 78:
            leave_days = 3 if summary.burnout_probability >= 86 else 2
            recommendations.append(
                WellnessRecommendation(
                    category="recovery_leave",
                    priority="critical" if summary.burnout_probability >= 86 else "high",
                    action=f"Recommend {leave_days}-day recovery leave and remove escalation ownership for the next sprint.",
                    expected_impact=f"Expected to reduce emotional exhaustion by {round(summary.emotional_exhaustion_probability * 0.22)}%.",
                    confidence=0.91,
                )
            )
        if summary.stress_score >= 62 or work.overtime_pressure >= 58:
            reduction = min(28, max(12, round(summary.stress_score * 0.23)))
            recommendations.append(
                WellnessRecommendation(
                    category="workload_reduction",
                    priority="high" if summary.stress_score >= 72 else "medium",
                    action=f"Reduce workload by {reduction}% and move deadline-critical overflow to backup owners.",
                    expected_impact=f"Expected stress reduction of {round(reduction * 0.7)}% within one sprint.",
                    confidence=0.88,
                )
            )
        if work.meeting_overload >= 55 or summary.communication_fatigue >= 55:
            recommendations.append(
                WellnessRecommendation(
                    category="meeting_reduction",
                    priority="medium",
                    action="Cancel low-signal recurring meetings for 5 business days and convert status updates to async notes.",
                    expected_impact="Restores focus time and reduces communication fatigue.",
                    confidence=0.86,
                )
            )
        if typing.cognitive_load_score >= 48:
            recommendations.append(
                WellnessRecommendation(
                    category="typing_behavior",
                    priority="medium",
                    action="Insert protected focus blocks after high-error typing sessions and pause urgent written escalations.",
                    expected_impact="Reduces cognitive load and message rework risk.",
                    confidence=0.82,
                )
            )
        for item in [*voice_recommendations, *employee_recommendations]:
            recommendations.append(
                WellnessRecommendation(
                    category="model_fusion",
                    priority="medium",
                    action=item,
                    expected_impact="Cross-model intervention grounded in voice, NLP, and work-pattern signals.",
                    confidence=0.79,
                )
            )
        if not recommendations:
            recommendations.append(
                WellnessRecommendation(
                    category="monitoring",
                    priority="low",
                    action="Maintain current workload and continue passive emotional telemetry monitoring.",
                    expected_impact="Keeps wellness baseline stable.",
                    confidence=0.76,
                )
            )
        return recommendations[:7]

    @staticmethod
    def _risk_alerts(summary: WellnessSummary, typing: TypingBehaviorAnalytics, work: WorkPatternWellnessAnalytics, nlp_batch, voice) -> list[WellnessRiskAlert]:
        alerts = [
            WellnessIntelligenceService._alert("stress", summary.stress_score, ["NLP stress", "voice stress", "workload escalation"], "Reduce deadline pressure and create recovery capacity."),
            WellnessIntelligenceService._alert("burnout", summary.burnout_probability, ["burnout ensemble", "voice fatigue", "message exhaustion"], "Trigger manager wellness check-in and rebalance urgent ownership."),
            WellnessIntelligenceService._alert("emotional_exhaustion", summary.emotional_exhaustion_probability, ["fatigue", "late work", "focus deficit"], "Recommend recovery leave if exhaustion remains elevated for 48 hours."),
            WellnessIntelligenceService._alert("typing_instability", typing.instability_score, typing.evidence, "Pause urgent written escalation and add a focus reset."),
            WellnessIntelligenceService._alert("communication_fatigue", summary.communication_fatigue, [f"team_sentiment={nlp_batch.team_sentiment_score}", f"voice_pressure={voice.communication_pressure}"], "Reduce live meeting pressure and move updates async."),
            WellnessIntelligenceService._alert("work_pattern_overload", max(work.overtime_pressure, work.meeting_overload), [work.forecast], "Reduce overtime and meeting load this week."),
        ]
        return [alert for alert in alerts if alert.score >= 34]

    @staticmethod
    def _alert(category: str, score: float, evidence: list[str], recommendation: str) -> WellnessRiskAlert:
        if score >= 82:
            severity = "critical"
        elif score >= 66:
            severity = "high"
        elif score >= 46:
            severity = "medium"
        else:
            severity = "low"
        return WellnessRiskAlert(
            category=category,
            severity=severity,
            score=round(float(np.clip(score, 0, 100)), 2),
            message=f"{category.replace('_', ' ').title()} signal is {round(score)}%.",
            evidence=evidence[:5],
            recommendation=recommendation,
        )

    @staticmethod
    def _executive_insights(request: WellnessAnalyzeRequest, summary: WellnessSummary, heatmap: list[WellnessHeatmapCell], recommendations: list[WellnessRecommendation]) -> list[str]:
        highest = heatmap[0] if heatmap else None
        insights = [
            f"{request.employee_name} wellness score is {round(summary.wellness_score)} with burnout probability {round(summary.burnout_probability)}%.",
            f"Stress is driven by mental overload {round(summary.mental_overload)}%, communication fatigue {round(summary.communication_fatigue)}%, and exhaustion {round(summary.emotional_exhaustion_probability)}%.",
        ]
        if highest:
            insights.append(f"{highest.department} is the highest emotional heatmap zone at {round(highest.emotional_exhaustion)}% exhaustion risk.")
        if recommendations:
            insights.append(f"Top intervention: {recommendations[0].action}")
        return insights

    @staticmethod
    def _scenario_variant(base: WellnessAnalyzeRequest, stress_delta: float, negative_delta: float, overtime_delta: float) -> WellnessAnalyzeRequest:
        messages = [
            message.model_copy(update={"text": f"{message.text} Stress pressure increased by {round(stress_delta * 100)}% and recovery time is shrinking."})
            for message in (base.messages or WellnessIntelligenceService.default_request().messages)
        ]
        typing = [
            sample.model_copy(
                update={
                    "backspace_rate": min(1, sample.backspace_rate + negative_delta),
                    "error_rate": min(1, sample.error_rate + negative_delta * 0.7),
                    "pause_ratio": min(1, sample.pause_ratio + stress_delta * 0.4),
                    "burstiness": min(1, sample.burstiness + stress_delta * 0.36),
                    "after_hours": True,
                }
            )
            for sample in (base.typing_samples or WellnessIntelligenceService.default_request().typing_samples)
        ]
        work = (base.work_pattern or employee_dashboard_service.default_current()).model_copy(
            update={
                "overtime_hours": min(40, (base.work_pattern or employee_dashboard_service.default_current()).overtime_hours + overtime_delta),
                "meeting_hours": min(24, (base.work_pattern or employee_dashboard_service.default_current()).meeting_hours + stress_delta * 8),
                "sentiment_score": max(-1, (base.work_pattern or employee_dashboard_service.default_current()).sentiment_score - negative_delta),
                "task_completion_ratio": max(0, (base.work_pattern or employee_dashboard_service.default_current()).task_completion_ratio - stress_delta * 0.18),
                "focus_hours": max(0, (base.work_pattern or employee_dashboard_service.default_current()).focus_hours - stress_delta * 2.2),
                "negative_message_ratio": min(1, (base.work_pattern or employee_dashboard_service.default_current()).negative_message_ratio + negative_delta),
            }
        )
        return base.model_copy(update={"messages": messages, "typing_samples": typing, "work_pattern": work, "realtime": True})

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


wellness_intelligence_service = WellnessIntelligenceService()
