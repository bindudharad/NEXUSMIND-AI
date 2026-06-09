from __future__ import annotations

import asyncio
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

import numpy as np

from app.ai.innovation_engine import innovation_scoring_engine
from app.core.cache import TTLResponseCache
from app.schemas.innovation import (
    EmployeeInnovationScore,
    EmployeeInnovationProfile,
    GrowthTrajectoryForecast,
    HiddenTalentInsight,
    IdeaImpactForecast,
    IdeaMiningInsight,
    InnovationAssistantRequest,
    InnovationAssistantResponse,
    InnovationAlert,
    InnovationIdeaSignal,
    InnovationPriority,
    InnovationRecommendation,
    InnovationRequest,
    InnovationResponse,
    InnovationSummary,
    LeadershipPotentialInsight,
    ProblemSolvingInsight,
    PromotionRecommendation,
    TalentRiskInsight,
    InnovationTrendPoint,
    TeamInnovationHeatmapPoint,
)
from app.schemas.nlp import NLPAnalyzeRequest
from app.services.nlp_service import nlp_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "innovation_scoring_history.jsonl"
INNOVATION_TERMS = {
    "ai",
    "automation",
    "autonomous",
    "architecture",
    "optimize",
    "prototype",
    "experiment",
    "graph",
    "vector",
    "latency",
    "cost",
    "revenue",
    "workflow",
    "deployment",
    "resilience",
    "prediction",
    "research",
    "self-healing",
    "knowledge",
    "platform",
}


