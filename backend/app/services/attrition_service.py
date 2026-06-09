from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

import numpy as np

from app.ai.attrition_engine import attrition_forecasting_engine
from app.schemas.attrition import (
    AttritionAnalyzeRequest,
    AttritionEmployeeInput,
    AttritionFeatureAttribution,
    AttritionForecastPoint,
    AttritionPrediction,
    AttritionRecommendation,
    AttritionResponse,
    AttritionRiskLevel,
    AttritionSummary,
    TeamAttritionTrend,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "attrition_predictions.jsonl"


class AttritionPredictionService:
    model_name = "RandomForest/XGBoost Attrition Forecasting Engine"

    def __init__(self) -> None:
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def analyze(self, payload: AttritionAnalyzeRequest | None = None) -> AttritionResponse:
        request = payload or self.default_request()
        if not request.employees:
            request = request.model_copy(update={"employees": self.default_request().employees})
        predictions = [self._prediction(employee, request.horizon_days, request.sensitivity) for employee in request.employees]
        ordered = sorted(predictions, key=lambda item: item.resignation_probability, reverse=True)
        recommendations = self._portfolio_recommendations(ordered)
        response = AttritionResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            horizon_days=request.horizon_days,
            predictions=ordered,
            team_trends=self._team_trends(ordered),
            heatmap=self._heatmap(ordered),
            recommendations=recommendations,
            summary=self._summary(ordered),
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: AttritionAnalyzeRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, stress_delta=0.07, sentiment_delta=-0.08, satisfaction_delta=-0.05),
            self._scenario_variant(base, stress_delta=0.15, sentiment_delta=-0.18, satisfaction_delta=-0.1),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: attrition\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> AttritionAnalyzeRequest:
        minute_wave = datetime.now(timezone.utc).minute % 7
        drift = minute_wave / 100
        return AttritionAnalyzeRequest(
            horizon_days=90,
            sensitivity=0.64,
            employees=[
                AttritionEmployeeInput(
                    employee_id="emp-john",
                    employee_name="Employee John",
                    department="Engineering",
                    team_name="Development Team",
                    role="Backend Lead",
                    burnout_score=87 + minute_wave * 0.4,
                    productivity_score=48 - minute_wave * 0.3,
                    productivity_trend=-0.46 - drift,
                    overtime_hours_30d=82 + minute_wave,
                    meeting_hours_weekly=18 + minute_wave * 0.2,
                    salary_satisfaction=0.42,
                    sentiment_score=-0.62,
                    manager_compatibility=0.48,
                    team_stress=0.86,
                    promotion_delay_months=28,
                    work_life_balance=0.32,
                    attendance_rate=0.82,
                    absences_90d=8,
                    tenure_months=34,
                    knowledge_criticality=0.96,
                    annual_salary=178000,
                    billable_revenue_per_day=3600,
                ),
                AttritionEmployeeInput(
                    employee_id="emp-nina",
                    employee_name="Employee Nina",
                    department="Engineering",
                    team_name="Development Team",
                    role="Senior Frontend Engineer",
                    burnout_score=73 + minute_wave * 0.25,
                    productivity_score=61,
                    productivity_trend=-0.28,
                    overtime_hours_30d=56,
                    meeting_hours_weekly=14,
                    salary_satisfaction=0.55,
                    sentiment_score=-0.31,
                    manager_compatibility=0.58,
                    team_stress=0.72,
                    promotion_delay_months=18,
                    work_life_balance=0.46,
                    attendance_rate=0.89,
                    absences_90d=5,
                    tenure_months=22,
                    knowledge_criticality=0.74,
                    annual_salary=142000,
                    billable_revenue_per_day=2300,
                ),
                AttritionEmployeeInput(
                    employee_id="emp-bianca",
                    employee_name="Bianca Shah",
                    department="Platform",
                    team_name="Platform Reliability",
                    role="SRE Manager",
                    burnout_score=54,
                    productivity_score=78,
                    productivity_trend=-0.08,
                    overtime_hours_30d=31,
                    meeting_hours_weekly=12,
                    salary_satisfaction=0.71,
                    sentiment_score=0.16,
                    manager_compatibility=0.77,
                    team_stress=0.5,
                    promotion_delay_months=9,
                    work_life_balance=0.62,
                    attendance_rate=0.95,
                    absences_90d=2,
                    tenure_months=46,
                    knowledge_criticality=0.82,
                    annual_salary=168000,
                    billable_revenue_per_day=2600,
                ),
                AttritionEmployeeInput(
                    employee_id="emp-maya",
                    employee_name="Maya Iyer",
                    department="Operations",
                    team_name="Automation Team",
                    role="Automation Analyst",
                    burnout_score=24,
                    productivity_score=91,
                    productivity_trend=0.18,
                    overtime_hours_30d=9,
                    meeting_hours_weekly=5,
                    salary_satisfaction=0.84,
                    sentiment_score=0.52,
                    manager_compatibility=0.88,
                    team_stress=0.22,
                    promotion_delay_months=4,
                    work_life_balance=0.82,
                    attendance_rate=0.99,
                    absences_90d=0,
                    tenure_months=30,
                    knowledge_criticality=0.47,
                    annual_salary=116000,
                    billable_revenue_per_day=1500,
                ),
            ],
        )

    def _prediction(self, employee: AttritionEmployeeInput, horizon_days: int, sensitivity: float) -> AttritionPrediction:
        probabilities = attrition_forecasting_engine.predict(employee)
        risk_pressure = self._risk_pressure(employee)
        pressure_probability = self._sigmoid((risk_pressure - 0.48) * 5.3)
        horizon_lift = min(0.08, max(0, (horizon_days - 90) / 365 * 0.12))
        adjusted_probability = np.clip(
            probabilities["ensemble"] * 0.58 + pressure_probability * 0.42 + horizon_lift + (sensitivity - 0.5) * 0.08,
            0,
            0.98,
        )
        resignation_probability = round(float(adjusted_probability * 100), 2)
        feature_attributions = self._feature_attributions(employee)
        confidence = round(float(np.clip(0.64 + probabilities["random_forest"] * 0.12 + probabilities["xgboost"] * 0.12 + len(feature_attributions) * 0.008, 0.6, 0.96)), 3)
        primary_reasons = [item.evidence for item in feature_attributions if item.direction == "increases_attrition"][:4]
        recommended_interventions = self._interventions(employee, feature_attributions)
        return AttritionPrediction(
            employee_id=employee.employee_id,
            employee_name=employee.employee_name,
            department=employee.department,
            team_name=employee.team_name,
            role=employee.role,
            resignation_probability=resignation_probability,
            confidence=confidence,
            risk_level=self._risk_level(resignation_probability),
            estimated_departure_window=self._departure_window(resignation_probability),
            primary_reasons=primary_reasons or ["Attrition risk is currently contained by stable engagement signals."],
            feature_attributions=feature_attributions,
            burnout_correlation_multiplier=round(1 + employee.burnout_score / 100 * 2.2 + employee.team_stress * 0.62, 2),
            replacement_cost_exposure=self._replacement_exposure(employee, adjusted_probability),
            recommended_interventions=recommended_interventions,
            model_probabilities=probabilities,
            forecast=self._forecast(employee, horizon_days, adjusted_probability),
        )

    def _feature_attributions(self, employee: AttritionEmployeeInput) -> list[AttritionFeatureAttribution]:
        importance = attrition_forecasting_engine.feature_importance()
        drivers = {
            "burnout_score": (employee.burnout_score, employee.burnout_score / 100, "Burnout pressure is elevated."),
            "productivity_score": (employee.productivity_score, (100 - employee.productivity_score) / 100, "Productivity decline is increasing resignation risk."),
            "productivity_trend": (employee.productivity_trend, max(0, -employee.productivity_trend), "Productivity trend is deteriorating."),
            "overtime_hours_30d": (employee.overtime_hours_30d, min(employee.overtime_hours_30d / 90, 1), "Overtime escalation is above the retention safety band."),
            "meeting_hours_weekly": (employee.meeting_hours_weekly, min(employee.meeting_hours_weekly / 28, 1), "Meeting load is reducing focus recovery time."),
            "salary_satisfaction": (employee.salary_satisfaction, 1 - employee.salary_satisfaction, "Compensation satisfaction is below retention threshold."),
            "sentiment_score": (employee.sentiment_score, max(0, -employee.sentiment_score), "Communication sentiment is negative."),
            "manager_compatibility": (employee.manager_compatibility, 1 - employee.manager_compatibility, "Manager compatibility is weakening engagement."),
            "team_stress": (employee.team_stress, employee.team_stress, "Team stress can propagate resignation intent."),
            "promotion_delay_months": (float(employee.promotion_delay_months), min(employee.promotion_delay_months / 30, 1), "Promotion delay is creating career stagnation pressure."),
            "work_life_balance": (employee.work_life_balance, 1 - employee.work_life_balance, "Work-life balance is below healthy operating range."),
            "attendance_rate": (employee.attendance_rate, 1 - employee.attendance_rate, "Availability reliability drift suggests disengagement."),
            "absences_90d": (employee.absences_90d, min(employee.absences_90d / 14, 1), "Absence pressure is higher than normal."),
            "tenure_months": (float(employee.tenure_months), max(0, 18 - employee.tenure_months) / 18, "Early tenure risk is active."),
            "knowledge_criticality": (employee.knowledge_criticality, employee.knowledge_criticality * 0.22, "Knowledge criticality increases business exposure if resignation occurs."),
        }
        attributions: list[AttritionFeatureAttribution] = []
        for feature, (value, pressure, evidence) in drivers.items():
            weight = importance.get(feature, 0.04)
            contribution = round(float(np.clip(pressure * weight * 100 * 2.4, 0, 100)), 2)
            if contribution >= 5:
                direction = "increases_attrition"
            elif pressure <= 0.18:
                direction = "reduces_attrition"
                contribution = round(float(np.clip((0.18 - pressure) * weight * 100 * 1.8, 0, 100)), 2)
            else:
                direction = "neutral"
            attributions.append(
                AttritionFeatureAttribution(
                    feature=feature,
                    value=round(float(value), 3),
                    contribution=contribution,
                    direction=direction,
                    evidence=evidence if direction == "increases_attrition" else f"{feature.replace('_', ' ').title()} is within a safer band.",
                )
            )
        return sorted(attributions, key=lambda item: item.contribution, reverse=True)[:8]

    def _forecast(self, employee: AttritionEmployeeInput, horizon_days: int, base_probability: float) -> list[AttritionForecastPoint]:
        points: list[AttritionForecastPoint] = []
        for day in sorted(set([15, 30, 45, 60, 90, horizon_days])):
            if day > horizon_days:
                continue
            pressure = day / max(horizon_days, 1)
            growth = (
                employee.team_stress * 0.07
                + max(0, -employee.productivity_trend) * 0.05
                + min(employee.overtime_hours_30d / 100, 1) * 0.04
                + max(0, -employee.sentiment_score) * 0.04
            ) * pressure
            probability = float(np.clip(base_probability + growth, 0, 0.99))
            points.append(
                AttritionForecastPoint(
                    day=day,
                    resignation_probability=round(probability * 100, 2),
                    workforce_stability=round((1 - probability) * 100, 2),
                )
            )
        return points

    def _portfolio_recommendations(self, predictions: list[AttritionPrediction]) -> list[AttritionRecommendation]:
        if not predictions:
            return []
        high_risk = [prediction for prediction in predictions if prediction.resignation_probability >= 60]
        top = predictions[0]
        recommendations = [
            AttritionRecommendation(
                recommendation_id="attrition-retention-review",
                category="retention_intervention",
                title="Open targeted retention review",
                action=f"Run a manager, compensation, and workload intervention for {top.employee_name} within 7 days.",
                rationale=f"{top.employee_name} is carrying {round(top.resignation_probability)}% resignation probability with ${round(top.replacement_cost_exposure):,} expected exposure.",
                impact_score=round(min(100, top.resignation_probability + 14), 2),
                confidence=top.confidence,
                affected_employees=[top.employee_id],
                evidence=top.primary_reasons[:3],
            )
        ]
        overloaded = [prediction for prediction in predictions if any("Overtime" in reason or "Meeting" in reason for reason in prediction.primary_reasons)]
        if overloaded:
            recommendations.append(
                AttritionRecommendation(
                    recommendation_id="attrition-workload-reset",
                    category="workload_reduction",
                    title="Reduce burnout-driven resignation pressure",
                    action="Cut recurring meetings by 15-20% and redistribute incident ownership for high-risk employees.",
                    rationale=f"{len(overloaded)} employee(s) show workload or meeting overload as a top attrition driver.",
                    impact_score=round(mean(item.resignation_probability for item in overloaded), 2),
                    confidence=round(mean(item.confidence for item in overloaded), 3),
                    affected_employees=[item.employee_id for item in overloaded],
                    evidence=[item.primary_reasons[0] for item in overloaded if item.primary_reasons],
                )
            )
        if high_risk:
            recommendations.append(
                AttritionRecommendation(
                    recommendation_id="attrition-knowledge-shield",
                    category="knowledge_loss_prevention",
                    title="Protect critical knowledge before resignation risk materializes",
                    action="Generate SOPs and pair critical owners with backup engineers for the next sprint.",
                    rationale="High attrition probability combined with knowledge criticality creates delivery continuity exposure.",
                    impact_score=round(float(np.clip(mean(item.replacement_cost_exposure for item in high_risk) / 5000, 0, 100)), 2),
                    confidence=round(mean(item.confidence for item in high_risk), 3),
                    affected_employees=[item.employee_id for item in high_risk],
                    evidence=[f"{item.employee_name}: ${round(item.replacement_cost_exposure):,} exposure" for item in high_risk],
                )
            )
        return sorted(recommendations, key=lambda item: item.impact_score, reverse=True)[:5]

    @staticmethod
    def _interventions(employee: AttritionEmployeeInput, attributions: list[AttritionFeatureAttribution]) -> list[str]:
        features = {item.feature for item in attributions if item.direction == "increases_attrition"}
        interventions: list[str] = []
        if {"overtime_hours_30d", "work_life_balance", "burnout_score"}.intersection(features):
            interventions.append(f"Reduce {employee.employee_name}'s critical workload by 15% and add recovery capacity this sprint.")
        if "meeting_hours_weekly" in features:
            interventions.append(f"Reduce recurring meetings for {employee.employee_name} by 20% and protect two focus blocks weekly.")
        if "salary_satisfaction" in features:
            interventions.append(f"Open compensation and retention-bonus review for {employee.employee_name}.")
        if "promotion_delay_months" in features:
            interventions.append(f"Schedule promotion-path conversation with clear 60-day milestones for {employee.employee_name}.")
        if "manager_compatibility" in features:
            interventions.append(f"Add skip-level coaching or manager reassignment review for {employee.employee_name}.")
        if "sentiment_score" in features or "team_stress" in features:
            interventions.append(f"Run a team morale reset for {employee.team_name} and resolve the top communication blockers.")
        if not interventions:
            interventions.append(f"Maintain retention check-ins for {employee.employee_name} and monitor trend drift weekly.")
        return interventions[:5]

    @staticmethod
    def _team_trends(predictions: list[AttritionPrediction]) -> list[TeamAttritionTrend]:
        groups: dict[tuple[str, str], list[AttritionPrediction]] = defaultdict(list)
        for prediction in predictions:
            groups[(prediction.team_name, prediction.department)].append(prediction)
        trends: list[TeamAttritionTrend] = []
        for (team_name, department), members in groups.items():
            average = mean(member.resignation_probability for member in members)
            high_risk = sum(1 for member in members if member.resignation_probability >= 60)
            critical = sum(1 for member in members if member.resignation_probability >= 80)
            chain = min(100, average * 0.58 + high_risk * 14 + critical * 9)
            if average >= 78 or critical:
                morale = "critical"
            elif average >= 62:
                morale = "unstable"
            elif average >= 38:
                morale = "watch"
            else:
                morale = "stable"
            trends.append(
                TeamAttritionTrend(
                    team_name=team_name,
                    department=department,
                    employees_analyzed=len(members),
                    average_attrition_probability=round(average, 2),
                    high_risk_count=high_risk,
                    turnover_pressure=round(min(100, average + high_risk * 8), 2),
                    chain_reaction_risk=round(chain, 2),
                    morale_signal=morale,
                    recommendation=f"Prioritize retention actions for {team_name}." if high_risk else f"Keep {team_name} on normal retention watch.",
                )
            )
        return sorted(trends, key=lambda item: item.turnover_pressure, reverse=True)

    @staticmethod
    def _heatmap(predictions: list[AttritionPrediction]) -> list[dict[str, float | str]]:
        return [
            {
                "employee": item.employee_name,
                "team": item.team_name,
                "department": item.department,
                "attrition": item.resignation_probability,
                "stability": round(100 - item.resignation_probability, 2),
                "cost_exposure": item.replacement_cost_exposure,
                "burnout_multiplier": item.burnout_correlation_multiplier,
            }
            for item in predictions
        ]

    @staticmethod
    def _summary(predictions: list[AttritionPrediction]) -> AttritionSummary:
        top = predictions[0] if predictions else None
        average = mean(item.resignation_probability for item in predictions) if predictions else 0
        return AttritionSummary(
            employees_analyzed=len(predictions),
            average_resignation_probability=round(average, 2),
            high_risk_employees=sum(1 for item in predictions if item.resignation_probability >= 60),
            critical_risk_employees=sum(1 for item in predictions if item.resignation_probability >= 80),
            workforce_stability_score=round(max(0, 100 - average), 2),
            top_risk_employee=top.employee_name if top else "n/a",
            estimated_replacement_exposure=round(sum(item.replacement_cost_exposure for item in predictions), 2),
        )

    @staticmethod
    def _scenario_variant(
        base: AttritionAnalyzeRequest,
        stress_delta: float,
        sentiment_delta: float,
        satisfaction_delta: float,
    ) -> AttritionAnalyzeRequest:
        employees = []
        for employee in base.employees or AttritionPredictionService.default_request().employees:
            employees.append(
                employee.model_copy(
                    update={
                        "burnout_score": AttritionPredictionService._clip100(employee.burnout_score + stress_delta * 100),
                        "productivity_score": AttritionPredictionService._clip100(employee.productivity_score - stress_delta * 30),
                        "productivity_trend": float(np.clip(employee.productivity_trend - stress_delta * 0.3, -1, 1)),
                        "overtime_hours_30d": min(240, employee.overtime_hours_30d + stress_delta * 42),
                        "meeting_hours_weekly": min(80, employee.meeting_hours_weekly + stress_delta * 9),
                        "salary_satisfaction": AttritionPredictionService._clip01(employee.salary_satisfaction + satisfaction_delta),
                        "sentiment_score": float(np.clip(employee.sentiment_score + sentiment_delta, -1, 1)),
                        "manager_compatibility": AttritionPredictionService._clip01(employee.manager_compatibility - stress_delta * 0.18),
                        "team_stress": AttritionPredictionService._clip01(employee.team_stress + stress_delta),
                        "work_life_balance": AttritionPredictionService._clip01(employee.work_life_balance - stress_delta * 0.22),
                        "attendance_rate": AttritionPredictionService._clip01(employee.attendance_rate - stress_delta * 0.08),
                        "absences_90d": min(60, employee.absences_90d + stress_delta * 8),
                    }
                )
            )
        return base.model_copy(update={"employees": employees, "realtime": True})

    @staticmethod
    def _risk_pressure(employee: AttritionEmployeeInput) -> float:
        components = attrition_forecasting_engine.risk_components(employee)
        weights = {
            "burnout_score": 1.32,
            "productivity_decline": 0.85,
            "overtime_escalation": 0.95,
            "meeting_overload": 0.58,
            "salary_dissatisfaction": 1.12,
            "negative_sentiment": 0.92,
            "manager_misalignment": 0.94,
            "team_stress": 0.86,
            "promotion_delay": 0.88,
            "work_life_imbalance": 0.9,
            "attendance_change": 0.62,
            "absence_pressure": 0.55,
            "early_tenure_pressure": 0.38,
            "knowledge_loss_impact": 0.18,
        }
        return sum(components[name] * weight for name, weight in weights.items()) / sum(weights.values())

    @staticmethod
    def _replacement_exposure(employee: AttritionEmployeeInput, probability: float) -> float:
        hiring = employee.annual_salary * 0.22
        training = employee.annual_salary * (0.12 + employee.knowledge_criticality * 0.13)
        recovery = employee.annual_salary * (0.14 + (1 - employee.productivity_score / 100) * 0.2)
        knowledge = employee.annual_salary * employee.knowledge_criticality * 0.62
        disruption = employee.billable_revenue_per_day * (18 + employee.team_stress * 24)
        return round((hiring + training + recovery + knowledge + disruption) * float(probability), 2)

    @staticmethod
    def _risk_level(probability: float) -> AttritionRiskLevel:
        if probability >= 80:
            return "critical"
        if probability >= 60:
            return "high"
        if probability >= 36:
            return "medium"
        return "low"

    @staticmethod
    def _departure_window(probability: float) -> str:
        if probability >= 82:
            return "0-30 days"
        if probability >= 68:
            return "31-60 days"
        if probability >= 48:
            return "61-90 days"
        return "90+ days"

    @staticmethod
    def _sigmoid(value: float) -> float:
        return float(1 / (1 + np.exp(-value)))

    @staticmethod
    def _clip01(value: float) -> float:
        return float(np.clip(value, 0, 1))

    @staticmethod
    def _clip100(value: float) -> float:
        return float(np.clip(value, 0, 100))

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


attrition_prediction_service = AttritionPredictionService()
