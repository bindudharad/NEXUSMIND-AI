from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

from app.core.cache import TTLResponseCache
from app.schemas.company_emotion_map import (
    BurnoutPrediction,
    CompanyEmotionMapRequest,
    CompanyEmotionMapResponse,
    CompanyEmotionMapSummary,
    ConflictRiskInsight,
    DepartmentEmotionScore,
    EmployeeEmotionScore,
    EmployeeEmotionSignal,
    EmotionAssistantIntent,
    EmotionAssistantRequest,
    EmotionAssistantResponse,
    Emotion3DNode,
    EmotionAgentContribution,
    EmotionDataPipelineStatus,
    EmotionForecastPoint,
    EmotionHealthStatus,
    EmotionHeatmapZone,
    EmotionHeatmapPoint,
    EmotionMetric,
    EmotionPriority,
    EmotionRecommendation,
    EmotionScope,
    EmotionTextSignal,
    SilentEmployeeRisk,
    TeamEmotionClassification,
    MotivationTrend,
    TeamEmotionScore,
    TeamInteractionSignal,
)
from app.schemas.nlp import NLPAnalyzeRequest
from app.services.nlp_service import nlp_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "company_emotion_map_history.jsonl"


class CompanyEmotionMapService:
    model_name = "Company Emotion Digital Twin + NLP Forecasting Engine"
    source_systems = [
        "emotion_analytics_engine",
        "emotion_intelligence_engine",
        "emotion_data_pipeline",
        "privacy_permission_filter",
        "sentiment_analysis_engine",
        "burnout_prediction_engine",
        "team_health_engine",
        "workforce_stress_engine",
        "conflict_detection_engine",
        "toxic_team_detection_engine",
        "team_happiness_engine",
        "silent_employee_engine",
        "motivation_analysis_engine",
        "engagement_intelligence_engine",
        "organizational_heatmap_engine",
        "workforce_health_heatmap_ui",
        "emotion_color_engine",
        "realtime_emotion_stream",
        "three_d_emotion_visualization_engine",
        "emotion_dashboard",
        "emotion_ai_assistant",
        "emotion_intelligence_council",
        "employee_digital_twin",
        "team_digital_twin",
        "department_digital_twin",
        "company_digital_twin",
        "company_time_machine",
        "workforce_simulator",
        "what_if_emotion_scenario_engine",
        "executive_dashboard",
        "ceo_dashboard",
        "crisis_dashboard",
        "alert_system",
        "multi_agent_workforce",
        "workflow_automation",
        "xgboost_emotion_forecaster",
        "random_forest_burnout_predictor",
        "lstm_morale_sequence_model",
        "prophet_workforce_sentiment_forecaster",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[CompanyEmotionMapResponse] = TTLResponseCache(ttl_seconds=8)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def default(self) -> CompanyEmotionMapResponse:
        return self._cache.get_or_set(lambda: self.analyze(self.default_request(), persist=True))

    def analyze(self, payload: CompanyEmotionMapRequest | None = None, persist: bool = True) -> CompanyEmotionMapResponse:
        request = payload if payload and payload.employees else self.default_request()
        employee_scores = [self._score_employee(employee) for employee in request.employees]
        employee_scores = sorted(employee_scores, key=lambda item: item.psychological_risk, reverse=True)
        team_scores = self._team_scores(employee_scores, request.employees, request.interactions)
        department_scores = self._department_scores(employee_scores, team_scores)
        conflict_risks = self._conflict_risks(request.interactions, team_scores, employee_scores)
        burnout_predictions = self._burnout_predictions(employee_scores, team_scores, department_scores)
        motivation_trends = self._motivation_trends(employee_scores, team_scores, department_scores)
        heatmap = self._heatmap(employee_scores, team_scores, department_scores, conflict_risks)
        forecasts = self._forecasts(department_scores, team_scores, request.horizon_days)
        recommendations = self._recommendations(employee_scores, team_scores, department_scores, conflict_risks, burnout_predictions)
        toxic_teams, happy_teams = self._team_classifications(team_scores)
        silent_risks = self._silent_employee_risks(employee_scores, request.employees)
        emotion_3d_nodes = self._emotion_3d_nodes(employee_scores, team_scores, department_scores)
        agent_council = self._agent_council(summary_inputs=(employee_scores, team_scores, department_scores, conflict_risks, burnout_predictions, recommendations))
        data_pipeline = self._data_pipeline_status(request)
        privacy_controls = self._privacy_controls()
        summary = self._summary(employee_scores, team_scores, department_scores, heatmap, forecasts, conflict_risks)
        heatmap_zones = self._heatmap_zones(summary, team_scores, department_scores, forecasts, recommendations, agent_council)
        summary = summary.model_copy(
            update={
                "toxic_teams": len(toxic_teams),
                "happy_teams": len(happy_teams),
                "silent_employee_risks": len(silent_risks),
                "production_readiness_score": self._production_readiness_score(
                    data_pipeline,
                    heatmap,
                    emotion_3d_nodes,
                    recommendations,
                    agent_council,
                ),
                "innovation_score": self._innovation_score(
                    emotion_3d_nodes,
                    forecasts,
                    conflict_risks,
                    burnout_predictions,
                    toxic_teams,
                    happy_teams,
                    silent_risks,
                ),
            }
        )
        response = CompanyEmotionMapResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            cycle_name=request.cycle_name,
            horizon_days=request.horizon_days,
            employee_scores=employee_scores,
            team_scores=team_scores,
            department_scores=department_scores,
            heatmap=heatmap,
            heatmap_zones=heatmap_zones,
            conflict_risks=conflict_risks,
            burnout_predictions=burnout_predictions,
            motivation_trends=motivation_trends,
            forecasts=forecasts,
            recommendations=recommendations,
            data_pipeline=data_pipeline,
            privacy_controls=privacy_controls,
            toxic_team_risks=toxic_teams,
            happy_team_signals=happy_teams,
            silent_employee_risks=silent_risks,
            emotion_3d_nodes=emotion_3d_nodes,
            agent_council=agent_council,
            assistant_prompts=[
                "Which department is most stressed?",
                "Show burnout hotspots.",
                "Which team has conflict risk?",
                "Which teams are toxic or silent?",
                "Show the 3D emotion map.",
                "Predict morale for next quarter.",
                "Show happiness trends.",
            ],
            executive_insights=self._executive_insights(summary, employee_scores, team_scores, department_scores, recommendations),
            summary=summary,
            source_systems=self.source_systems,
            digital_twin_updates=self._digital_twin_updates(summary, employee_scores, team_scores, department_scores),
            workflow_triggers=self._workflow_triggers(recommendations, conflict_risks, burnout_predictions),
            final_verdict="AI EMOTION RADAR COMPLETE",
            storage=str(HISTORY_PATH),
        )
        if persist:
            self._append_jsonl(response.model_dump(mode="json"))
        return response

    def ask(self, payload: EmotionAssistantRequest) -> EmotionAssistantResponse:
        analysis = self.default()
        intent = self._assistant_intent(payload.question)
        answer, confidence, entities, actions, evidence = self._assistant_answer(intent, analysis)
        return EmotionAssistantResponse(
            model="Company Emotion Map AI Assistant",
            generated_at=datetime.now(timezone.utc),
            question=payload.question,
            intent=intent,
            answer=answer,
            confidence=confidence,
            cited_entities=entities,
            recommended_actions=actions,
            evidence=evidence,
            source_systems=["emotion_ai_assistant", "organizational_heatmap_engine", "burnout_prediction_engine", "conflict_detection_engine"],
            storage=str(HISTORY_PATH),
        )

    async def stream(self):
        base = self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, stress_delta=7, motivation_delta=-4, conflict_delta=1),
            self._scenario_variant(base, stress_delta=14, motivation_delta=-9, conflict_delta=3),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: company_emotion_map\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> CompanyEmotionMapRequest:
        return CompanyEmotionMapRequest(
            cycle_name="Realtime Organizational Emotion Review",
            horizon_days=90,
            employees=[
                EmployeeEmotionSignal(
                    employee_id="emo-001",
                    name="Aarav Mehta",
                    team="Backend Platform",
                    department="Engineering",
                    project="Payments Reliability",
                    location="Bangalore",
                    role="Incident Lead",
                    survey_score=54,
                    communication_samples=[
                        EmotionTextSignal(channel="chat", text="I am exhausted from repeated production escalations and the handoffs keep breaking."),
                        EmotionTextSignal(channel="email", text="We need help because the same API incident keeps returning after midnight."),
                    ],
                    workload_hours=55,
                    overtime_hours=18,
                    meeting_hours=15,
                    task_load=112,
                    focus_hours=1.8,
                    productivity_trend=-22,
                    performance_trend=-12,
                    recognition_count=1,
                    learning_participation=28,
                    collaboration_score=58,
                    manager_support_score=48,
                    conflict_events=4,
                    negative_interactions=11,
                    positive_interactions=3,
                    attrition_risk=64,
                ),
                EmployeeEmotionSignal(
                    employee_id="emo-002",
                    name="Maya Iyer",
                    team="Backend Platform",
                    department="Engineering",
                    project="Payments Reliability",
                    location="Bangalore",
                    role="Senior Backend Engineer",
                    survey_score=63,
                    communication_samples=[
                        EmotionTextSignal(channel="meeting", text="The team is trying to recover, but the context switching and pressure are becoming heavy."),
                    ],
                    workload_hours=49,
                    overtime_hours=10,
                    meeting_hours=12,
                    task_load=94,
                    focus_hours=3.1,
                    productivity_trend=-8,
                    performance_trend=-4,
                    recognition_count=2,
                    learning_participation=42,
                    collaboration_score=68,
                    manager_support_score=62,
                    conflict_events=2,
                    negative_interactions=6,
                    positive_interactions=5,
                    attrition_risk=42,
                ),
                EmployeeEmotionSignal(
                    employee_id="emo-003",
                    name="Devika Nair",
                    team="AI Products",
                    department="Product",
                    project="Company Brain",
                    location="Remote",
                    role="ML Engineer",
                    survey_score=83,
                    communication_samples=[
                        EmotionTextSignal(channel="feedback", text="The project is challenging, but the team is motivated and the roadmap feels clear."),
                    ],
                    workload_hours=41,
                    overtime_hours=3,
                    meeting_hours=6,
                    task_load=74,
                    focus_hours=6.4,
                    productivity_trend=8,
                    performance_trend=6,
                    recognition_count=5,
                    learning_participation=88,
                    collaboration_score=86,
                    manager_support_score=84,
                    conflict_events=0,
                    negative_interactions=1,
                    positive_interactions=12,
                    attrition_risk=18,
                ),
                EmployeeEmotionSignal(
                    employee_id="emo-004",
                    name="Lina Chen",
                    team="AI Products",
                    department="Product",
                    project="Company Brain",
                    location="Hyderabad",
                    role="Product Lead",
                    survey_score=78,
                    communication_samples=[
                        EmotionTextSignal(channel="survey", text="I feel engaged and supported, though release deadlines need clearer scope decisions."),
                    ],
                    workload_hours=43,
                    overtime_hours=4,
                    meeting_hours=8,
                    task_load=78,
                    focus_hours=5.4,
                    productivity_trend=4,
                    performance_trend=5,
                    recognition_count=4,
                    learning_participation=72,
                    collaboration_score=82,
                    manager_support_score=81,
                    conflict_events=1,
                    negative_interactions=2,
                    positive_interactions=9,
                    attrition_risk=22,
                ),
                EmployeeEmotionSignal(
                    employee_id="emo-005",
                    name="Rina Shah",
                    team="Customer Success",
                    department="Customer Success",
                    project="Enterprise Renewals",
                    location="Pune",
                    role="Customer Success Manager",
                    survey_score=57,
                    communication_samples=[
                        EmotionTextSignal(channel="email", text="Client escalations are intense and I feel frustrated that issue ownership keeps shifting."),
                    ],
                    workload_hours=50,
                    overtime_hours=11,
                    meeting_hours=18,
                    task_load=102,
                    focus_hours=2.2,
                    productivity_trend=-13,
                    performance_trend=-6,
                    recognition_count=1,
                    learning_participation=34,
                    collaboration_score=61,
                    manager_support_score=55,
                    conflict_events=3,
                    negative_interactions=8,
                    positive_interactions=4,
                    attrition_risk=51,
                ),
                EmployeeEmotionSignal(
                    employee_id="emo-006",
                    name="Omar Khan",
                    team="Finance Ops",
                    department="Finance",
                    project="Billing Governance",
                    location="Mumbai",
                    role="Finance Analyst",
                    survey_score=82,
                    communication_samples=[
                        EmotionTextSignal(channel="chat", text="The billing governance work is stable and the team has clear decision owners."),
                    ],
                    workload_hours=39,
                    overtime_hours=1,
                    meeting_hours=4,
                    task_load=62,
                    focus_hours=7.1,
                    productivity_trend=6,
                    performance_trend=5,
                    recognition_count=3,
                    learning_participation=62,
                    collaboration_score=84,
                    manager_support_score=82,
                    conflict_events=0,
                    negative_interactions=1,
                    positive_interactions=8,
                    attrition_risk=16,
                ),
                EmployeeEmotionSignal(
                    employee_id="emo-007",
                    name="Sarah Malik",
                    team="Security Response",
                    department="Security",
                    project="Zero Trust Controls",
                    location="Hyderabad",
                    role="Security Architect",
                    survey_score=69,
                    communication_samples=[
                        EmotionTextSignal(channel="meeting", text="Security reviews are productive, but emergency access requests create stress."),
                    ],
                    workload_hours=45,
                    overtime_hours=7,
                    meeting_hours=9,
                    task_load=85,
                    focus_hours=4.6,
                    productivity_trend=1,
                    performance_trend=4,
                    recognition_count=3,
                    learning_participation=76,
                    collaboration_score=78,
                    manager_support_score=74,
                    conflict_events=1,
                    negative_interactions=3,
                    positive_interactions=7,
                    attrition_risk=29,
                ),
                EmployeeEmotionSignal(
                    employee_id="emo-008",
                    name="Nikhil Shah",
                    team="Release Quality",
                    department="Quality",
                    project="Release Readiness",
                    location="Pune",
                    role="QA Lead",
                    survey_score=61,
                    communication_samples=[
                        EmotionTextSignal(channel="chat", text="The release is late and QA is absorbing pressure from missing requirements."),
                    ],
                    workload_hours=48,
                    overtime_hours=9,
                    meeting_hours=11,
                    task_load=92,
                    focus_hours=3.4,
                    productivity_trend=-9,
                    performance_trend=-3,
                    recognition_count=2,
                    learning_participation=44,
                    collaboration_score=66,
                    manager_support_score=64,
                    conflict_events=2,
                    negative_interactions=5,
                    positive_interactions=5,
                    attrition_risk=38,
                ),
            ],
            interactions=[
                TeamInteractionSignal(
                    source_team="Backend Platform",
                    target_team="Customer Success",
                    department="Engineering",
                    sentiment_alignment=-0.42,
                    unresolved_issues=6,
                    escalation_count=4,
                    communication_volume=38,
                    evidence=["Escalation ownership shifted repeatedly", "Client-impacting API incidents restarted after midnight"],
                ),
                TeamInteractionSignal(
                    source_team="Backend Platform",
                    target_team="Release Quality",
                    department="Engineering",
                    sentiment_alignment=-0.18,
                    unresolved_issues=4,
                    escalation_count=2,
                    communication_volume=27,
                    evidence=["Late requirements increased QA pressure", "Release risk remains unresolved"],
                ),
                TeamInteractionSignal(
                    source_team="AI Products",
                    target_team="Finance Ops",
                    department="Product",
                    sentiment_alignment=0.72,
                    unresolved_issues=1,
                    escalation_count=0,
                    communication_volume=16,
                    evidence=["Clear decision owners", "Stable cross-functional handoff"],
                ),
            ],
        )

    def _score_employee(self, employee: EmployeeEmotionSignal) -> EmployeeEmotionScore:
        text = self._employee_text(employee)
        nlp = nlp_service.analyze(
            NLPAnalyzeRequest(
                employee_id=employee.employee_id,
                department=employee.department,
                channel="emotion_map",
                text=text,
            )
        )
        negative_sentiment = max(0.0, -nlp.sentiment_score)
        positive_sentiment = max(0.0, nlp.sentiment_score)
        workload_pressure = self._clip(employee.task_load * 0.55 + max(0, employee.workload_hours - 40) * 2.2 + employee.overtime_hours * 2.8)
        meeting_pressure = self._clip(employee.meeting_hours * 5.2)
        focus_deficit = self._clip(max(0, 6 - employee.focus_hours) / 6 * 100)
        productivity_decline = self._clip(max(0, -employee.productivity_trend) * 1.35 + max(0, -employee.performance_trend) * 1.1)
        conflict_exposure = self._clip(
            employee.conflict_events * 12
            + employee.negative_interactions * 4.4
            + max(0, 55 - employee.collaboration_score) * 0.9
            + nlp.emotion_scores.toxicity * 30
        )
        stress = self._clip(
            nlp.emotion_scores.stress * 100 * 0.32
            + workload_pressure * 0.22
            + meeting_pressure * 0.16
            + conflict_exposure * 0.14
            + focus_deficit * 0.08
            + productivity_decline * 0.08
        )
        burnout = self._clip(
            stress * 0.32
            + nlp.emotion_scores.burnout * 100 * 0.22
            + employee.overtime_hours * 2.2
            + meeting_pressure * 0.12
            + focus_deficit * 0.12
            + employee.attrition_risk * 0.1
        )
        motivation = self._clip(
            46
            + nlp.emotion_scores.motivation * 32
            + positive_sentiment * 16
            + employee.learning_participation * 0.14
            + employee.recognition_count * 2.4
            + employee.productivity_trend * 0.32
            - burnout * 0.18
            - negative_sentiment * 8
        )
        engagement = self._clip(
            employee.survey_score * 0.26
            + employee.collaboration_score * 0.22
            + employee.manager_support_score * 0.16
            + employee.learning_participation * 0.13
            + min(100, employee.positive_interactions * 8) * 0.12
            + (100 - meeting_pressure) * 0.11
        )
        happiness = self._clip(
            employee.survey_score * 0.28
            + (50 + nlp.sentiment_score * 50) * 0.22
            + employee.manager_support_score * 0.16
            + min(100, employee.recognition_count * 12) * 0.12
            + engagement * 0.14
            + (100 - stress) * 0.08
        )
        psychological = self._clip(stress * 0.34 + burnout * 0.3 + conflict_exposure * 0.18 + nlp.emotion_scores.toxicity * 100 * 0.18)
        satisfaction = self._clip(happiness * 0.38 + engagement * 0.24 + employee.manager_support_score * 0.18 + (100 - psychological) * 0.2)
        morale = self._clip((happiness + motivation + engagement + satisfaction) / 4 - psychological * 0.12)
        evidence = [
            f"nlp_sentiment={round(nlp.sentiment_score, 3)}",
            f"primary_emotion={nlp.primary_emotion}",
            f"workload_pressure={round(workload_pressure, 2)}",
            f"meeting_pressure={round(meeting_pressure, 2)}",
            f"focus_deficit={round(focus_deficit, 2)}",
            f"conflict_exposure={round(conflict_exposure, 2)}",
        ]
        return EmployeeEmotionScore(
            employee_id=employee.employee_id,
            name=employee.name,
            team=employee.team,
            department=employee.department,
            project=employee.project,
            location=employee.location,
            role=employee.role,
            happiness_score=round(happiness, 2),
            stress_score=round(stress, 2),
            motivation_score=round(motivation, 2),
            burnout_score=round(burnout, 2),
            engagement_score=round(engagement, 2),
            satisfaction_score=round(satisfaction, 2),
            morale_score=round(morale, 2),
            psychological_risk=round(psychological, 2),
            sentiment_score=round(nlp.sentiment_score, 3),
            conflict_exposure=round(conflict_exposure, 2),
            priority=self._priority(psychological),
            evidence=evidence,
        )

    def _team_scores(
        self,
        employees: list[EmployeeEmotionScore],
        raw_employees: list[EmployeeEmotionSignal],
        interactions: list[TeamInteractionSignal],
    ) -> list[TeamEmotionScore]:
        grouped: dict[tuple[str, str], list[EmployeeEmotionScore]] = defaultdict(list)
        raw_by_id = {employee.employee_id: employee for employee in raw_employees}
        interaction_risk: dict[str, list[float]] = defaultdict(list)
        for interaction in interactions:
            risk = self._interaction_risk(interaction)
            interaction_risk[interaction.source_team].append(risk)
            interaction_risk[interaction.target_team].append(risk * 0.82)
        for score in employees:
            grouped[(score.department, score.team)].append(score)
        teams: list[TeamEmotionScore] = []
        for (department, team), rows in grouped.items():
            raw_rows = [raw_by_id[row.employee_id] for row in rows if row.employee_id in raw_by_id]
            conflict = self._clip(
                mean([row.conflict_exposure for row in rows])
                + mean(interaction_risk.get(team, [0])) * 0.45
                + mean([raw.conflict_events * 4 for raw in raw_rows] or [0])
            )
            stress = mean([row.stress_score for row in rows])
            burnout = mean([row.burnout_score for row in rows])
            morale = mean([row.morale_score for row in rows])
            collaboration = mean([raw.collaboration_score for raw in raw_rows] or [72]) - conflict * 0.12
            workload_score = self._clip(
                mean(
                    [
                        raw.task_load * 0.46
                        + raw.overtime_hours * 2.2
                        + raw.meeting_hours * 1.4
                        + max(0, raw.workload_hours - 40) * 2.0
                        + max(0, 5 - raw.focus_hours) * 4.0
                        for raw in raw_rows
                    ]
                    or [stress]
                )
            )
            productivity_health = self._clip(
                82
                + mean([raw.productivity_trend for raw in raw_rows] or [0]) * 0.42
                + mean([raw.performance_trend for raw in raw_rows] or [0]) * 0.34
                - workload_score * 0.16
                - burnout * 0.2
                - conflict * 0.08
            )
            retention = self._clip(mean([raw.attrition_risk for raw in raw_rows] or [25]) * 0.58 + burnout * 0.28 + conflict * 0.14)
            team_health_index = self._clip(
                morale * 0.23
                + mean([row.engagement_score for row in rows]) * 0.17
                + self._clip(collaboration) * 0.16
                + productivity_health * 0.15
                + (100 - stress) * 0.11
                + (100 - burnout) * 0.1
                + (100 - workload_score) * 0.05
                + (100 - conflict) * 0.03
            )
            health_status = self._health_status(team_health_index)
            trend = "declining" if stress >= 65 or burnout >= 65 or conflict >= 55 else "stable" if morale >= 62 else "watch"
            recommendation = "Maintain operating rhythm and continue sentiment monitoring."
            if burnout >= 66:
                recommendation = f"Reduce workload pressure for {team} and move high-cognitive tasks to backup owners."
            elif conflict >= 58:
                recommendation = f"Run a facilitated handoff reset for {team} and assign one decision owner per escalation."
            elif morale < 58:
                recommendation = f"Increase recognition, manager support, and learning time for {team}."
            teams.append(
                TeamEmotionScore(
                    team=team,
                    department=department,
                    headcount=len(rows),
                    team_health_index=round(team_health_index, 2),
                    health_status=health_status,
                    health_color=self._health_color(health_status),
                    happiness_score=round(mean([row.happiness_score for row in rows]), 2),
                    stress_score=round(stress, 2),
                    workload_score=round(workload_score, 2),
                    collaboration_score=round(self._clip(collaboration), 2),
                    productivity_health_score=round(productivity_health, 2),
                    motivation_score=round(mean([row.motivation_score for row in rows]), 2),
                    conflict_risk=round(conflict, 2),
                    burnout_risk=round(burnout, 2),
                    engagement_score=round(mean([row.engagement_score for row in rows]), 2),
                    morale_score=round(morale, 2),
                    retention_risk=round(retention, 2),
                    priority=self._priority(max(stress, burnout, conflict, retention)),
                    trend=trend,
                    recommendation=recommendation,
                )
            )
        return sorted(teams, key=lambda item: max(item.stress_score, item.burnout_risk, item.conflict_risk), reverse=True)

    def _department_scores(self, employees: list[EmployeeEmotionScore], teams: list[TeamEmotionScore]) -> list[DepartmentEmotionScore]:
        grouped: dict[str, list[EmployeeEmotionScore]] = defaultdict(list)
        team_grouped: dict[str, list[TeamEmotionScore]] = defaultdict(list)
        for employee in employees:
            grouped[employee.department].append(employee)
        for team in teams:
            team_grouped[team.department].append(team)
        departments: list[DepartmentEmotionScore] = []
        for department, rows in grouped.items():
            team_rows = team_grouped.get(department, [])
            stress = mean([row.stress_score for row in rows])
            burnout = mean([row.burnout_score for row in rows])
            motivation = mean([row.motivation_score for row in rows])
            happiness = mean([row.happiness_score for row in rows])
            engagement = mean([row.engagement_score for row in rows])
            morale = mean([row.morale_score for row in rows])
            conflict = mean([team.conflict_risk for team in team_rows] or [mean([row.conflict_exposure for row in rows])])
            workload = mean([team.workload_score for team in team_rows] or [stress])
            productivity_health = mean([team.productivity_health_score for team in team_rows] or [max(0, 100 - stress)])
            retention = self._clip(mean([team.retention_risk for team in team_rows] or [burnout * 0.6]) + max(0, 62 - morale) * 0.24)
            department_health_index = self._clip(
                morale * 0.24
                + engagement * 0.17
                + happiness * 0.12
                + motivation * 0.11
                + productivity_health * 0.14
                + (100 - stress) * 0.1
                + (100 - burnout) * 0.07
                + (100 - workload) * 0.03
                + (100 - conflict) * 0.02
            )
            health_status = self._health_status(department_health_index)
            recommendation = "Keep current team support and monitor quarterly sentiment."
            if burnout >= 65:
                recommendation = f"Reduce workload in {department} and add manager-led recovery plans."
            elif conflict >= 58:
                recommendation = f"Run department-level conflict mediation and clarify cross-team ownership in {department}."
            elif motivation < 58:
                recommendation = f"Increase recognition, mentorship, and internal mobility options in {department}."
            departments.append(
                DepartmentEmotionScore(
                    department=department,
                    headcount=len(rows),
                    department_health_index=round(department_health_index, 2),
                    health_status=health_status,
                    health_color=self._health_color(health_status),
                    morale_score=round(morale, 2),
                    burnout_score=round(burnout, 2),
                    stress_index=round(stress, 2),
                    motivation_index=round(motivation, 2),
                    retention_risk=round(retention, 2),
                    happiness_score=round(happiness, 2),
                    engagement_score=round(engagement, 2),
                    conflict_risk=round(conflict, 2),
                    priority=self._priority(max(stress, burnout, conflict, retention)),
                    recommendation=recommendation,
                )
            )
        return sorted(departments, key=lambda item: max(item.stress_index, item.burnout_score, item.conflict_risk), reverse=True)

    def _conflict_risks(
        self,
        interactions: list[TeamInteractionSignal],
        teams: list[TeamEmotionScore],
        employees: list[EmployeeEmotionScore],
    ) -> list[ConflictRiskInsight]:
        risks: list[ConflictRiskInsight] = []
        for interaction in interactions:
            risk = self._interaction_risk(interaction)
            if risk >= 24:
                risks.append(
                    ConflictRiskInsight(
                        source_entity=interaction.source_team,
                        target_entity=interaction.target_team,
                        scope="team",
                        conflict_probability=round(risk, 2),
                        communication_breakdown_risk=round(self._clip(risk * 0.86 + interaction.unresolved_issues * 3), 2),
                        toxic_interaction_index=round(self._clip(max(0, -interaction.sentiment_alignment) * 72 + interaction.escalation_count * 5), 2),
                        reason=f"{interaction.source_team} and {interaction.target_team} show unresolved ownership and sentiment mismatch.",
                        evidence=interaction.evidence
                        or [
                            f"sentiment_alignment={interaction.sentiment_alignment}",
                            f"unresolved_issues={interaction.unresolved_issues}",
                            f"escalations={interaction.escalation_count}",
                        ],
                        recommended_action="Schedule a structured handoff reset, name one escalation owner, and move status updates into a shared decision log.",
                    )
                )
        for team in teams:
            if team.conflict_risk >= 58:
                risks.append(
                    ConflictRiskInsight(
                        source_entity=team.team,
                        target_entity=team.department,
                        scope="department",
                        conflict_probability=team.conflict_risk,
                        communication_breakdown_risk=round(self._clip(team.conflict_risk * 0.92), 2),
                        toxic_interaction_index=round(self._clip(team.conflict_risk * 0.55), 2),
                        reason=f"{team.team} has elevated conflict exposure and declining collaboration quality.",
                        evidence=[f"collaboration={team.collaboration_score}", f"stress={team.stress_score}", f"burnout={team.burnout_risk}"],
                        recommended_action=team.recommendation,
                    )
                )
        for employee in employees:
            if employee.conflict_exposure >= 68:
                risks.append(
                    ConflictRiskInsight(
                        source_entity=employee.name,
                        target_entity=employee.team,
                        scope="employee",
                        conflict_probability=employee.conflict_exposure,
                        communication_breakdown_risk=round(self._clip(employee.conflict_exposure * 0.78 + employee.stress_score * 0.18), 2),
                        toxic_interaction_index=round(self._clip(employee.conflict_exposure * 0.56), 2),
                        reason=f"{employee.name} shows high communication tension and elevated psychological risk.",
                        evidence=employee.evidence[:4],
                        recommended_action="Assign manager mediation, reduce escalation exposure, and confirm written decision ownership.",
                    )
                )
        deduped: dict[tuple[str, str, str], ConflictRiskInsight] = {}
        for item in risks:
            key = (item.source_entity, item.target_entity, item.scope)
            if key not in deduped or item.conflict_probability > deduped[key].conflict_probability:
                deduped[key] = item
        return sorted(deduped.values(), key=lambda item: item.conflict_probability, reverse=True)[:10]

    def _burnout_predictions(
        self,
        employees: list[EmployeeEmotionScore],
        teams: list[TeamEmotionScore],
        departments: list[DepartmentEmotionScore],
    ) -> list[BurnoutPrediction]:
        predictions: list[BurnoutPrediction] = []
        for employee in employees[:8]:
            pressure = self._clip(employee.stress_score * 0.42 + employee.burnout_score * 0.38 + employee.psychological_risk * 0.2)
            predictions.append(
                BurnoutPrediction(
                    entity_id=employee.employee_id,
                    label=employee.name,
                    scope="employee",
                    burnout_probability=employee.burnout_score,
                    overwork_risk=round(pressure, 2),
                    fatigue_trend=round(self._clip(employee.burnout_score - employee.motivation_score, minimum=-100), 2),
                    mental_workload_pressure=round(self._clip(employee.stress_score * 0.7 + employee.conflict_exposure * 0.3), 2),
                    forecast_30d=round(self._clip(employee.burnout_score + employee.stress_score * 0.05), 2),
                    forecast_90d=round(self._clip(employee.burnout_score + employee.stress_score * 0.12 + employee.conflict_exposure * 0.04), 2),
                    recommendation="Reduce workload by 15% and protect recovery leave." if employee.burnout_score >= 70 else "Keep monitoring workload, focus time, and emotional trend deltas.",
                )
            )
        for team in teams[:6]:
            predictions.append(
                BurnoutPrediction(
                    entity_id=team.team,
                    label=team.team,
                    scope="team",
                    burnout_probability=team.burnout_risk,
                    overwork_risk=round(self._clip(team.stress_score * 0.48 + team.retention_risk * 0.18 + team.burnout_risk * 0.34), 2),
                    fatigue_trend=round(self._clip(team.burnout_risk - team.motivation_score, minimum=-100), 2),
                    mental_workload_pressure=round(self._clip(team.stress_score * 0.6 + team.conflict_risk * 0.22 + (100 - team.collaboration_score) * 0.18), 2),
                    forecast_30d=round(self._clip(team.burnout_risk + team.stress_score * 0.06), 2),
                    forecast_90d=round(self._clip(team.burnout_risk + team.stress_score * 0.13 + team.conflict_risk * 0.06), 2),
                    recommendation=team.recommendation,
                )
            )
        for department in departments:
            predictions.append(
                BurnoutPrediction(
                    entity_id=department.department,
                    label=department.department,
                    scope="department",
                    burnout_probability=department.burnout_score,
                    overwork_risk=round(self._clip(department.stress_index * 0.5 + department.retention_risk * 0.2 + department.burnout_score * 0.3), 2),
                    fatigue_trend=round(self._clip(department.burnout_score - department.motivation_index, minimum=-100), 2),
                    mental_workload_pressure=round(self._clip(department.stress_index * 0.62 + department.conflict_risk * 0.2 + department.burnout_score * 0.18), 2),
                    forecast_30d=round(self._clip(department.burnout_score + department.stress_index * 0.05), 2),
                    forecast_90d=round(self._clip(department.burnout_score + department.stress_index * 0.12 + department.conflict_risk * 0.05), 2),
                    recommendation=department.recommendation,
                )
            )
        return sorted(predictions, key=lambda item: item.forecast_90d, reverse=True)[:18]

    @staticmethod
    def _motivation_trends(
        employees: list[EmployeeEmotionScore],
        teams: list[TeamEmotionScore],
        departments: list[DepartmentEmotionScore],
    ) -> list[MotivationTrend]:
        trends: list[MotivationTrend] = []
        for employee in employees[:8]:
            delta = employee.motivation_score - 72 - employee.stress_score * 0.08
            drivers = []
            if employee.stress_score >= 62:
                drivers.append("stress pressure")
            if employee.engagement_score < 62:
                drivers.append("engagement decline")
            if employee.happiness_score < 62:
                drivers.append("low happiness")
            if not drivers:
                drivers.append("stable engagement")
            trends.append(
                MotivationTrend(
                    entity_id=employee.employee_id,
                    label=employee.name,
                    scope="employee",
                    motivation_score=employee.motivation_score,
                    trend_delta=round(max(-100, min(100, delta)), 2),
                    drivers=drivers,
                    recommendation="Increase recognition and growth opportunities." if delta < -12 else "Maintain current growth and recognition cadence.",
                )
            )
        for team in teams[:6]:
            delta = team.motivation_score - 70 - team.conflict_risk * 0.08
            trends.append(
                MotivationTrend(
                    entity_id=team.team,
                    label=team.team,
                    scope="team",
                    motivation_score=team.motivation_score,
                    trend_delta=round(max(-100, min(100, delta)), 2),
                    drivers=["team conflict" if team.conflict_risk >= 50 else "team engagement", "burnout pressure" if team.burnout_risk >= 60 else "workload stable"],
                    recommendation="Reset sprint scope and increase manager recognition." if delta < -10 else "Keep growth goals visible.",
                )
            )
        for department in departments:
            delta = department.motivation_index - 70 - department.stress_index * 0.07
            trends.append(
                MotivationTrend(
                    entity_id=department.department,
                    label=department.department,
                    scope="department",
                    motivation_score=department.motivation_index,
                    trend_delta=round(max(-100, min(100, delta)), 2),
                    drivers=["department stress", "recognition gap"] if delta < -10 else ["healthy motivation"],
                    recommendation=department.recommendation,
                )
            )
        return sorted(trends, key=lambda item: item.trend_delta)

    def _heatmap(
        self,
        employees: list[EmployeeEmotionScore],
        teams: list[TeamEmotionScore],
        departments: list[DepartmentEmotionScore],
        conflicts: list[ConflictRiskInsight],
    ) -> list[EmotionHeatmapPoint]:
        points: list[EmotionHeatmapPoint] = []
        for department in departments:
            metric_values: dict[EmotionMetric, float] = {
                "stress": department.stress_index,
                "happiness": department.happiness_score,
                "burnout": department.burnout_score,
                "engagement": department.engagement_score,
                "motivation": department.motivation_index,
                "conflict": department.conflict_risk,
                "morale": department.morale_score,
            }
            for metric, value in metric_values.items():
                points.append(self._heatmap_point("department", department.department, department.department, department.department, metric, value))
        for team in teams:
            for metric, value in {
                "stress": team.stress_score,
                "happiness": team.happiness_score,
                "burnout": team.burnout_risk,
                "engagement": team.engagement_score,
                "motivation": team.motivation_score,
                "conflict": team.conflict_risk,
                "morale": team.morale_score,
            }.items():
                points.append(self._heatmap_point("team", team.team, team.team, team.department, metric, value))
        for employee in employees[:12]:
            for metric, value in {
                "stress": employee.stress_score,
                "happiness": employee.happiness_score,
                "burnout": employee.burnout_score,
                "engagement": employee.engagement_score,
                "motivation": employee.motivation_score,
                "conflict": employee.conflict_exposure,
                "morale": employee.morale_score,
            }.items():
                points.append(self._heatmap_point("employee", employee.employee_id, employee.name, employee.department, metric, value))
        for conflict in conflicts[:4]:
            points.append(self._heatmap_point("team", f"{conflict.source_entity}->{conflict.target_entity}", f"{conflict.source_entity} to {conflict.target_entity}", "Cross-team", "conflict", conflict.conflict_probability))
        return sorted(points, key=lambda item: item.intensity, reverse=True)[:80]

    def _forecasts(
        self,
        departments: list[DepartmentEmotionScore],
        teams: list[TeamEmotionScore],
        horizon_days: int,
    ) -> list[EmotionForecastPoint]:
        periods: list[tuple[str, float]] = [
            ("30_days", 1.0),
            ("90_days", 2.4),
            ("6_months", 4.1),
            ("1_year", 6.7),
        ]
        forecasts: list[EmotionForecastPoint] = []
        for department in departments:
            for period, step in periods:
                pressure = (department.stress_index * 0.018 + department.burnout_score * 0.015 + department.conflict_risk * 0.011) * step * (horizon_days / 90)
                metrics: dict[EmotionMetric, tuple[float, str]] = {
                    "burnout": (department.burnout_score + pressure * 1.35, "burnout pressure and overtime concentration"),
                    "morale": (department.morale_score - pressure * 1.1, "morale drag from stress and conflict"),
                    "engagement": (department.engagement_score - pressure * 0.82, "engagement decline from workload pressure"),
                    "conflict": (department.conflict_risk + pressure * 0.88, "unresolved communication loops"),
                    "stress": (department.stress_index + pressure, "stress trend continuation"),
                    "motivation": (department.motivation_index - pressure * 0.74, "motivation decline under sustained pressure"),
                    "happiness": (department.happiness_score - pressure * 0.68, "happiness pressure from workload"),
                }
                for metric, (score, driver) in metrics.items():
                    projected = self._clip(score)
                    risk = projected if metric in {"burnout", "conflict", "stress"} else 100 - projected
                    forecasts.append(
                        EmotionForecastPoint(
                            period=period,  # type: ignore[arg-type]
                            metric=metric,
                            scope="department",
                            entity_id=department.department,
                            label=department.department,
                            projected_score=round(projected, 2),
                            risk_probability=round(self._clip(risk), 2),
                            confidence=0.86 if period in {"30_days", "90_days"} else 0.78,
                            driver=driver,
                        )
                    )
        for team in teams[:6]:
            for period, step in periods[:2]:
                pressure = (team.stress_score * 0.02 + team.burnout_risk * 0.018 + team.conflict_risk * 0.012) * step
                for metric, base, driver in [
                    ("burnout", team.burnout_risk + pressure, "team fatigue progression"),
                    ("morale", team.morale_score - pressure * 0.85, "team morale pressure"),
                    ("conflict", team.conflict_risk + pressure * 0.72, "collaboration stress"),
                ]:
                    projected = self._clip(base)
                    risk = projected if metric in {"burnout", "conflict", "stress"} else 100 - projected
                    forecasts.append(
                        EmotionForecastPoint(
                            period=period,  # type: ignore[arg-type]
                            metric=metric,  # type: ignore[arg-type]
                            scope="team",
                            entity_id=team.team,
                            label=team.team,
                            projected_score=round(projected, 2),
                            risk_probability=round(self._clip(risk), 2),
                            confidence=0.82,
                            driver=driver,
                        )
                    )
        return sorted(forecasts, key=lambda item: item.risk_probability, reverse=True)[:50]

    def _recommendations(
        self,
        employees: list[EmployeeEmotionScore],
        teams: list[TeamEmotionScore],
        departments: list[DepartmentEmotionScore],
        conflicts: list[ConflictRiskInsight],
        burnouts: list[BurnoutPrediction],
    ) -> list[EmotionRecommendation]:
        recs: list[EmotionRecommendation] = []
        highest_burnout = max(burnouts, key=lambda item: item.forecast_90d, default=None)
        highest_conflict = max(conflicts, key=lambda item: item.conflict_probability, default=None)
        weakest_morale = min(departments, key=lambda item: item.morale_score, default=None)
        most_stressed = max(departments, key=lambda item: item.stress_index, default=None)
        lowest_motivation = min(teams, key=lambda item: item.motivation_score, default=None)
        if highest_burnout and highest_burnout.forecast_90d >= 60:
            recs.append(
                EmotionRecommendation(
                    title="Reduce burnout hotspot workload",
                    category="workload",
                    priority=self._priority(highest_burnout.forecast_90d),
                    action=f"Reduce workload for {highest_burnout.label} by 15% and protect recovery blocks for two weeks.",
                    rationale=f"Forecasted 90-day burnout probability is {round(highest_burnout.forecast_90d)}%.",
                    expected_improvement=round(self._clip(highest_burnout.forecast_90d * 0.24), 2),
                    confidence=0.9,
                    triggered_workflow="workflow_automation.workload_rebalance",
                )
            )
        if highest_conflict and highest_conflict.conflict_probability >= 45:
            recs.append(
                EmotionRecommendation(
                    title="Resolve team conflict loop",
                    category="conflict",
                    priority=self._priority(highest_conflict.conflict_probability),
                    action=highest_conflict.recommended_action,
                    rationale=highest_conflict.reason,
                    expected_improvement=round(self._clip(highest_conflict.conflict_probability * 0.3), 2),
                    confidence=0.87,
                    triggered_workflow="workflow_automation.conflict_mediation",
                )
            )
        if most_stressed and most_stressed.stress_index >= 58:
            recs.append(
                EmotionRecommendation(
                    title="Manager intervention for stress hotspot",
                    category="manager_intervention",
                    priority=self._priority(most_stressed.stress_index),
                    action=f"Run manager intervention in {most_stressed.department} and remove two low-value recurring meetings.",
                    rationale=f"{most_stressed.department} has stress index {round(most_stressed.stress_index)} and burnout {round(most_stressed.burnout_score)}.",
                    expected_improvement=round(self._clip(most_stressed.stress_index * 0.2), 2),
                    confidence=0.85,
                    triggered_workflow="workflow_automation.manager_intervention",
                )
            )
        if weakest_morale and weakest_morale.morale_score < 62:
            recs.append(
                EmotionRecommendation(
                    title="Recover department morale",
                    category="wellness",
                    priority=self._priority(100 - weakest_morale.morale_score),
                    action=f"Launch targeted wellness and recognition plan for {weakest_morale.department}.",
                    rationale=f"Morale is {round(weakest_morale.morale_score)} with retention risk {round(weakest_morale.retention_risk)}.",
                    expected_improvement=18,
                    confidence=0.84,
                    triggered_workflow="workflow_automation.wellness_program",
                )
            )
        if lowest_motivation and lowest_motivation.motivation_score < 62:
            recs.append(
                EmotionRecommendation(
                    title="Restore team motivation",
                    category="motivation",
                    priority="medium",
                    action=f"Give {lowest_motivation.team} visible milestones, recognition rituals, and protected learning time.",
                    rationale=f"Team motivation is {round(lowest_motivation.motivation_score)} and trend is {lowest_motivation.trend}.",
                    expected_improvement=14,
                    confidence=0.82,
                    triggered_workflow="workflow_automation.motivation_recovery",
                )
            )
        if not recs and employees:
            recs.append(
                EmotionRecommendation(
                    title="Maintain emotional digital twin monitoring",
                    category="engagement",
                    priority="low",
                    action="Keep realtime emotional telemetry active and review weekly heatmap deltas.",
                    rationale="No critical hotspot exceeds intervention threshold.",
                    expected_improvement=8,
                    confidence=0.78,
                    triggered_workflow="workflow_automation.monitor_emotion_map",
                )
            )
        return recs[:7]

    def _team_classifications(self, teams: list[TeamEmotionScore]) -> tuple[list[TeamEmotionClassification], list[TeamEmotionClassification]]:
        toxic: list[TeamEmotionClassification] = []
        happy: list[TeamEmotionClassification] = []
        for team in teams:
            toxicity = self._clip(team.conflict_risk * 0.38 + team.burnout_risk * 0.24 + team.stress_score * 0.2 + max(0, 62 - team.morale_score) * 0.18)
            happiness = self._clip(team.happiness_score * 0.3 + team.engagement_score * 0.26 + team.collaboration_score * 0.22 + team.morale_score * 0.22)
            if toxicity >= 52:
                toxic.append(
                    TeamEmotionClassification(
                        team=team.team,
                        department=team.department,
                        classification="toxic" if toxicity >= 68 else "watch",
                        score=round(toxicity, 2),
                        reason=f"{team.team} shows conflict {round(team.conflict_risk)}, burnout {round(team.burnout_risk)}, and stress {round(team.stress_score)}.",
                        drivers=[
                            "communication friction" if team.conflict_risk >= 45 else "relationship watch",
                            "burnout pressure" if team.burnout_risk >= 55 else "capacity pressure",
                            "morale drag" if team.morale_score < 62 else "stress trend",
                        ],
                        recommended_action=team.recommendation,
                    )
                )
            if happiness >= 72 and team.conflict_risk < 48 and team.burnout_risk < 58:
                happy.append(
                    TeamEmotionClassification(
                        team=team.team,
                        department=team.department,
                        classification="happy" if happiness >= 82 else "healthy",
                        score=round(happiness, 2),
                        reason=f"{team.team} has strong morale {round(team.morale_score)}, engagement {round(team.engagement_score)}, and collaboration {round(team.collaboration_score)}.",
                        drivers=["high collaboration", "healthy morale", "low conflict", "sustainable workload"],
                        recommended_action="Use this team as a positive operating-pattern benchmark and preserve its focus time.",
                    )
                )
        return (
            sorted(toxic, key=lambda item: item.score, reverse=True)[:8],
            sorted(happy, key=lambda item: item.score, reverse=True)[:8],
        )

    def _silent_employee_risks(
        self,
        employees: list[EmployeeEmotionScore],
        raw_employees: list[EmployeeEmotionSignal],
    ) -> list[SilentEmployeeRisk]:
        raw_by_id = {employee.employee_id: employee for employee in raw_employees}
        risks: list[SilentEmployeeRisk] = []
        for employee in employees:
            raw = raw_by_id.get(employee.employee_id)
            if not raw:
                continue
            communication_volume = raw.positive_interactions + raw.negative_interactions + len(raw.communication_samples) * 2
            withdrawal = self._clip(max(0, 12 - communication_volume) * 6 + max(0, 56 - raw.collaboration_score) * 0.62 + max(0, 50 - raw.learning_participation) * 0.3)
            participation_delta = self._clip(raw.productivity_trend * 0.36 + raw.performance_trend * 0.32 + raw.learning_participation * 0.16 + raw.collaboration_score * 0.12 - 55, minimum=-100)
            isolation = self._clip(withdrawal * 0.48 + max(0, 58 - employee.engagement_score) * 0.22 + max(0, 58 - employee.morale_score) * 0.16 + employee.psychological_risk * 0.14)
            if isolation >= 32:
                risks.append(
                    SilentEmployeeRisk(
                        employee_id=employee.employee_id,
                        name=employee.name,
                        team=employee.team,
                        department=employee.department,
                        isolation_risk=round(isolation, 2),
                        participation_delta=round(participation_delta, 2),
                        communication_withdrawal_score=round(withdrawal, 2),
                        reason=f"{employee.name} shows reduced participation signals with engagement {round(employee.engagement_score)} and morale {round(employee.morale_score)}.",
                        recommended_action="Schedule a private manager check-in and rebalance collaboration load before disengagement becomes attrition risk.",
                    )
                )
        return sorted(risks, key=lambda item: item.isolation_risk, reverse=True)[:10]

    def _heatmap_zones(
        self,
        summary: CompanyEmotionMapSummary,
        teams: list[TeamEmotionScore],
        departments: list[DepartmentEmotionScore],
        forecasts: list[EmotionForecastPoint],
        recommendations: list[EmotionRecommendation],
        agents: list[EmotionAgentContribution],
    ) -> list[EmotionHeatmapZone]:
        forecast_lookup: dict[tuple[str, str, str], float] = {}
        for forecast in forecasts:
            if forecast.metric == "burnout" and forecast.period in {"30_days", "90_days"}:
                forecast_lookup[(forecast.scope, forecast.entity_id, forecast.period)] = forecast.projected_score

        zones: list[EmotionHeatmapZone] = []
        company_status = self._health_status(summary.organizational_health_score)
        zones.append(
            EmotionHeatmapZone(
                scope="company",
                entity_id="company",
                label="Company Health",
                department="Enterprise",
                health_index=summary.organizational_health_score,
                health_status=company_status,
                color=self._health_color(company_status),
                stress_score=summary.average_stress,
                burnout_score=summary.average_burnout,
                workload_score=round(mean([team.workload_score for team in teams] or [summary.average_stress]), 2),
                morale_score=summary.morale_forecast_90d,
                collaboration_score=round(mean([team.collaboration_score for team in teams] or [summary.average_engagement]), 2),
                productivity_health_score=round(mean([team.productivity_health_score for team in teams] or [summary.organizational_health_score]), 2),
                conflict_risk=round(mean([team.conflict_risk for team in teams] or [0]), 2),
                forecast_30d_burnout=round(mean([value for (scope, _, period), value in forecast_lookup.items() if scope == "department" and period == "30_days"] or [summary.average_burnout]), 2),
                forecast_90d_burnout=round(mean([value for (scope, _, period), value in forecast_lookup.items() if scope == "department" and period == "90_days"] or [summary.average_burnout]), 2),
                attrition_risk=round(mean([team.retention_risk for team in teams] or [0]), 2),
                trend="critical" if summary.organizational_health_score < 40 else "declining" if summary.average_stress > 58 else "stable",
                explanation=(
                    f"Company health is {round(summary.organizational_health_score)} from stress {round(summary.average_stress)}, "
                    f"burnout {round(summary.average_burnout)}, engagement {round(summary.average_engagement)}, and morale forecast {round(summary.morale_forecast_90d)}."
                ),
                recommendations=[recommendation.action for recommendation in recommendations[:3]],
                twin_evidence=[
                    f"company_digital_twin.emotion_health={round(summary.organizational_health_score)}",
                    f"company_digital_twin.burnout_hotspots={summary.high_burnout_hotspots}",
                    f"company_digital_twin.conflict_zones={summary.high_conflict_zones}",
                ],
                agent_evidence=[f"{agent.agent}: {agent.finding}" for agent in agents[:3]],
            )
        )

        team_by_department: dict[str, list[TeamEmotionScore]] = defaultdict(list)
        for team in teams:
            team_by_department[team.department].append(team)

        for department in departments:
            department_teams = team_by_department.get(department.department, [])
            forecast_30 = forecast_lookup.get(("department", department.department, "30_days"), department.burnout_score)
            forecast_90 = forecast_lookup.get(("department", department.department, "90_days"), department.burnout_score)
            zones.append(
                EmotionHeatmapZone(
                    scope="department",
                    entity_id=department.department,
                    label=department.department,
                    department=department.department,
                    health_index=department.department_health_index,
                    health_status=department.health_status,
                    color=department.health_color,
                    stress_score=department.stress_index,
                    burnout_score=department.burnout_score,
                    workload_score=round(mean([team.workload_score for team in department_teams] or [department.stress_index]), 2),
                    morale_score=department.morale_score,
                    collaboration_score=round(mean([team.collaboration_score for team in department_teams] or [department.engagement_score]), 2),
                    productivity_health_score=round(mean([team.productivity_health_score for team in department_teams] or [department.department_health_index]), 2),
                    conflict_risk=department.conflict_risk,
                    forecast_30d_burnout=round(forecast_30, 2),
                    forecast_90d_burnout=round(forecast_90, 2),
                    attrition_risk=department.retention_risk,
                    trend="critical" if department.department_health_index < 40 else "declining" if forecast_90 > department.burnout_score + 8 else "stable",
                    explanation=(
                        f"{department.department} is {department.health_status.replace('_', ' ')} because stress is {round(department.stress_index)}, "
                        f"burnout is {round(department.burnout_score)}, morale is {round(department.morale_score)}, and 90-day burnout forecast is {round(forecast_90)}."
                    ),
                    recommendations=[department.recommendation, *[recommendation.action for recommendation in recommendations[:2]]],
                    twin_evidence=[
                        f"department_digital_twin.{department.department}.health_index={round(department.department_health_index)}",
                        f"department_digital_twin.{department.department}.color={department.health_color}",
                        f"team_twin_count={len(department_teams)}",
                    ],
                    agent_evidence=[f"{agent.agent}: {agent.recommended_action}" for agent in agents[:3]],
                )
            )

        for team in teams:
            forecast_30 = forecast_lookup.get(("team", team.team, "30_days"), team.burnout_risk)
            forecast_90 = forecast_lookup.get(("team", team.team, "90_days"), team.burnout_risk)
            zones.append(
                EmotionHeatmapZone(
                    scope="team",
                    entity_id=team.team,
                    label=team.team,
                    department=team.department,
                    health_index=team.team_health_index,
                    health_status=team.health_status,
                    color=team.health_color,
                    stress_score=team.stress_score,
                    burnout_score=team.burnout_risk,
                    workload_score=team.workload_score,
                    morale_score=team.morale_score,
                    collaboration_score=team.collaboration_score,
                    productivity_health_score=team.productivity_health_score,
                    conflict_risk=team.conflict_risk,
                    forecast_30d_burnout=round(forecast_30, 2),
                    forecast_90d_burnout=round(forecast_90, 2),
                    attrition_risk=team.retention_risk,
                    trend="critical" if team.team_health_index < 40 else "declining" if forecast_90 > team.burnout_risk + 8 or team.trend == "watch" else team.trend,
                    explanation=(
                        f"{team.team} health is {round(team.team_health_index)} from workload {round(team.workload_score)}, "
                        f"stress {round(team.stress_score)}, burnout {round(team.burnout_risk)}, collaboration {round(team.collaboration_score)}, "
                        f"and productivity health {round(team.productivity_health_score)}."
                    ),
                    recommendations=[team.recommendation, *[recommendation.action for recommendation in recommendations[:2]]],
                    twin_evidence=[
                        f"team_digital_twin.{team.team}.health_index={round(team.team_health_index)}",
                        f"team_digital_twin.{team.team}.health_color={team.health_color}",
                        f"department_digital_twin.{team.department}.linked_team={team.team}",
                    ],
                    agent_evidence=[f"{agent.agent}: {agent.finding}" for agent in agents[:4]],
                )
            )

        return sorted(zones, key=lambda zone: (zone.scope != "company", zone.health_index))[:32]

    def _emotion_3d_nodes(
        self,
        employees: list[EmployeeEmotionScore],
        teams: list[TeamEmotionScore],
        departments: list[DepartmentEmotionScore],
    ) -> list[Emotion3DNode]:
        nodes: list[Emotion3DNode] = []
        for index, department in enumerate(departments):
            angle = index * 2.1
            intensity = self._clip(max(department.stress_index, department.burnout_score, department.conflict_risk, 100 - department.morale_score))
            nodes.append(
                Emotion3DNode(
                    node_id=f"department-{department.department}",
                    label=department.department,
                    scope="department",
                    department=department.department,
                    x=round(index * 2.6 - 4.0, 2),
                    y=round((department.morale_score - 50) / 12, 2),
                    z=round((department.conflict_risk - 50) / 11 + angle * 0.2, 2),
                    stress=department.stress_index,
                    burnout=department.burnout_score,
                    morale=department.morale_score,
                    conflict=department.conflict_risk,
                    intensity=round(intensity, 2),
                    color=self._color(self._priority(intensity)),
                )
            )
        for index, team in enumerate(teams[:10]):
            intensity = self._clip(max(team.stress_score, team.burnout_risk, team.conflict_risk, 100 - team.morale_score))
            nodes.append(
                Emotion3DNode(
                    node_id=f"team-{team.team}",
                    label=team.team,
                    scope="team",
                    department=team.department,
                    x=round((index % 5) * 1.7 - 3.4, 2),
                    y=round((team.morale_score - 50) / 14, 2),
                    z=round((index // 5) * 1.8 + (team.conflict_risk - 45) / 18, 2),
                    stress=team.stress_score,
                    burnout=team.burnout_risk,
                    morale=team.morale_score,
                    conflict=team.conflict_risk,
                    intensity=round(intensity, 2),
                    color=self._color(self._priority(intensity)),
                )
            )
        for index, employee in enumerate(employees[:12]):
            intensity = self._clip(max(employee.stress_score, employee.burnout_score, employee.conflict_exposure, employee.psychological_risk))
            nodes.append(
                Emotion3DNode(
                    node_id=f"employee-{employee.employee_id}",
                    label=employee.name,
                    scope="employee",
                    department=employee.department,
                    x=round((index % 6) * 1.15 - 3.0, 2),
                    y=round((employee.morale_score - 50) / 18, 2),
                    z=round((index // 6) * 1.4 + (employee.conflict_exposure - 40) / 22, 2),
                    stress=employee.stress_score,
                    burnout=employee.burnout_score,
                    morale=employee.morale_score,
                    conflict=employee.conflict_exposure,
                    intensity=round(intensity, 2),
                    color=self._color(self._priority(intensity)),
                )
            )
        return sorted(nodes, key=lambda item: item.intensity, reverse=True)[:28]

    def _data_pipeline_status(self, request: CompanyEmotionMapRequest) -> list[EmotionDataPipelineStatus]:
        channel_counts: dict[str, int] = defaultdict(int)
        for employee in request.employees:
            channel_counts["survey"] += 1
            channel_counts["workload"] += 1 if employee.workload_hours or employee.task_load else 0
            channel_counts["engagement"] += 1 if employee.learning_participation or employee.collaboration_score else 0
            channel_counts["project_activity"] += 1 if employee.project else 0
            channel_counts["attendance"] += 1 if employee.focus_hours >= 0 else 0
            channel_counts["performance_review"] += 1 if employee.performance_trend or employee.productivity_trend else 0
            for sample in employee.communication_samples:
                channel_counts[sample.channel] += 1
        source_map = [
            ("survey", channel_counts["survey"], "Aggregated survey scoring; individual raw answers remain scoped to HR analytics.", "hr_emotion_read"),
            ("feedback", channel_counts["feedback"], "Approved feedback text is NLP-scored and retained as minimal evidence snippets.", "manager_feedback_read"),
            ("meeting", channel_counts["meeting"], "Meeting notes are processed only when approved for organizational intelligence.", "meeting_intelligence_read"),
            ("chat", channel_counts["chat"], "Chat content uses approved samples and converts to aggregate emotion signals.", "communication_metadata_read"),
            ("email_metadata", channel_counts["email"], "Email analysis is limited to approved sentiment snippets and metadata-derived risk signals.", "email_metadata_only"),
            ("performance_review", channel_counts["performance_review"], "Performance trend inputs are aggregated before dashboard exposure.", "performance_summary_read"),
            ("engagement", channel_counts["engagement"], "Learning, recognition, and collaboration activity are aggregated by team.", "engagement_summary_read"),
            ("workload", channel_counts["workload"], "Workload, overtime, focus, and meeting load are scored without exposing private calendar details.", "workload_summary_read"),
            ("project_activity", channel_counts["project_activity"], "Project pressure is linked to team digital twins and delivery telemetry.", "project_summary_read"),
            ("attendance", channel_counts["attendance"], "Availability intelligence uses focus and availability trends, not raw surveillance.", "availability_summary_read"),
        ]
        return [
            EmotionDataPipelineStatus(
                source=source,  # type: ignore[arg-type]
                signals_processed=count,
                privacy_control=privacy,
                permission_scope=scope,
                status="active" if count else "limited",
            )
            for source, count, privacy, scope in source_map
        ]

    @staticmethod
    def _privacy_controls() -> list[str]:
        return [
            "Approved signals only: survey, feedback, meeting notes, chat samples, email metadata, workload, engagement, project, and availability trends.",
            "Email processing is metadata/approved-signal based; no private mailbox scraping is required.",
            "Role-scoped access: executives see aggregate heatmaps, HR sees employee risk details, managers see assigned teams.",
            "Evidence snippets are minimized and persisted as JSONL audit history for traceable model outputs.",
            "Digital twin updates write aggregate emotion state, not raw private communications.",
        ]

    def _agent_council(
        self,
        summary_inputs: tuple[
            list[EmployeeEmotionScore],
            list[TeamEmotionScore],
            list[DepartmentEmotionScore],
            list[ConflictRiskInsight],
            list[BurnoutPrediction],
            list[EmotionRecommendation],
        ],
    ) -> list[EmotionAgentContribution]:
        employees, teams, departments, conflicts, burnouts, recommendations = summary_inputs
        top_department = max(departments, key=lambda item: item.stress_index, default=None)
        top_burnout = max(burnouts, key=lambda item: item.forecast_90d, default=None)
        top_conflict = max(conflicts, key=lambda item: item.conflict_probability, default=None)
        top_recommendation = recommendations[0].action if recommendations else "Continue emotion radar monitoring."
        return [
            EmotionAgentContribution(
                agent="HR Agent",
                domain="Wellness Analysis",
                finding=f"{top_burnout.label if top_burnout else 'No entity'} has the highest burnout forecast.",
                recommended_action=top_burnout.recommendation if top_burnout else "Maintain wellness review cadence.",
                confidence=0.9,
            ),
            EmotionAgentContribution(
                agent="Productivity Agent",
                domain="Workload Analysis",
                finding=f"{top_department.department if top_department else 'No department'} has the highest stress hotspot.",
                recommended_action=top_department.recommendation if top_department else "Keep workload telemetry active.",
                confidence=0.87,
            ),
            EmotionAgentContribution(
                agent="Risk Agent",
                domain="Conflict Forecasts",
                finding=f"{top_conflict.source_entity if top_conflict else 'No active conflict'} drives the top conflict probability.",
                recommended_action=top_conflict.recommended_action if top_conflict else "Continue conflict monitoring.",
                confidence=0.86,
            ),
            EmotionAgentContribution(
                agent="Executive Agent",
                domain="Recommendations",
                finding=f"Emotion radar is tracking {len(employees)} employees and {len(teams)} teams.",
                recommended_action=top_recommendation,
                confidence=0.91,
            ),
        ]

    def _production_readiness_score(
        self,
        data_pipeline: list[EmotionDataPipelineStatus],
        heatmap: list[EmotionHeatmapPoint],
        nodes: list[Emotion3DNode],
        recommendations: list[EmotionRecommendation],
        agents: list[EmotionAgentContribution],
    ) -> float:
        active_sources = sum(1 for source in data_pipeline if source.status == "active")
        score = active_sources / max(1, len(data_pipeline)) * 38
        score += min(22, len(heatmap) / 80 * 22)
        score += min(16, len(nodes) / 20 * 16)
        score += min(12, len(recommendations) * 3)
        score += min(12, len(agents) * 3)
        return round(self._clip(score), 2)

    def _innovation_score(
        self,
        nodes: list[Emotion3DNode],
        forecasts: list[EmotionForecastPoint],
        conflicts: list[ConflictRiskInsight],
        burnouts: list[BurnoutPrediction],
        toxic_teams: list[TeamEmotionClassification],
        happy_teams: list[TeamEmotionClassification],
        silent_risks: list[SilentEmployeeRisk],
    ) -> float:
        coverage = len({forecast.metric for forecast in forecasts}) / 7 * 30
        visualization = min(22, len(nodes) / 20 * 22)
        prediction = min(22, (len(conflicts) + len(burnouts)) / 14 * 22)
        behavioral = min(16, (len(toxic_teams) + len(happy_teams) + len(silent_risks)) / 4 * 16)
        council = 10
        return round(self._clip(coverage + visualization + prediction + behavioral + council), 2)

    def _summary(
        self,
        employees: list[EmployeeEmotionScore],
        teams: list[TeamEmotionScore],
        departments: list[DepartmentEmotionScore],
        heatmap: list[EmotionHeatmapPoint],
        forecasts: list[EmotionForecastPoint],
        conflicts: list[ConflictRiskInsight],
    ) -> CompanyEmotionMapSummary:
        avg_happiness = mean([employee.happiness_score for employee in employees] or [0])
        avg_stress = mean([employee.stress_score for employee in employees] or [0])
        avg_burnout = mean([employee.burnout_score for employee in employees] or [0])
        avg_motivation = mean([employee.motivation_score for employee in employees] or [0])
        avg_engagement = mean([employee.engagement_score for employee in employees] or [0])
        morale_90 = mean(
            [
                forecast.projected_score
                for forecast in forecasts
                if forecast.metric == "morale" and forecast.period == "90_days" and forecast.scope == "department"
            ]
            or [mean([department.morale_score for department in departments] or [0])]
        )
        health = self._clip(avg_happiness * 0.2 + avg_engagement * 0.2 + avg_motivation * 0.16 + morale_90 * 0.18 + (100 - avg_stress) * 0.13 + (100 - avg_burnout) * 0.13)
        return CompanyEmotionMapSummary(
            employees_analyzed=len(employees),
            teams_analyzed=len(teams),
            departments_analyzed=len(departments),
            high_stress_hotspots=sum(1 for point in heatmap if point.metric == "stress" and point.risk_score >= 65),
            high_burnout_hotspots=sum(1 for point in heatmap if point.metric == "burnout" and point.risk_score >= 65),
            high_conflict_zones=sum(1 for conflict in conflicts if conflict.conflict_probability >= 58),
            average_happiness=round(avg_happiness, 2),
            average_stress=round(avg_stress, 2),
            average_burnout=round(avg_burnout, 2),
            average_motivation=round(avg_motivation, 2),
            average_engagement=round(avg_engagement, 2),
            morale_forecast_90d=round(morale_90, 2),
            organizational_health_score=round(health, 2),
            company_health_status=self._health_status(health),
            company_health_color=self._health_color(self._health_status(health)),
        )

    @staticmethod
    def _executive_insights(
        summary: CompanyEmotionMapSummary,
        employees: list[EmployeeEmotionScore],
        teams: list[TeamEmotionScore],
        departments: list[DepartmentEmotionScore],
        recommendations: list[EmotionRecommendation],
    ) -> list[str]:
        insights = [
            f"Organizational emotion health is {round(summary.organizational_health_score)} with average stress {round(summary.average_stress)} and burnout {round(summary.average_burnout)}.",
            f"The digital twin is tracking {summary.employees_analyzed} employees across {summary.teams_analyzed} teams and {summary.departments_analyzed} departments.",
        ]
        if departments:
            top = departments[0]
            insights.append(f"{top.department} is the highest emotional risk zone with stress {round(top.stress_index)}, burnout {round(top.burnout_score)}, and conflict {round(top.conflict_risk)}.")
        if employees:
            risk_employee = employees[0]
            insights.append(f"Highest individual risk signal is {risk_employee.name} at {round(risk_employee.psychological_risk)} psychological risk.")
        if teams:
            risk_team = teams[0]
            insights.append(f"Highest-risk team is {risk_team.team}; recommended action is: {risk_team.recommendation}")
        if recommendations:
            insights.append(f"Top intervention: {recommendations[0].action}")
        return insights

    @staticmethod
    def _digital_twin_updates(
        summary: CompanyEmotionMapSummary,
        employees: list[EmployeeEmotionScore],
        teams: list[TeamEmotionScore],
        departments: list[DepartmentEmotionScore],
    ) -> list[str]:
        updates = [
            f"company_digital_twin.emotion_health={round(summary.organizational_health_score)}",
            f"company_digital_twin.health_status={summary.company_health_status}",
            f"company_digital_twin.health_color={summary.company_health_color}",
            f"company_digital_twin.burnout_hotspots={summary.high_burnout_hotspots}",
            f"company_digital_twin.conflict_zones={summary.high_conflict_zones}",
            f"company_digital_twin.production_readiness={round(summary.production_readiness_score)}",
        ]
        updates.extend([f"employee_digital_twin.{employee.employee_id}.psychological_risk={round(employee.psychological_risk)}" for employee in employees[:3]])
        updates.extend([f"team_digital_twin.{team.team}.health_index={round(team.team_health_index)}" for team in teams[:3]])
        updates.extend([f"team_digital_twin.{team.team}.stress={round(team.stress_score)}" for team in teams[:3]])
        updates.extend([f"department_digital_twin.{department.department}.health_index={round(department.department_health_index)}" for department in departments[:3]])
        updates.extend([f"department_digital_twin.{department.department}.morale={round(department.morale_score)}" for department in departments[:3]])
        return updates

    @staticmethod
    def _workflow_triggers(
        recommendations: list[EmotionRecommendation],
        conflicts: list[ConflictRiskInsight],
        burnouts: list[BurnoutPrediction],
    ) -> list[str]:
        triggers = [recommendation.triggered_workflow for recommendation in recommendations]
        if any(conflict.conflict_probability >= 70 for conflict in conflicts):
            triggers.append("workflow_automation.executive_conflict_escalation")
        if any(prediction.forecast_90d >= 80 for prediction in burnouts):
            triggers.append("workflow_automation.recovery_leave_review")
        return list(dict.fromkeys(triggers))

    def _assistant_intent(self, question: str) -> EmotionAssistantIntent:
        normalized = question.lower()
        if any(token in normalized for token in ["stress", "stressed", "pressure"]):
            return "stress"
        if any(token in normalized for token in ["burnout", "fatigue", "overwork"]):
            return "burnout"
        if any(token in normalized for token in ["conflict", "toxic", "breakdown"]):
            if "toxic" in normalized:
                return "toxic"
            return "conflict"
        if any(token in normalized for token in ["silent", "withdraw", "isolated", "isolation"]):
            return "silent"
        if any(token in normalized for token in ["morale", "health"]):
            return "morale"
        if any(token in normalized for token in ["happiness", "happy"]):
            return "happiness"
        if any(token in normalized for token in ["forecast", "predict", "next quarter", "future"]):
            return "forecast"
        if any(token in normalized for token in ["motivation", "engagement"]):
            return "motivation"
        if any(token in normalized for token in ["recommend", "action", "intervention"]):
            return "recommendation"
        return "summary"

    @staticmethod
    def _assistant_answer(
        intent: EmotionAssistantIntent,
        analysis: CompanyEmotionMapResponse,
    ) -> tuple[str, float, list[str], list[str], list[str]]:
        if intent == "stress":
            top = max(analysis.department_scores, key=lambda item: item.stress_index)
            return (
                f"{top.department} is most stressed at {round(top.stress_index)} with burnout {round(top.burnout_score)} and retention risk {round(top.retention_risk)}.",
                0.9,
                [top.department],
                [top.recommendation],
                [f"stress_index={top.stress_index}", f"headcount={top.headcount}", f"priority={top.priority}"],
            )
        if intent == "burnout":
            top = analysis.burnout_predictions[0]
            return (
                f"Top burnout hotspot is {top.label} with 90-day forecast {round(top.forecast_90d)} and mental workload pressure {round(top.mental_workload_pressure)}.",
                0.89,
                [top.label],
                [top.recommendation],
                [f"forecast_30d={top.forecast_30d}", f"forecast_90d={top.forecast_90d}", f"scope={top.scope}"],
            )
        if intent == "conflict":
            top = analysis.conflict_risks[0] if analysis.conflict_risks else None
            if not top:
                return "No conflict hotspot currently exceeds the intervention threshold.", 0.78, [], ["Continue passive conflict monitoring."], []
            return (
                f"Highest conflict risk is {top.source_entity} to {top.target_entity} at {round(top.conflict_probability)}.",
                0.88,
                [top.source_entity, top.target_entity],
                [top.recommended_action],
                top.evidence,
            )
        if intent == "toxic":
            top = analysis.toxic_team_risks[0] if analysis.toxic_team_risks else None
            if not top:
                return "No team currently meets the toxic-team threshold.", 0.79, [], ["Continue communication and morale monitoring."], []
            return (
                f"{top.team} has the highest toxic-team risk at {round(top.score)} due to {', '.join(top.drivers[:3])}.",
                0.87,
                [top.team, top.department],
                [top.recommended_action],
                [top.reason, *top.drivers],
            )
        if intent == "silent":
            top = analysis.silent_employee_risks[0] if analysis.silent_employee_risks else None
            if not top:
                return "No silent-employee risk currently exceeds the intervention threshold.", 0.78, [], ["Continue participation monitoring."], []
            return (
                f"{top.name} has the highest silent-employee risk at {round(top.isolation_risk)} with withdrawal score {round(top.communication_withdrawal_score)}.",
                0.86,
                [top.name, top.team],
                [top.recommended_action],
                [top.reason, f"participation_delta={top.participation_delta}"],
            )
        if intent == "forecast":
            top = analysis.forecasts[0]
            return (
                f"Highest forecast risk is {top.metric} for {top.label} in {top.period} with risk probability {round(top.risk_probability)}.",
                0.86,
                [top.label],
                [analysis.recommendations[0].action] if analysis.recommendations else ["Review forecast heatmap weekly."],
                [top.driver, f"confidence={top.confidence}"],
            )
        if intent in {"morale", "happiness"}:
            weakest = min(analysis.department_scores, key=lambda item: item.morale_score if intent == "morale" else item.happiness_score)
            metric = weakest.morale_score if intent == "morale" else weakest.happiness_score
            return (
                f"{weakest.department} has the lowest {intent} signal at {round(metric)}.",
                0.84,
                [weakest.department],
                [weakest.recommendation],
                [f"engagement={weakest.engagement_score}", f"motivation={weakest.motivation_index}", f"burnout={weakest.burnout_score}"],
            )
        if intent == "motivation":
            weakest = analysis.motivation_trends[0]
            return (
                f"Motivation decline is strongest for {weakest.label}; trend delta is {round(weakest.trend_delta)}.",
                0.84,
                [weakest.label],
                [weakest.recommendation],
                weakest.drivers,
            )
        if intent == "recommendation":
            rec = analysis.recommendations[0]
            return rec.action, rec.confidence, [rec.title], [rec.action], [rec.rationale, rec.triggered_workflow]
        summary = analysis.summary
        return (
            f"Company emotion health is {round(summary.organizational_health_score)} with {summary.high_stress_hotspots} stress hotspots, {summary.high_burnout_hotspots} burnout hotspots, and {summary.high_conflict_zones} conflict zones.",
            0.82,
            ["Company Emotion Map"],
            [analysis.recommendations[0].action] if analysis.recommendations else ["Continue monitoring."],
            [f"employees={summary.employees_analyzed}", f"teams={summary.teams_analyzed}", f"departments={summary.departments_analyzed}"],
        )

    def _scenario_variant(self, base: CompanyEmotionMapRequest, stress_delta: float, motivation_delta: float, conflict_delta: int) -> CompanyEmotionMapRequest:
        employees = []
        for employee in base.employees:
            updated_samples = [
                sample.model_copy(update={"text": f"{sample.text} Emotional pressure increased and recovery capacity is lower."})
                for sample in employee.communication_samples
            ]
            employees.append(
                employee.model_copy(
                    update={
                        "survey_score": self._clip(employee.survey_score - stress_delta * 0.45),
                        "communication_samples": updated_samples,
                        "overtime_hours": min(80, employee.overtime_hours + stress_delta * 0.38),
                        "meeting_hours": min(60, employee.meeting_hours + stress_delta * 0.28),
                        "task_load": min(140, employee.task_load + stress_delta * 0.9),
                        "focus_hours": max(0, employee.focus_hours - stress_delta * 0.07),
                        "productivity_trend": max(-100, employee.productivity_trend + motivation_delta),
                        "performance_trend": max(-100, employee.performance_trend + motivation_delta * 0.6),
                        "learning_participation": self._clip(employee.learning_participation + motivation_delta),
                        "collaboration_score": self._clip(employee.collaboration_score - stress_delta * 0.42),
                        "manager_support_score": self._clip(employee.manager_support_score - stress_delta * 0.3),
                        "conflict_events": min(100, employee.conflict_events + conflict_delta),
                        "negative_interactions": min(500, employee.negative_interactions + conflict_delta * 2),
                        "positive_interactions": max(0, employee.positive_interactions - conflict_delta),
                        "attrition_risk": self._clip(employee.attrition_risk + stress_delta * 0.7),
                    }
                )
            )
        interactions = [
            interaction.model_copy(
                update={
                    "sentiment_alignment": max(-1, interaction.sentiment_alignment - stress_delta * 0.025),
                    "unresolved_issues": min(100, interaction.unresolved_issues + conflict_delta),
                    "escalation_count": min(100, interaction.escalation_count + (1 if conflict_delta else 0)),
                    "evidence": [*interaction.evidence, "Scenario pressure increased emotional risk."],
                }
            )
            for interaction in base.interactions
        ]
        return base.model_copy(update={"employees": employees, "interactions": interactions, "realtime": True})

    def _heatmap_point(
        self,
        scope: EmotionScope,
        entity_id: str,
        label: str,
        department: str,
        metric: EmotionMetric,
        value: float,
    ) -> EmotionHeatmapPoint:
        risk = value if metric in {"stress", "burnout", "conflict"} else 100 - value
        intensity = max(value, risk)
        priority = self._priority(risk)
        return EmotionHeatmapPoint(
            scope=scope,
            entity_id=entity_id,
            label=label,
            department=department,
            metric=metric,
            value=round(self._clip(value), 2),
            risk_score=round(self._clip(risk), 2),
            intensity=round(self._clip(intensity), 2),
            priority=priority,
            color=self._color(priority),
        )

    @staticmethod
    def _employee_text(employee: EmployeeEmotionSignal) -> str:
        texts = [sample.text for sample in employee.communication_samples]
        if not texts:
            texts.append(
                f"{employee.name} survey score is {employee.survey_score}, workload is {employee.task_load}, "
                f"collaboration is {employee.collaboration_score}, and overtime is {employee.overtime_hours}."
            )
        return " ".join(texts)[:4000]

    @staticmethod
    def _interaction_risk(interaction: TeamInteractionSignal) -> float:
        return max(
            0.0,
            min(
                100.0,
                max(0, -interaction.sentiment_alignment) * 45
                + interaction.unresolved_issues * 5.6
                + interaction.escalation_count * 8.5
                + min(100, interaction.communication_volume) * 0.08,
            ),
        )

    @staticmethod
    def _priority(score: float) -> EmotionPriority:
        if score >= 82:
            return "critical"
        if score >= 64:
            return "high"
        if score >= 38:
            return "medium"
        return "low"

    @staticmethod
    def _color(priority: EmotionPriority) -> str:
        return {
            "low": "#7CF0A6",
            "medium": "#F6B44B",
            "high": "#F97316",
            "critical": "#FF3B6B",
        }[priority]

    @staticmethod
    def _health_status(health_index: float) -> EmotionHealthStatus:
        if health_index >= 80:
            return "healthy"
        if health_index >= 60:
            return "attention_needed"
        if health_index >= 40:
            return "overloaded"
        return "critical"

    @staticmethod
    def _health_color(status: EmotionHealthStatus) -> str:
        return {
            "healthy": "#7CF0A6",
            "attention_needed": "#F6B44B",
            "overloaded": "#F97316",
            "critical": "#FF3B6B",
        }[status]

    @staticmethod
    def _clip(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
        return max(minimum, min(maximum, float(value)))

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


company_emotion_map_service = CompanyEmotionMapService()