class InnovationScoringService:
    model_name = "PyTorch TextEmotionNet + TF-IDF Innovation Impact Ensemble"

    def __init__(self) -> None:
        self._default_cache: TTLResponseCache[InnovationResponse] = TTLResponseCache(ttl_seconds=8)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def score(self, payload: InnovationRequest | None = None) -> InnovationResponse:
        if payload is None:
            return self._default_cache.get_or_set(self._score_default_uncached)
        return self._score_uncached(payload)

    def _score_default_uncached(self) -> InnovationResponse:
        return self._score_uncached(self.default_request())

    def _score_uncached(self, payload: InnovationRequest) -> InnovationResponse:
        request = payload if payload.ideas else self.default_request()
        idea_insights = [self._idea_insight(idea) for idea in request.ideas]
        employee_scores = self._employee_scores(request.ideas, idea_insights)
        profiles = self._profiles(request.ideas, employee_scores, request.employee_profiles)
        hidden_talent = self._hidden_talent(employee_scores, idea_insights, profiles)
        leadership_predictions = self._leadership_predictions(employee_scores, idea_insights, profiles)
        problem_solving = self._problem_solving(employee_scores, idea_insights, profiles)
        growth_forecasts = self._growth_forecasts(employee_scores, profiles, leadership_predictions)
        talent_risks = self._talent_risks(employee_scores, profiles, hidden_talent)
        promotion_recommendations = self._promotion_recommendations(employee_scores, leadership_predictions, hidden_talent, talent_risks)
        team_heatmap = self._team_heatmap(request.ideas, idea_insights, employee_scores)
        forecasts = self._impact_forecasts(request.ideas, idea_insights, request.horizon_days)
        trend_points = self._trend_points(request.ideas, idea_insights)
        recommendations = self._recommendations(request.ideas, idea_insights, employee_scores, team_heatmap, hidden_talent, leadership_predictions)
        alerts = self._alerts(idea_insights, employee_scores, team_heatmap)
        response = InnovationResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            cycle_name=request.cycle_name,
            horizon_days=request.horizon_days,
            idea_insights=sorted(idea_insights, key=lambda item: item.impact_score, reverse=True),
            employee_scores=employee_scores,
            hidden_talent=hidden_talent,
            leadership_predictions=leadership_predictions,
            problem_solving_insights=problem_solving,
            growth_forecasts=growth_forecasts,
            talent_risks=talent_risks,
            promotion_recommendations=promotion_recommendations,
            team_heatmap=sorted(team_heatmap, key=lambda item: item.innovation_score, reverse=True),
            impact_forecasts=sorted(forecasts, key=lambda item: item.predicted_business_impact, reverse=True),
            trend_points=trend_points,
            recommendations=recommendations,
            alerts=alerts,
            executive_insights=self._executive_insights(idea_insights, employee_scores, team_heatmap, hidden_talent, leadership_predictions),
            summary=self._summary(idea_insights, employee_scores, forecasts, hidden_talent, leadership_predictions, promotion_recommendations, talent_risks, growth_forecasts),
            source_systems=self.source_systems(),
            digital_twin_updates=self._digital_twin_updates(hidden_talent, leadership_predictions, talent_risks),
            marketplace_updates=self._marketplace_updates(hidden_talent, promotion_recommendations),
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    def ask(self, payload: InnovationAssistantRequest) -> InnovationAssistantResponse:
        analysis = self.score()
        question = payload.question.lower()
        if any(token in question for token in ["future leader", "leader", "manager", "architect"]):
            intent = "leaders"
            rows = analysis.leadership_predictions[:3]
            answer = "Future leadership candidates are " + ", ".join(
                f"{row.employee_name} ({round(row.leadership_potential)}%)" for row in rows
            ) + "."
            actions = [analysis.promotion_recommendations[0].action] if analysis.promotion_recommendations else []
            evidence = [row.reason for row in rows]
            employees = [row.employee_name for row in rows]
        elif any(token in question for token in ["hidden", "under-recognized", "underrated", "talent"]):
            intent = "hidden_talent"
            rows = analysis.hidden_talent[:3]
            answer = "Hidden talent signals are strongest for " + ", ".join(
                f"{row.employee_name} ({round(row.hidden_talent_score)}%)" for row in rows
            ) + "."
            actions = [row.reason for row in rows]
            evidence = [", ".join(row.evidence[:2]) for row in rows]
            employees = [row.employee_name for row in rows]
        elif any(token in question for token in ["promote", "promotion", "promoted"]):
            intent = "promotion"
            rows = analysis.promotion_recommendations[:3]
            answer = "Promotion-readiness recommendations prioritize " + ", ".join(
                f"{row.employee_name} for {row.target_program}" for row in rows
            ) + "."
            actions = [row.action for row in rows]
            evidence = [row.reason for row in rows]
            employees = [row.employee_name for row in rows]
        elif any(token in question for token in ["problem", "solver", "incident", "root cause"]):
            intent = "problem_solving"
            rows = analysis.problem_solving_insights[:3]
            answer = "Best problem solvers are " + ", ".join(
                f"{row.employee_name} ({round(row.problem_solving_score)}%)" for row in rows
            ) + "."
            actions = [f"Assign {row.employee_name} to {row.strength.lower()} initiatives." for row in rows]
            evidence = [", ".join(row.evidence[:2]) for row in rows]
            employees = [row.employee_name for row in rows]
        elif any(token in question for token in ["risk", "leave", "leaving", "retain", "retention"]):
            intent = "risk"
            rows = analysis.talent_risks[:3]
            answer = "Critical talent risk is highest for " + ", ".join(
                f"{row.employee_name} ({round(row.flight_risk)}% flight risk)" for row in rows
            ) + "."
            actions = [row.retention_action for row in rows]
            evidence = [row.risk_reason for row in rows]
            employees = [row.employee_name for row in rows]
        elif any(token in question for token in ["growth", "career", "trajectory"]):
            intent = "growth"
            rows = analysis.growth_forecasts[:3]
            answer = "Growth trajectory is strongest for " + ", ".join(
                f"{row.employee_name} toward {row.expected_future_role}" for row in rows
            ) + "."
            actions = [f"Place {row.employee_name} on the {row.expected_future_role} track." for row in rows]
            evidence = [", ".join(row.drivers[:2]) for row in rows]
            employees = [row.employee_name for row in rows]
        elif any(token in question for token in ["innovation", "innovator", "creative"]):
            intent = "innovation"
            rows = analysis.employee_scores[:3]
            answer = "Highest innovation potential is held by " + ", ".join(
                f"{row.employee_name} ({round(row.innovation_score)}%)" for row in rows
            ) + "."
            actions = [analysis.recommendations[0].action] if analysis.recommendations else []
            evidence = [", ".join(row.evidence[:2]) for row in rows]
            employees = [row.employee_name for row in rows]
        else:
            intent = "summary"
            answer = (
                f"The innovation detector analyzed {analysis.summary.employees_ranked} employees, found "
                f"{analysis.summary.hidden_talent_count} hidden-talent signals and "
                f"{analysis.summary.future_leaders_count} future-leader candidates."
            )
            actions = [item.action for item in analysis.promotion_recommendations[:2]]
            evidence = analysis.executive_insights[:3]
            employees = [item.employee_name for item in analysis.employee_scores[:3]]
        return InnovationAssistantResponse(
            model="AI Innovation Detector Assistant",
            generated_at=datetime.now(timezone.utc),
            question=payload.question,
            intent=intent,  # type: ignore[arg-type]
            answer=answer,
            confidence=0.88 if employees else 0.72,
            cited_employees=employees,
            recommended_actions=actions,
            evidence=evidence,
            source_systems=self.source_systems(),
            storage=str(HISTORY_PATH),
        )

    async def stream(self, payload: InnovationRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, impact_delta=0.08, adoption_delta=0.08, extra_reactions=5),
            self._scenario_variant(base, impact_delta=0.16, adoption_delta=0.14, extra_reactions=11),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.score(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: innovation_scoring\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> InnovationRequest:
        ideas = [
            InnovationIdeaSignal(
                idea_id="idea-001",
                employee_id="emp-innovation-1",
                employee_name="Aarav Mehta",
                department="Engineering",
                team="Platform Architecture",
                channel="proposal",
                text="Prototype an event-driven deployment optimizer that predicts risky diffs, batches safe changes, and triggers automated rollback when release telemetry degrades.",
                adoption_stage="piloting",
                reactions_count=34,
                cross_team_votes=14,
                collaboration_mentions=9,
                implementation_progress=0.62,
                estimated_hours_saved=420,
                estimated_cost_saving=185000,
                feasibility_signal=0.82,
                strategic_alignment=0.9,
                novelty_claim=0.86,
            ),
            InnovationIdeaSignal(
                idea_id="idea-002",
                employee_id="emp-innovation-2",
                employee_name="Maya Iyer",
                department="Product",
                team="AI Products",
                channel="meeting",
                text="Create an executive insight canvas that turns attrition, productivity, meeting waste, and project failure signals into a single explainable intervention plan.",
                adoption_stage="reviewing",
                reactions_count=29,
                cross_team_votes=16,
                collaboration_mentions=12,
                implementation_progress=0.34,
                estimated_hours_saved=260,
                estimated_revenue_impact=310000,
                feasibility_signal=0.74,
                strategic_alignment=0.88,
                novelty_claim=0.78,
            ),
            InnovationIdeaSignal(
                idea_id="idea-003",
                employee_id="emp-innovation-3",
                employee_name="Rina Shah",
                department="Quality",
                team="Release Intelligence",
                channel="chat",
                text="Use AI summaries over regression failures to cluster duplicate defects and recommend the smallest test set for each release branch.",
                adoption_stage="adopted",
                reactions_count=41,
                cross_team_votes=11,
                collaboration_mentions=10,
                implementation_progress=0.86,
                estimated_hours_saved=510,
                estimated_cost_saving=142000,
                feasibility_signal=0.9,
                strategic_alignment=0.78,
                novelty_claim=0.72,
            ),
            InnovationIdeaSignal(
                idea_id="idea-004",
                employee_id="emp-innovation-4",
                employee_name="Omar Singh",
                department="Operations",
                team="Incident Response",
                channel="research",
                text="Build self-healing incident runbooks that use postmortem retrieval and dependency graphs to restore known service states without manual escalation.",
                adoption_stage="reviewing",
                reactions_count=22,
                cross_team_votes=9,
                collaboration_mentions=7,
                implementation_progress=0.24,
                estimated_hours_saved=340,
                estimated_cost_saving=98000,
                feasibility_signal=0.66,
                strategic_alignment=0.84,
                novelty_claim=0.88,
            ),
            InnovationIdeaSignal(
                idea_id="idea-005",
                employee_id="emp-innovation-5",
                employee_name="Devika Nair",
                department="Design",
                team="Design Systems",
                channel="ticket",
                text="Update dashboard copy and visual grouping so managers can understand the difference between risk, recommendation, and intervention states.",
                adoption_stage="submitted",
                reactions_count=8,
                cross_team_votes=2,
                collaboration_mentions=3,
                implementation_progress=0.08,
                estimated_hours_saved=60,
                feasibility_signal=0.82,
                strategic_alignment=0.52,
                novelty_claim=0.38,
            ),
        ]
        return InnovationRequest(cycle_name="Realtime Innovation Scoring Review", horizon_days=90, ideas=ideas)

    def _idea_insight(self, idea: InnovationIdeaSignal) -> IdeaMiningInsight:
        nlp = nlp_service.analyze(
            NLPAnalyzeRequest(
                employee_id=idea.employee_id,
                department=idea.department,
                channel=idea.channel,
                text=idea.text,
            )
        )
        model = innovation_scoring_engine.predict_text(idea.text)
        keywords = self._keywords(idea.text)
        term_density = len(set(keywords) & INNOVATION_TERMS) / max(1, min(8, len(keywords)))
        adoption_bonus = {"submitted": 0, "reviewing": 7, "piloting": 14, "adopted": 21, "rejected": -16}[idea.adoption_stage]
        social_signal = self._clip100(idea.reactions_count * 0.9 + idea.cross_team_votes * 1.8 + idea.collaboration_mentions * 1.4)
        business_signal = self._clip100(idea.estimated_hours_saved / 8 + idea.estimated_cost_saving / 4500 + idea.estimated_revenue_impact / 6500)
        originality = self._clip100(
            float(model["originality_probability"]) * 58
            + idea.novelty_claim * 24
            + term_density * 18
            + max(0, nlp.sentiment_score) * 4
        )
        feasibility = self._clip100(float(model["adoption_probability"]) * 45 + idea.feasibility_signal * 38 + idea.implementation_progress * 17)
        impact = self._clip100(
            float(model["impact_probability"]) * 46
            + idea.strategic_alignment * 20
            + business_signal * 0.2
            + social_signal * 0.14
            + adoption_bonus
        )
        adoption = self._clip100(
            float(model["adoption_probability"]) * 42
            + idea.implementation_progress * 28
            + idea.feasibility_signal * 18
            + social_signal * 0.12
            + adoption_bonus * 0.5
        )
        theme = self._theme(model["category"], keywords)
        return IdeaMiningInsight(
            idea_id=idea.idea_id,
            employee_id=idea.employee_id,
            employee_name=idea.employee_name,
            department=idea.department,
            team=idea.team,
            channel=idea.channel,
            idea_category=str(model["category"]),
            extracted_theme=theme,
            originality_score=round(originality, 2),
            feasibility_score=round(feasibility, 2),
            impact_score=round(impact, 2),
            adoption_probability=round(adoption, 2),
            confidence=round(max(float(model["confidence"]), nlp.confidence), 3),
            evidence=[
                f"nlp_sentiment={nlp.sentiment} score={nlp.sentiment_score}",
                f"category={model['category']} confidence={round(float(model['category_confidence']) * 100)}%",
                f"business_signal={round(business_signal)}",
                f"social_signal={round(social_signal)}",
                f"stage={idea.adoption_stage}",
            ],
            extracted_keywords=keywords[:8],
            recommendation=self._idea_recommendation(impact, originality, feasibility, adoption),
        )

    def _employee_scores(self, ideas: list[InnovationIdeaSignal], insights: list[IdeaMiningInsight]) -> list[EmployeeInnovationScore]:
        idea_lookup = {idea.idea_id: idea for idea in ideas}
        grouped: dict[str, list[IdeaMiningInsight]] = defaultdict(list)
        for insight in insights:
            grouped[insight.employee_id].append(insight)
        rows: list[EmployeeInnovationScore] = []
        for employee_id, employee_ideas in grouped.items():
            source = employee_ideas[0]
            idea_sources = [idea_lookup[item.idea_id] for item in employee_ideas]
            adoption_rate = mean([self._stage_score(idea.adoption_stage) for idea in idea_sources])
            social = mean([self._clip100(idea.reactions_count + idea.cross_team_votes * 2.2 + idea.collaboration_mentions * 1.8) for idea in idea_sources])
            originality = mean([item.originality_score for item in employee_ideas])
            impact = mean([item.impact_score for item in employee_ideas])
            frequency = len(employee_ideas)
            score = self._clip100(impact * 0.34 + originality * 0.25 + adoption_rate * 0.17 + social * 0.14 + min(100, frequency * 12) * 0.1)
            top = max(employee_ideas, key=lambda item: item.impact_score)
            rows.append(
                EmployeeInnovationScore(
                    employee_id=employee_id,
                    employee_name=source.employee_name,
                    department=source.department,
                    team=source.team,
                    innovation_score=round(score, 2),
                    originality_score=round(originality, 2),
                    idea_impact_score=round(impact, 2),
                    contribution_frequency=frequency,
                    adoption_rate=round(adoption_rate, 2),
                    collaboration_influence=round(social, 2),
                    creativity_rank=1,
                    top_idea=top.extracted_theme,
                    evidence=[
                        f"{frequency} idea(s) analyzed",
                        f"average impact {round(impact)}",
                        f"average originality {round(originality)}",
                        f"adoption signal {round(adoption_rate)}",
                    ],
                )
            )
        rows.sort(key=lambda item: item.innovation_score, reverse=True)
        return [row.model_copy(update={"creativity_rank": index}) for index, row in enumerate(rows, start=1)]

    def _profiles(
        self,
        ideas: list[InnovationIdeaSignal],
        employee_scores: list[EmployeeInnovationScore],
        supplied: list[EmployeeInnovationProfile],
    ) -> dict[str, EmployeeInnovationProfile]:
        profiles = {profile.employee_id: profile for profile in supplied}
        ideas_by_employee: dict[str, list[InnovationIdeaSignal]] = defaultdict(list)
        for idea in ideas:
            ideas_by_employee[idea.employee_id].append(idea)
        for score in employee_scores:
            if score.employee_id in profiles:
                continue
            rows = ideas_by_employee.get(score.employee_id, [])
            reactions = sum(idea.reactions_count for idea in rows)
            votes = sum(idea.cross_team_votes for idea in rows)
            mentions = sum(idea.collaboration_mentions for idea in rows)
            progress = mean([idea.implementation_progress for idea in rows] or [0.2])
            adopted = sum(1 for idea in rows if idea.adoption_stage in {"adopted", "piloting"})
            performance = [
                self._clip01(score.innovation_score / 100 - 0.12),
                self._clip01(score.innovation_score / 100 - 0.05),
                self._clip01(score.innovation_score / 100 + 0.02),
                self._clip01(score.innovation_score / 100 + min(0.18, progress / 4)),
            ]
            visibility = self._clip01((reactions * 0.35 + votes * 1.3 + mentions * 0.9) / 100)
            profiles[score.employee_id] = EmployeeInnovationProfile(
                employee_id=score.employee_id,
                employee_name=score.employee_name,
                department=score.department,
                team=score.team,
                role="Innovation Contributor" if score.innovation_score >= 70 else "Employee",
                performance_history=performance,
                learning_activity=self._clip01(0.42 + score.originality_score / 220 + score.adoption_rate / 360),
                project_contributions=max(len(rows), adopted, 1),
                peer_recognition=min(1000, reactions),
                knowledge_sharing=min(1000, mentions + votes // 2),
                mentorship_participation=max(0, mentions // 4),
                ownership_score=self._clip01(0.35 + score.adoption_rate / 180 + progress / 3),
                communication_effectiveness=self._clip01(0.42 + score.collaboration_influence / 190),
                decision_quality=self._clip01(0.38 + score.idea_impact_score / 210 + progress / 5),
                incident_resolution_count=sum(1 for idea in rows if any(term in idea.text.lower() for term in ["incident", "rollback", "failure", "restore", "self-healing"])),
                root_cause_analyses=sum(1 for idea in rows if any(term in idea.text.lower() for term in ["root cause", "postmortem", "dependency", "telemetry", "failure"])),
                strategic_thinking_score=self._clip01(0.36 + score.idea_impact_score / 180 + score.originality_score / 360),
                engagement_score=self._clip01(0.45 + visibility / 2 + progress / 3),
                burnout_risk=self._clip01(0.18 + max(0, score.innovation_score - visibility * 100) / 420),
                retention_risk=self._clip01(0.18 + max(0, score.innovation_score - score.collaboration_influence) / 300),
                manager_visibility=visibility,
                promotion_readiness=self._clip01(0.34 + score.innovation_score / 250 + score.adoption_rate / 320 + progress / 4),
            )
        return profiles

    def _hidden_talent(
        self,
        employees: list[EmployeeInnovationScore],
        insights: list[IdeaMiningInsight],
        profiles: dict[str, EmployeeInnovationProfile],
    ) -> list[HiddenTalentInsight]:
        insight_groups: dict[str, list[IdeaMiningInsight]] = defaultdict(list)
        for insight in insights:
            insight_groups[insight.employee_id].append(insight)
        rows: list[HiddenTalentInsight] = []
        for employee in employees:
            profile = profiles[employee.employee_id]
            growth = self._growth_velocity(profile)
            emerging = self._clip100(employee.originality_score * 0.36 + employee.idea_impact_score * 0.28 + profile.learning_activity * 24 + profile.knowledge_sharing * 1.2)
            recognition = self._clip100(profile.manager_visibility * 100 + profile.peer_recognition * 0.45 + profile.mentorship_participation * 1.6)
            under_recognized_gap = self._clip100(max(0, employee.innovation_score - recognition * 0.72))
            hidden_score = self._clip100(
                employee.innovation_score * 0.3
                + growth * 0.22
                + emerging * 0.2
                + under_recognized_gap * 0.18
                + profile.engagement_score * 100 * 0.1
            )
            top = max(insight_groups[employee.employee_id], key=lambda item: item.impact_score, default=None)
            rows.append(
                HiddenTalentInsight(
                    employee_id=employee.employee_id,
                    employee_name=employee.employee_name,
                    department=employee.department,
                    team=employee.team,
                    hidden_talent_score=round(hidden_score, 2),
                    potential=self._potential(hidden_score),
                    under_recognized_gap=round(under_recognized_gap, 2),
                    growth_trajectory_score=round(growth, 2),
                    emerging_expertise_score=round(emerging, 2),
                    reason=(
                        f"{employee.employee_name} combines {round(employee.innovation_score)} innovation score, "
                        f"{round(growth)} growth trajectory, and {round(under_recognized_gap)} under-recognition gap."
                    ),
                    evidence=[
                        f"performance_growth={round(growth)}",
                        f"learning_activity={round(profile.learning_activity * 100)}",
                        f"knowledge_sharing={profile.knowledge_sharing}",
                        f"top_signal={top.extracted_theme if top else employee.top_idea}",
                    ],
                )
            )
        rows.sort(key=lambda item: item.hidden_talent_score, reverse=True)
        return rows

    def _leadership_predictions(
        self,
        employees: list[EmployeeInnovationScore],
        insights: list[IdeaMiningInsight],
        profiles: dict[str, EmployeeInnovationProfile],
    ) -> list[LeadershipPotentialInsight]:
        rows: list[LeadershipPotentialInsight] = []
        for employee in employees:
            profile = profiles[employee.employee_id]
            team_influence = self._clip100(employee.collaboration_influence * 0.58 + profile.peer_recognition * 0.8 + profile.mentorship_participation * 2.8 + profile.knowledge_sharing * 1.2)
            decision = self._clip100(profile.decision_quality * 100 * 0.72 + employee.idea_impact_score * 0.28)
            communication = self._clip100(profile.communication_effectiveness * 100 * 0.72 + team_influence * 0.18 + profile.engagement_score * 10)
            ownership = self._clip100(profile.ownership_score * 100 * 0.72 + employee.adoption_rate * 0.18 + profile.project_contributions * 1.2)
            leadership = self._clip100(team_influence * 0.24 + decision * 0.22 + communication * 0.2 + ownership * 0.2 + employee.innovation_score * 0.14)
            architect = self._clip100(employee.originality_score * 0.3 + employee.idea_impact_score * 0.34 + profile.strategic_thinking_score * 100 * 0.24 + profile.root_cause_analyses * 2.2)
            manager = self._clip100(leadership * 0.72 + communication * 0.18 + profile.mentorship_participation * 2.4)
            executive = self._clip100(leadership * 0.48 + profile.strategic_thinking_score * 100 * 0.34 + employee.idea_impact_score * 0.18)
            track = "Future Architect" if architect >= manager and architect >= executive else "Future Executive" if executive >= manager else "Future Team Lead"
            rows.append(
                LeadershipPotentialInsight(
                    employee_id=employee.employee_id,
                    employee_name=employee.employee_name,
                    department=employee.department,
                    team=employee.team,
                    leadership_potential=round(leadership, 2),
                    team_influence=round(team_influence, 2),
                    decision_making_ability=round(decision, 2),
                    communication_effectiveness=round(communication, 2),
                    ownership_mindset=round(ownership, 2),
                    future_manager_probability=round(manager, 2),
                    future_architect_probability=round(architect, 2),
                    future_executive_probability=round(executive, 2),
                    confidence=round(float(np.clip(0.68 + len(insights) / 120 + employee.contribution_frequency / 20, 0.68, 0.94)), 3),
                    recommended_track=track,
                    reason=f"{track} signal from ownership {round(ownership)}, communication {round(communication)}, and decision quality {round(decision)}.",
                )
            )
        rows.sort(key=lambda item: item.leadership_potential, reverse=True)
        return rows

    def _problem_solving(
        self,
        employees: list[EmployeeInnovationScore],
        insights: list[IdeaMiningInsight],
        profiles: dict[str, EmployeeInnovationProfile],
    ) -> list[ProblemSolvingInsight]:
        insight_groups: dict[str, list[IdeaMiningInsight]] = defaultdict(list)
        for insight in insights:
            insight_groups[insight.employee_id].append(insight)
        rows: list[ProblemSolvingInsight] = []
        for employee in employees:
            profile = profiles[employee.employee_id]
            text_signal = sum(
                1
                for insight in insight_groups[employee.employee_id]
                for keyword in ["incident", "rollback", "latency", "failure", "dependency", "optimizer", "self healing", "root"]
                if keyword in f"{insight.extracted_theme} {' '.join(insight.extracted_keywords)}".lower()
            )
            incident = self._clip100(profile.incident_resolution_count * 16 + text_signal * 6 + employee.adoption_rate * 0.28)
            root_cause = self._clip100(profile.root_cause_analyses * 18 + profile.decision_quality * 100 * 0.42 + employee.idea_impact_score * 0.22)
            complex_resolution = self._clip100(employee.idea_impact_score * 0.42 + employee.originality_score * 0.2 + incident * 0.22 + profile.project_contributions * 2.2)
            strategic = self._clip100(profile.strategic_thinking_score * 100 * 0.68 + employee.originality_score * 0.18 + employee.idea_impact_score * 0.14)
            score = self._clip100(complex_resolution * 0.3 + incident * 0.24 + root_cause * 0.24 + strategic * 0.22)
            rows.append(
                ProblemSolvingInsight(
                    employee_id=employee.employee_id,
                    employee_name=employee.employee_name,
                    department=employee.department,
                    team=employee.team,
                    problem_solving_score=round(score, 2),
                    complex_issue_resolution=round(complex_resolution, 2),
                    incident_handling=round(incident, 2),
                    root_cause_analysis=round(root_cause, 2),
                    strategic_thinking=round(strategic, 2),
                    strength=self._problem_strength(incident, root_cause, strategic),
                    evidence=[
                        f"incident_resolution_count={profile.incident_resolution_count}",
                        f"root_cause_analyses={profile.root_cause_analyses}",
                        f"idea_impact={round(employee.idea_impact_score)}",
                    ],
                )
            )
        rows.sort(key=lambda item: item.problem_solving_score, reverse=True)
        return rows

    def _growth_forecasts(
        self,
        employees: list[EmployeeInnovationScore],
        profiles: dict[str, EmployeeInnovationProfile],
        leaders: list[LeadershipPotentialInsight],
    ) -> list[GrowthTrajectoryForecast]:
        leader_lookup = {leader.employee_id: leader for leader in leaders}
        rows: list[GrowthTrajectoryForecast] = []
        for employee in employees:
            profile = profiles[employee.employee_id]
            leader = leader_lookup[employee.employee_id]
            growth = self._growth_velocity(profile)
            skill_3m = self._clip100(growth * 0.55 + profile.learning_activity * 100 * 0.28 + employee.originality_score * 0.17)
            career_6m = self._clip100(skill_3m * 0.36 + employee.innovation_score * 0.28 + profile.promotion_readiness * 100 * 0.22 + leader.leadership_potential * 0.14)
            leadership_1y = self._clip100(leader.leadership_potential * 0.52 + career_6m * 0.24 + profile.mentorship_participation * 2.2 + profile.ownership_score * 12)
            innovation_3y = self._clip100(employee.innovation_score * 0.45 + employee.originality_score * 0.24 + profile.strategic_thinking_score * 100 * 0.2 + profile.knowledge_sharing * 1.2)
            expected_role = leader.recommended_track.replace("Future ", "Senior ")
            rows.append(
                GrowthTrajectoryForecast(
                    employee_id=employee.employee_id,
                    employee_name=employee.employee_name,
                    current_role=profile.role,
                    expected_future_role=expected_role,
                    growth_forecast=self._potential(max(skill_3m, career_6m, leadership_1y, innovation_3y)),
                    skill_growth_3_months=round(skill_3m, 2),
                    career_growth_6_months=round(career_6m, 2),
                    leadership_growth_1_year=round(leadership_1y, 2),
                    innovation_growth_3_years=round(innovation_3y, 2),
                    confidence=round(float(np.clip(0.7 + len(profile.performance_history) / 40 + employee.contribution_frequency / 24, 0.7, 0.95)), 3),
                    drivers=[
                        f"learning velocity {round(profile.learning_activity * 100)}",
                        f"innovation signal {round(employee.innovation_score)}",
                        f"leadership signal {round(leader.leadership_potential)}",
                    ],
                )
            )
        rows.sort(key=lambda item: max(item.skill_growth_3_months, item.career_growth_6_months, item.leadership_growth_1_year, item.innovation_growth_3_years), reverse=True)
        return rows

    def _talent_risks(
        self,
        employees: list[EmployeeInnovationScore],
        profiles: dict[str, EmployeeInnovationProfile],
        hidden_talent: list[HiddenTalentInsight],
    ) -> list[TalentRiskInsight]:
        hidden_lookup = {item.employee_id: item for item in hidden_talent}
        rows: list[TalentRiskInsight] = []
        for employee in employees:
            profile = profiles[employee.employee_id]
            hidden = hidden_lookup[employee.employee_id]
            flight = self._clip100(profile.retention_risk * 100 * 0.5 + hidden.hidden_talent_score * 0.22 + hidden.under_recognized_gap * 0.28)
            burnout = self._clip100(profile.burnout_risk * 100 * 0.72 + max(0, employee.innovation_score - 65) * 0.28)
            retention = self._clip100(flight * 0.56 + burnout * 0.18 + hidden.under_recognized_gap * 0.26)
            level = self._risk_level(max(flight, retention, burnout))
            rows.append(
                TalentRiskInsight(
                    employee_id=employee.employee_id,
                    employee_name=employee.employee_name,
                    department=employee.department,
                    team=employee.team,
                    critical_talent_risk=level,
                    flight_risk=round(flight, 2),
                    retention_risk=round(retention, 2),
                    burnout_risk=round(burnout, 2),
                    risk_reason=f"{employee.employee_name} has {round(hidden.under_recognized_gap)} under-recognition gap and {round(burnout)} burnout pressure.",
                    retention_action=f"Give {employee.employee_name} visible sponsorship, protected innovation time, and a growth conversation within 14 days.",
                )
            )
        rows.sort(key=lambda item: max(item.flight_risk, item.retention_risk, item.burnout_risk), reverse=True)
        return rows

    def _promotion_recommendations(
        self,
        employees: list[EmployeeInnovationScore],
        leaders: list[LeadershipPotentialInsight],
        hidden_talent: list[HiddenTalentInsight],
        risks: list[TalentRiskInsight],
    ) -> list[PromotionRecommendation]:
        leader_lookup = {item.employee_id: item for item in leaders}
        hidden_lookup = {item.employee_id: item for item in hidden_talent}
        risk_lookup = {item.employee_id: item for item in risks}
        rows: list[PromotionRecommendation] = []
        for employee in employees:
            leader = leader_lookup[employee.employee_id]
            hidden = hidden_lookup[employee.employee_id]
            risk = risk_lookup[employee.employee_id]
            readiness = self._clip100(employee.innovation_score * 0.28 + leader.leadership_potential * 0.36 + hidden.growth_trajectory_score * 0.2 + hidden.emerging_expertise_score * 0.16)
            if readiness < 55 and hidden.hidden_talent_score < 62:
                continue
            program = "Architect Acceleration Program" if leader.future_architect_probability >= leader.future_manager_probability else "Team Lead Candidate Program"
            if leader.future_executive_probability >= 78:
                program = "Strategic Leadership Bench"
            rows.append(
                PromotionRecommendation(
                    employee_id=employee.employee_id,
                    employee_name=employee.employee_name,
                    target_program=program,
                    priority=self._priority(max(readiness, risk.flight_risk)),
                    readiness_score=round(readiness, 2),
                    action=f"Place {employee.employee_name} into {program} and assign a visible executive-sponsored initiative.",
                    reason=f"Readiness {round(readiness)} with leadership potential {round(leader.leadership_potential)} and hidden talent {round(hidden.hidden_talent_score)}.",
                    expected_impact=round(self._clip100(readiness * 0.52 + employee.idea_impact_score * 0.3 + risk.flight_risk * 0.18), 2),
                    confidence=round(float(np.clip(0.74 + employee.contribution_frequency / 20 + readiness / 600, 0.74, 0.95)), 3),
                )
            )
        rows.sort(key=lambda item: item.readiness_score, reverse=True)
        return rows[:8]

    def _team_heatmap(
        self,
        ideas: list[InnovationIdeaSignal],
        insights: list[IdeaMiningInsight],
        employee_scores: list[EmployeeInnovationScore],
    ) -> list[TeamInnovationHeatmapPoint]:
        grouped: dict[tuple[str, str], list[IdeaMiningInsight]] = defaultdict(list)
        idea_lookup = {idea.idea_id: idea for idea in ideas}
        employees_by_team: dict[tuple[str, str], list[EmployeeInnovationScore]] = defaultdict(list)
        for insight in insights:
            grouped[(insight.department, insight.team)].append(insight)
        for score in employee_scores:
            employees_by_team[(score.department, score.team)].append(score)
        heatmap: list[TeamInnovationHeatmapPoint] = []
        for (department, team), rows in grouped.items():
            sources = [idea_lookup[row.idea_id] for row in rows]
            innovation = mean([row.impact_score * 0.42 + row.originality_score * 0.33 + row.adoption_probability * 0.25 for row in rows])
            creativity = mean([row.originality_score for row in rows])
            adoption = mean([self._stage_score(idea.adoption_stage) for idea in sources])
            influence = mean([self._clip100(idea.cross_team_votes * 4 + idea.collaboration_mentions * 3 + idea.reactions_count) for idea in sources])
            heatmap.append(
                TeamInnovationHeatmapPoint(
                    department=department,
                    team=team,
                    innovation_score=round(self._clip100(innovation), 2),
                    creativity_density=round(self._clip100(creativity + min(16, len(rows) * 2)), 2),
                    adoption_velocity=round(adoption, 2),
                    cross_functional_influence=round(influence, 2),
                    idea_count=len(rows),
                    priority=self._priority(max(innovation, creativity, adoption, influence)),
                )
            )
        return heatmap

    def _impact_forecasts(self, ideas: list[InnovationIdeaSignal], insights: list[IdeaMiningInsight], horizon_days: int) -> list[IdeaImpactForecast]:
        idea_lookup = {idea.idea_id: idea for idea in ideas}
        forecasts: list[IdeaImpactForecast] = []
        for insight in insights:
            idea = idea_lookup[insight.idea_id]
            base = self._clip100(insight.impact_score * 0.52 + insight.adoption_probability * 0.28 + insight.feasibility_score * 0.2)
            slope = np.clip(insight.originality_score * 0.012 + idea.implementation_progress * 2.1 + self._stage_score(idea.adoption_stage) * 0.01, 0.4, 5.6)
            series = [round(float(np.clip(base + slope * step * horizon_days / 90, 0, 100)), 2) for step in range(1, 7)]
            productivity_lift = self._clip100(series[-1] * 0.28 + idea.estimated_hours_saved / 75)
            cost = max(idea.estimated_cost_saving, idea.estimated_hours_saved * 95) * (series[-1] / 100)
            drivers = []
            if insight.originality_score >= 75:
                drivers.append("high originality")
            if insight.adoption_probability >= 70:
                drivers.append("strong adoption path")
            if idea.cross_team_votes >= 8:
                drivers.append("cross-team sponsorship")
            if idea.estimated_hours_saved >= 250 or idea.estimated_cost_saving >= 100000:
                drivers.append("measurable operating leverage")
            forecasts.append(
                IdeaImpactForecast(
                    idea_id=idea.idea_id,
                    title=insight.extracted_theme,
                    department=idea.department,
                    team=idea.team,
                    predicted_business_impact=round(series[-1], 2),
                    productivity_lift_percent=round(productivity_lift, 2),
                    cost_saving_estimate=round(float(cost), 2),
                    adoption_probability=insight.adoption_probability,
                    confidence=insight.confidence,
                    drivers=drivers or ["early-stage innovation signal"],
                    forecast=series,
                )
            )
        return forecasts

    def _trend_points(self, ideas: list[InnovationIdeaSignal], insights: list[IdeaMiningInsight]) -> list[InnovationTrendPoint]:
        ordered = sorted(insights, key=lambda item: item.impact_score)
        points: list[InnovationTrendPoint] = []
        for index in range(6):
            window = ordered[: max(1, min(len(ordered), index + 1))]
            multiplier = 0.88 + index * 0.035
            points.append(
                InnovationTrendPoint(
                    label=f"W{index + 1}",
                    idea_volume=max(1, round(len(ideas) * (0.62 + index * 0.08))),
                    average_impact=round(self._clip100(mean([item.impact_score for item in window]) * multiplier), 2),
                    average_originality=round(self._clip100(mean([item.originality_score for item in window]) * multiplier), 2),
                    adoption_probability=round(self._clip100(mean([item.adoption_probability for item in window]) * multiplier), 2),
                )
            )
        return points

    def _recommendations(
        self,
        ideas: list[InnovationIdeaSignal],
        insights: list[IdeaMiningInsight],
        employees: list[EmployeeInnovationScore],
        teams: list[TeamInnovationHeatmapPoint],
        hidden_talent: list[HiddenTalentInsight],
        leadership: list[LeadershipPotentialInsight],
    ) -> list[InnovationRecommendation]:
        recommendations: list[InnovationRecommendation] = []
        top_idea = max(insights, key=lambda item: item.impact_score, default=None)
        if top_idea:
            recommendations.append(
                InnovationRecommendation(
                    title="Sponsor highest-impact idea",
                    category="idea_sponsorship",
                    priority=self._priority(top_idea.impact_score),
                    impact_score=top_idea.impact_score,
                    action=f"Assign an executive sponsor to {top_idea.employee_name}'s {top_idea.extracted_theme.lower()} and move it into a measured pilot.",
                    rationale=top_idea.recommendation,
                    confidence=top_idea.confidence,
                )
            )
        prototype = max((item for item in insights if item.feasibility_score >= 65), key=lambda item: item.originality_score, default=None)
        if prototype:
            recommendations.append(
                InnovationRecommendation(
                    title="Convert creative proposal into prototype",
                    category="prototype",
                    priority=self._priority(prototype.originality_score),
                    impact_score=prototype.originality_score,
                    action=f"Fund a two-week prototype for {prototype.extracted_theme.lower()} with success metrics for adoption and business impact.",
                    rationale=f"Originality {round(prototype.originality_score)} and feasibility {round(prototype.feasibility_score)} make this prototype-ready.",
                    confidence=prototype.confidence,
                )
            )
        top_employee = employees[0] if employees else None
        if top_employee:
            recommendations.append(
                InnovationRecommendation(
                    title="Recognize innovation leader",
                    category="recognition",
                    priority=self._priority(top_employee.innovation_score),
                    impact_score=top_employee.innovation_score,
                    action=f"Recognize {top_employee.employee_name} as an innovation contributor and pair them with delivery sponsors.",
                    rationale=f"Innovation score {round(top_employee.innovation_score)} with top idea: {top_employee.top_idea}.",
                    confidence=0.84,
                )
            )
        top_hidden = hidden_talent[0] if hidden_talent else None
        if top_hidden:
            recommendations.append(
                InnovationRecommendation(
                    title="Activate hidden talent",
                    category="recognition",
                    priority=self._priority(top_hidden.hidden_talent_score),
                    impact_score=top_hidden.hidden_talent_score,
                    action=f"Give {top_hidden.employee_name} a visible innovation brief, mentoring sponsor, and growth-track review.",
                    rationale=top_hidden.reason,
                    confidence=0.86,
                )
            )
        top_leader = leadership[0] if leadership else None
        if top_leader and top_leader.leadership_potential >= 62:
            recommendations.append(
                InnovationRecommendation(
                    title="Build future leader pipeline",
                    category="collaboration",
                    priority=self._priority(top_leader.leadership_potential),
                    impact_score=top_leader.leadership_potential,
                    action=f"Enroll {top_leader.employee_name} in {top_leader.recommended_track} development with a cross-functional assignment.",
                    rationale=top_leader.reason,
                    confidence=top_leader.confidence,
                )
            )
        weak_team = min(teams, key=lambda item: item.idea_count, default=None)
        if weak_team and weak_team.idea_count <= 1:
            recommendations.append(
                InnovationRecommendation(
                    title="Increase cross-functional idea flow",
                    category="collaboration",
                    priority="medium",
                    impact_score=48,
                    action=f"Run a cross-functional brainstorming sprint for {weak_team.department} / {weak_team.team} and require measurable impact hypotheses.",
                    rationale="Team innovation density is below portfolio average.",
                    confidence=0.77,
                )
            )
        return recommendations[:6]

    def _alerts(
        self,
        insights: list[IdeaMiningInsight],
        employees: list[EmployeeInnovationScore],
        teams: list[TeamInnovationHeatmapPoint],
    ) -> list[InnovationAlert]:
        alerts: list[InnovationAlert] = []
        for insight in insights[:5]:
            signal = max(insight.impact_score, insight.originality_score, insight.adoption_probability)
            if signal >= 72:
                alerts.append(
                    InnovationAlert(
                        title=f"{insight.employee_name} high-impact idea signal",
                        priority=self._priority(signal),
                        probability=round(signal, 2),
                        impact=f"{insight.extracted_theme} scored {round(insight.impact_score)} impact and {round(insight.originality_score)} originality.",
                        recommendation=insight.recommendation,
                    )
                )
        if employees and employees[0].innovation_score >= 70:
            leader = employees[0]
            alerts.append(
                InnovationAlert(
                    title="Innovation leaderboard shift",
                    priority=self._priority(leader.innovation_score),
                    probability=leader.innovation_score,
                    impact=f"{leader.employee_name} is the current top innovation contributor.",
                    recommendation="Move top contributor ideas into sponsor review and capture implementation metrics.",
                )
            )
        for team in teams[:2]:
            if team.innovation_score >= 72:
                alerts.append(
                    InnovationAlert(
                        title=f"{team.team} innovation heatmap surge",
                        priority=self._priority(team.innovation_score),
                        probability=team.innovation_score,
                        impact=f"{team.department} / {team.team} generated {team.idea_count} idea signal(s) with {round(team.cross_functional_influence)} cross-functional influence.",
                        recommendation="Protect maker time and accelerate prototype funding.",
                    )
                )
        return alerts[:8]

    def _executive_insights(
        self,
        insights: list[IdeaMiningInsight],
        employees: list[EmployeeInnovationScore],
        teams: list[TeamInnovationHeatmapPoint],
        hidden_talent: list[HiddenTalentInsight],
        leadership: list[LeadershipPotentialInsight],
    ) -> list[str]:
        output: list[str] = []
        if employees:
            top = employees[0]
            output.append(f"{top.employee_name} leads the innovation leaderboard with {round(top.innovation_score)} innovation score and {top.contribution_frequency} analyzed idea(s).")
        if insights:
            idea = max(insights, key=lambda item: item.impact_score)
            output.append(f"Highest-impact idea is {idea.extracted_theme.lower()} at {round(idea.impact_score)} impact and {round(idea.adoption_probability)} adoption probability.")
        if teams:
            team = teams[0]
            output.append(f"{team.department} / {team.team} is the strongest innovation heatmap zone at {round(team.innovation_score)}.")
        if hidden_talent:
            hidden = hidden_talent[0]
            output.append(f"Top hidden talent signal is {hidden.employee_name} with {round(hidden.hidden_talent_score)} hidden talent score and {round(hidden.under_recognized_gap)} under-recognition gap.")
        if leadership:
            leader = leadership[0]
            output.append(f"Future leader prediction ranks {leader.employee_name} highest at {round(leader.leadership_potential)} leadership potential for {leader.recommended_track}.")
        output.append("Innovation detector combines TF-IDF idea mining, local ML impact/originality models, NLP sentiment, growth forecasting, leadership scoring, talent-risk analytics, and digital twin updates.")
        return output

    def _summary(
        self,
        insights: list[IdeaMiningInsight],
        employees: list[EmployeeInnovationScore],
        forecasts: list[IdeaImpactForecast],
        hidden_talent: list[HiddenTalentInsight],
        leadership: list[LeadershipPotentialInsight],
        promotions: list[PromotionRecommendation],
        risks: list[TalentRiskInsight],
        growth: list[GrowthTrajectoryForecast],
    ) -> InnovationSummary:
        return InnovationSummary(
            ideas_analyzed=len(insights),
            employees_ranked=len(employees),
            high_impact_ideas=sum(1 for item in insights if item.impact_score >= 70),
            adopted_or_piloting_ideas=sum(1 for item in insights if item.adoption_probability >= 70),
            average_innovation_score=round(mean([employee.innovation_score for employee in employees] or [0]), 2),
            average_originality_score=round(mean([item.originality_score for item in insights] or [0]), 2),
            forecasted_business_impact=round(mean([item.predicted_business_impact for item in forecasts] or [0]), 2),
            hidden_talent_count=sum(1 for item in hidden_talent if item.hidden_talent_score >= 60),
            future_leaders_count=sum(1 for item in leadership if item.leadership_potential >= 62),
            promotion_candidates=len(promotions),
            critical_talent_risks=sum(1 for item in risks if item.critical_talent_risk in {"high", "critical"}),
            average_leadership_potential=round(mean([item.leadership_potential for item in leadership] or [0]), 2),
            average_growth_velocity=round(mean([max(item.skill_growth_3_months, item.career_growth_6_months, item.leadership_growth_1_year, item.innovation_growth_3_years) for item in growth] or [0]), 2),
        )

    def _digital_twin_updates(
        self,
        hidden_talent: list[HiddenTalentInsight],
        leaders: list[LeadershipPotentialInsight],
        risks: list[TalentRiskInsight],
    ) -> list[str]:
        updates: list[str] = []
        for row in hidden_talent[:3]:
            updates.append(f"employee_digital_twin.{row.employee_id}.hidden_talent_score={round(row.hidden_talent_score)}")
        for row in leaders[:3]:
            updates.append(f"employee_digital_twin.{row.employee_id}.leadership_potential={round(row.leadership_potential)}")
        for row in risks[:3]:
            updates.append(f"company_digital_twin.talent_risk.{row.employee_id}={row.critical_talent_risk}")
        return updates

    @staticmethod
    def _marketplace_updates(
        hidden_talent: list[HiddenTalentInsight],
        promotions: list[PromotionRecommendation],
    ) -> list[str]:
        updates: list[str] = []
        for row in hidden_talent[:3]:
            updates.append(f"talent_marketplace.expert_discovery.{row.employee_id}=hidden_talent")
        for row in promotions[:3]:
            updates.append(f"talent_marketplace.growth_path.{row.employee_id}={row.target_program}")
        return updates

    @staticmethod
    def source_systems() -> list[str]:
        return [
            "innovation_analytics_engine",
            "leadership_potential_engine",
            "creativity_intelligence_engine",
            "problem_solving_intelligence_engine",
            "talent_discovery_engine",
            "employee_growth_engine",
            "future_leader_prediction_engine",
            "talent_risk_engine",
            "promotion_recommendation_engine",
            "innovation_dashboard",
            "innovation_ai_assistant",
            "employee_digital_twin",
            "company_digital_twin",
            "knowledge_brain",
            "talent_marketplace",
            "hiring_intelligence",
            "executive_dashboard",
            "pytorch_text_emotion_net",
            "tfidf_idea_mining",
            "random_forest_originality_model",
            "gradient_boosting_impact_forecaster",
            "innovation_history_jsonl",
        ]

    @staticmethod
    def _idea_recommendation(impact: float, originality: float, feasibility: float, adoption: float) -> str:
        if impact >= 78 and feasibility >= 65:
            return "Move into sponsored prototype with implementation owner, metric baseline, and adoption milestone."
        if originality >= 78 and feasibility < 58:
            return "Run a feasibility spike before committing delivery capacity."
        if adoption >= 72:
            return "Document implementation pattern and expand to adjacent teams."
        if impact < 40:
            return "Clarify measurable business outcome before prioritizing this idea."
        return "Keep in innovation backlog and collect sponsor feedback."

    @staticmethod
    def _keywords(text: str) -> list[str]:
        tokens = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", text.lower())
        stop = {"the", "and", "with", "that", "this", "into", "from", "when", "will", "should", "could", "each", "before", "after", "during"}
        ordered: list[str] = []
        for token in tokens:
            if token not in stop and token not in ordered:
                ordered.append(token)
        return ordered[:12]

    @staticmethod
    def _theme(category: object, keywords: list[str]) -> str:
        label = str(category).replace("_", " ").title()
        terms = ", ".join(keywords[:3]) if keywords else "idea"
        return f"{label} innovation around {terms}"

    @staticmethod
    def _stage_score(stage: str) -> float:
        return {"submitted": 30, "reviewing": 52, "piloting": 76, "adopted": 92, "rejected": 8}.get(stage, 30)

    @staticmethod
    def _growth_velocity(profile: EmployeeInnovationProfile) -> float:
        history = profile.performance_history or [0.5, 0.55, 0.6]
        normalized = [float(np.clip(value, 0, 1)) for value in history]
        delta = (normalized[-1] - normalized[0]) * 100 if len(normalized) > 1 else 0
        consistency = mean(normalized) * 100
        return float(np.clip(consistency * 0.55 + max(-20, delta) * 0.45 + profile.learning_activity * 18, 0, 100))

    @staticmethod
    def _potential(score: float) -> str:
        if score >= 86:
            return "exceptional"
        if score >= 72:
            return "very_high"
        if score >= 58:
            return "high"
        return "moderate"

    @staticmethod
    def _risk_level(score: float) -> str:
        if score >= 82:
            return "critical"
        if score >= 66:
            return "high"
        if score >= 42:
            return "medium"
        return "low"

    @staticmethod
    def _problem_strength(incident: float, root_cause: float, strategic: float) -> str:
        if incident >= root_cause and incident >= strategic:
            return "Infrastructure Incident Resolution"
        if root_cause >= strategic:
            return "Root Cause Analysis"
        return "Strategic Problem Framing"

    @staticmethod
    def _priority(score: float) -> InnovationPriority:
        if score >= 82:
            return "critical"
        if score >= 66:
            return "high"
        if score >= 42:
            return "medium"
        return "low"

    @staticmethod
    def _clip100(value: float) -> float:
        return float(np.clip(value, 0, 100))

    @staticmethod
    def _clip01(value: float) -> float:
        return float(np.clip(value, 0, 1))

    def _scenario_variant(self, base: InnovationRequest, impact_delta: float, adoption_delta: float, extra_reactions: int) -> InnovationRequest:
        source = base if base.ideas else self.default_request()
        ideas = [
            idea.model_copy(
                update={
                    "reactions_count": min(5000, idea.reactions_count + extra_reactions),
                    "cross_team_votes": min(5000, idea.cross_team_votes + max(1, extra_reactions // 3)),
                    "collaboration_mentions": min(5000, idea.collaboration_mentions + max(1, extra_reactions // 4)),
                    "implementation_progress": min(1, idea.implementation_progress + adoption_delta),
                    "estimated_hours_saved": min(100000, idea.estimated_hours_saved * (1 + impact_delta)),
                    "estimated_cost_saving": min(100000000, idea.estimated_cost_saving * (1 + impact_delta)),
                    "estimated_revenue_impact": min(100000000, idea.estimated_revenue_impact * (1 + impact_delta)),
                    "strategic_alignment": min(1, idea.strategic_alignment + impact_delta / 2),
                }
            )
            for idea in source.ideas
        ]
        return source.model_copy(update={"ideas": ideas, "realtime": True})

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as file:
                file.write(json.dumps(payload) + "\n")


innovation_scoring_service = InnovationScoringService()
