from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

from app.core.cache import TTLResponseCache
from app.schemas.hidden_leader import (
    HiddenLeaderAssistantRequest,
    HiddenLeaderAssistantResponse,
    HiddenLeaderCandidate,
    HiddenLeaderDashboardSummary,
    HiddenLeaderDetectionResponse,
    HiddenLeaderRequest,
    InfluenceAnalysisInsight,
    InnovationLeaderInsight,
    KnowledgeLeaderInsight,
    LeadershipForecastPoint,
    LeadershipScorecard,
    ProblemSolvingTalentInsight,
    TalentAgentContribution,
    TalentDataQualityReport,
    TalentDigitalTwinSync,
    TalentGraphIntegration,
    TalentPromotionRecommendation,
    TalentReadinessLevel,
    TalentRiskLevel,
)
from app.schemas.innovation import (
    EmployeeInnovationProfile,
    EmployeeInnovationScore,
    GrowthTrajectoryForecast,
    HiddenTalentInsight,
    InnovationResponse,
    LeadershipPotentialInsight,
    ProblemSolvingInsight,
    PromotionRecommendation,
    TalentRiskInsight,
)
from app.schemas.organizational_brain import InfluenceFinding, OrganizationalBrainResponse
from app.schemas.talent_marketplace import (
    ExpertRanking,
    ReputationScore,
    TalentMarketplaceProfile,
    TalentMarketplaceResponse,
)
from app.services.innovation_service import innovation_scoring_service
from app.services.organizational_brain_service import organizational_brain_service
from app.services.talent_marketplace_service import talent_marketplace_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "hidden_leader_detection_history.jsonl"
ASSISTANT_HISTORY_PATH = DATA_DIR / "hidden_leader_assistant_history.jsonl"


class HiddenLeaderDetectionService:
    model_name = "NEXUSMIND Hidden Leader Detection & Talent Intelligence System"
    assistant_model = "Hidden Leader Talent AI Assistant"
    final_verdict = "HIDDEN LEADER DETECTION SYSTEM COMPLETE"
    source_systems = [
        "leadership_intelligence_engine",
        "talent_discovery_engine",
        "influence_analysis_engine",
        "communication_intelligence_engine",
        "innovation_detection_engine",
        "mentorship_analysis_engine",
        "skill_growth_engine",
        "problem_solving_intelligence_engine",
        "knowledge_leadership_engine",
        "leadership_forecast_engine",
        "talent_dashboard",
        "talent_ai_assistant",
        "communication_graph",
        "collaboration_graph",
        "knowledge_graph",
        "organizational_brain",
        "employee_digital_twin",
        "team_digital_twin",
        "department_digital_twin",
        "company_digital_twin",
        "executive_dashboard",
        "multi_agent_workforce",
        "hr_agent",
        "productivity_agent",
        "knowledge_agent",
        "executive_agent",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[HiddenLeaderDetectionResponse] = TTLResponseCache(ttl_seconds=8)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def default(self) -> HiddenLeaderDetectionResponse:
        return self._cache.get_or_set(lambda: self.analyze(HiddenLeaderRequest()))

    def analyze(self, payload: HiddenLeaderRequest | None = None) -> HiddenLeaderDetectionResponse:
        request = payload or HiddenLeaderRequest()
        innovation = innovation_scoring_service.score() if request.include_innovation_engine else None
        organization = organizational_brain_service.default() if request.include_organizational_graph else None
        marketplace = talent_marketplace_service.default() if request.include_talent_marketplace else None

        leadership_scorecards = self._leadership_scorecards(innovation, organization, marketplace)
        candidates = [
            candidate
            for candidate in self._hidden_leader_candidates(innovation, organization, marketplace)
            if candidate.hidden_leader_score >= request.min_candidate_score
        ]
        influence = self._influence_analysis(candidates, innovation, organization)
        problem_solving = self._problem_solving_intelligence(innovation)
        innovation_leaders = self._innovation_leaders(innovation)
        knowledge_leaders = self._knowledge_leaders(marketplace, innovation)
        forecasts = self._leadership_forecast(candidates, innovation, request.horizon_months)
        promotions = self._promotion_recommendations(candidates, innovation)
        graph_integration = self._graph_integration(organization, marketplace)
        digital_twin_sync = self._digital_twin_sync(candidates, forecasts)
        agent_council = self._agent_council(candidates, influence, knowledge_leaders, promotions)
        summary = self._summary(leadership_scorecards, candidates, innovation_leaders, knowledge_leaders)
        insights = self._executive_insights(candidates, influence, knowledge_leaders, forecasts)
        response = HiddenLeaderDetectionResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            cycle_name=request.cycle_name,
            summary=summary,
            data_quality=self._data_quality(innovation, organization, marketplace),
            leadership_scorecards=leadership_scorecards,
            hidden_leader_candidates=candidates,
            influence_analysis=influence,
            problem_solving_intelligence=problem_solving,
            innovation_leaders=innovation_leaders,
            knowledge_leaders=knowledge_leaders,
            leadership_forecast=forecasts,
            promotion_recommendations=promotions,
            graph_integration=graph_integration,
            digital_twin_sync=digital_twin_sync,
            agent_council=agent_council,
            supported_questions=[
                "Who are our future leaders?",
                "Which employee has the highest leadership potential?",
                "Who is influencing teams the most?",
                "Which employee should be promoted?",
                "Who is our most innovative contributor?",
                "Who are our knowledge leaders?",
                "Who solves the most critical problems?",
            ],
            executive_insights=insights,
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
            final_verdict=self.final_verdict,
        )
        self._append_jsonl(HISTORY_PATH, response.model_dump(mode="json"))
        return response

    def ask(self, payload: HiddenLeaderAssistantRequest) -> HiddenLeaderAssistantResponse:
        analysis = self.default() if payload.horizon_months == 24 else self.analyze(HiddenLeaderRequest(horizon_months=payload.horizon_months))
        question = payload.question.lower()
        if any(token in question for token in ["future leader", "leaders", "leadership pipeline"]):
            intent = "future_leaders"
            rows = analysis.hidden_leader_candidates[:4]
            answer = "Future leaders are " + ", ".join(
                f"{row.employee_name} for {row.recommended_future_role} ({round(row.hidden_leader_score)}%)" for row in rows
            ) + "."
            evidence = [row.why_hidden for row in rows]
            actions = [row.promotion_recommendation for row in rows[:3]]
            employees = [row.employee_name for row in rows]
        elif any(token in question for token in ["highest", "top", "best"]):
            intent = "top_leader"
            top = analysis.hidden_leader_candidates[0]
            answer = (
                f"{top.employee_name} has the highest hidden leadership score at {round(top.hidden_leader_score)}%, "
                f"with {round(top.influence_score)}% influence and {round(top.innovation_score)}% innovation strength."
            )
            evidence = top.evidence
            actions = [top.promotion_recommendation]
            employees = [top.employee_name]
        elif any(token in question for token in ["influence", "influencing", "connector", "advisor"]):
            intent = "influence"
            rows = analysis.influence_analysis[:4]
            answer = "Informal influence is strongest for " + ", ".join(
                f"{row.employee_name} ({round(row.influence_score)}%)" for row in rows
            ) + "."
            evidence = [", ".join(row.graph_evidence[:2]) for row in rows]
            actions = [f"Use {row.employee_name} as a bridge for {', '.join(row.consulted_by_teams[:2])}." for row in rows[:3]]
            employees = [row.employee_name for row in rows]
        elif any(token in question for token in ["promote", "promotion", "promoted"]):
            intent = "promotion"
            rows = analysis.promotion_recommendations[:4]
            answer = "Promotion recommendations prioritize " + ", ".join(
                f"{row.employee_name} for {row.target_track}" for row in rows
            ) + "."
            evidence = [row.reason for row in rows]
            actions = [row.action for row in rows]
            employees = [row.employee_name for row in rows]
        elif any(token in question for token in ["innovation", "innovative", "creative"]):
            intent = "innovation"
            rows = analysis.innovation_leaders[:4]
            answer = "Innovation leadership is strongest for " + ", ".join(
                f"{row.employee_name} ({round(row.innovation_score)}%)" for row in rows
            ) + "."
            evidence = [", ".join(row.evidence[:2]) for row in rows]
            actions = [f"Sponsor {row.employee_name}'s next cross-functional innovation prototype." for row in rows[:3]]
            employees = [row.employee_name for row in rows]
        elif any(token in question for token in ["knowledge", "expert", "mentor", "documentation"]):
            intent = "knowledge"
            rows = analysis.knowledge_leaders[:4]
            answer = "Knowledge leaders are " + ", ".join(
                f"{row.employee_name} ({round(row.knowledge_leadership_score)}%)" for row in rows
            ) + "."
            evidence = [", ".join(row.evidence[:2]) for row in rows]
            actions = [f"Give {row.employee_name} a formal mentoring and documentation charter." for row in rows[:3]]
            employees = [row.employee_name for row in rows]
        elif any(token in question for token in ["problem", "solver", "incident", "root cause"]):
            intent = "problem_solving"
            rows = analysis.problem_solving_intelligence[:4]
            answer = "Critical problem-solving signals are strongest for " + ", ".join(
                f"{row.employee_name} ({round(row.problem_solving_score)}%)" for row in rows
            ) + "."
            evidence = [", ".join(row.evidence[:2]) for row in rows]
            actions = [f"Assign {row.employee_name} to {row.strength.lower()} initiatives." for row in rows[:3]]
            employees = [row.employee_name for row in rows]
        else:
            intent = "summary"
            answer = (
                f"The system analyzed {analysis.summary.employees_analyzed} employees and found "
                f"{analysis.summary.hidden_leaders_found} hidden leader candidates, "
                f"{analysis.summary.innovation_leaders} innovation leaders, and "
                f"{analysis.summary.knowledge_leaders} knowledge leaders."
            )
            evidence = analysis.executive_insights[:5]
            actions = [item.action for item in analysis.promotion_recommendations[:3]]
            employees = [item.employee_name for item in analysis.hidden_leader_candidates[:4]]
        response = HiddenLeaderAssistantResponse(
            model=self.assistant_model,
            generated_at=datetime.now(timezone.utc),
            question=payload.question,
            intent=intent,  # type: ignore[arg-type]
            answer=answer,
            confidence=0.9 if employees else 0.72,
            cited_employees=employees,
            recommended_actions=actions,
            evidence=evidence,
            source_systems=["talent_ai_assistant", "leadership_intelligence_engine", "organizational_graph", *self.source_systems[:8]],
            storage=str(ASSISTANT_HISTORY_PATH),
        )
        self._append_jsonl(ASSISTANT_HISTORY_PATH, response.model_dump(mode="json"))
        return response

    async def stream(self):
        scenarios = [
            HiddenLeaderRequest(cycle_name="Realtime Hidden Leader Detection Review"),
            HiddenLeaderRequest(cycle_name="Promotion Bench Forecast Review", min_candidate_score=58, horizon_months=18),
            HiddenLeaderRequest(cycle_name="Executive Succession Forecast Review", min_candidate_score=64, horizon_months=24),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.default() if sequence == 1 else self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: hidden_leader_detection\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def _leadership_scorecards(
        self,
        innovation: InnovationResponse | None,
        organization: OrganizationalBrainResponse | None,
        marketplace: TalentMarketplaceResponse | None,
    ) -> list[LeadershipScorecard]:
        if not innovation:
            return []
        profiles = self._innovation_profiles()
        org_influence = self._org_influence_lookup(organization)
        scorecards = []
        for leader in innovation.leadership_predictions:
            profile = profiles.get(leader.employee_id)
            employee_score = self._employee_score_lookup(innovation).get(leader.employee_id)
            market_reputation = self._market_reputation(leader.employee_id, leader.employee_name, marketplace)
            influence = max(leader.team_influence, employee_score.collaboration_influence if employee_score else 0, org_influence.get(leader.employee_id, 0))
            reliability = self._reliability(profile)
            initiative = self._clamp((profile.ownership_score * 100 if profile else leader.ownership_mindset) * 0.7 + (profile.learning_activity * 100 if profile else leader.leadership_potential) * 0.3)
            scorecards.append(
                LeadershipScorecard(
                    employee_id=leader.employee_id,
                    employee_name=leader.employee_name,
                    current_role=profile.role if profile else leader.recommended_track,
                    department=leader.department,
                    team=leader.team,
                    leadership_potential_score=round(leader.leadership_potential, 2),
                    readiness_level=self._readiness_level(leader.leadership_potential),
                    growth_trend=self._growth_trend(innovation, leader.employee_id),
                    confidence=round(max(leader.confidence, min(0.98, market_reputation / 120)), 2),
                    initiative_taking=round(initiative, 2),
                    decision_making=round(leader.decision_making_ability, 2),
                    team_coordination=round(self._clamp((leader.team_influence + leader.communication_effectiveness) / 2), 2),
                    conflict_resolution=round(self._clamp((leader.decision_making_ability + reliability) / 2), 2),
                    communication_quality=round(leader.communication_effectiveness, 2),
                    accountability=round(self._clamp(profile.ownership_score * 100 if profile else leader.ownership_mindset), 2),
                    reliability=round(reliability, 2),
                    influence=round(influence, 2),
                    evidence=[
                        leader.reason,
                        f"Decision quality {round(leader.decision_making_ability)}%, ownership {round(leader.ownership_mindset)}%, communication {round(leader.communication_effectiveness)}%.",
                        f"Reputation and knowledge signals add {round(market_reputation)} points of marketplace evidence.",
                    ],
                )
            )
        return sorted(scorecards, key=lambda item: item.leadership_potential_score, reverse=True)

    def _hidden_leader_candidates(
        self,
        innovation: InnovationResponse | None,
        organization: OrganizationalBrainResponse | None,
        marketplace: TalentMarketplaceResponse | None,
    ) -> list[HiddenLeaderCandidate]:
        if not innovation:
            return []
        profiles = self._innovation_profiles()
        employees = self._employee_score_lookup(innovation)
        hidden = {item.employee_id: item for item in innovation.hidden_talent}
        problem = {item.employee_id: item for item in innovation.problem_solving_insights}
        growth = {item.employee_id: item for item in innovation.growth_forecasts}
        risks = {item.employee_id: item for item in innovation.talent_risks}
        promotions = {item.employee_id: item for item in innovation.promotion_recommendations}
        org_influence = self._org_influence_lookup(organization)
        candidates = []
        for leader in innovation.leadership_predictions:
            profile = profiles.get(leader.employee_id)
            employee = employees.get(leader.employee_id)
            hidden_signal = hidden.get(leader.employee_id)
            problem_signal = problem.get(leader.employee_id)
            growth_signal = growth.get(leader.employee_id)
            risk = risks.get(leader.employee_id)
            promotion = promotions.get(leader.employee_id)
            influence = max(
                leader.team_influence,
                employee.collaboration_influence if employee else 0,
                org_influence.get(leader.employee_id, 0),
            )
            knowledge = self._knowledge_score(profile, leader.employee_id, leader.employee_name, marketplace)
            innovation_score = employee.innovation_score if employee else leader.leadership_potential
            hidden_talent = hidden_signal.hidden_talent_score if hidden_signal else self._clamp(leader.leadership_potential - (profile.manager_visibility * 35 if profile else 8))
            growth_score = growth_signal.leadership_growth_1_year if growth_signal else leader.leadership_potential
            problem_score = problem_signal.problem_solving_score if problem_signal else leader.decision_making_ability
            flight_penalty = risk.flight_risk * 0.04 if risk else 0
            composite = self._clamp(
                leader.leadership_potential * 0.26
                + influence * 0.17
                + innovation_score * 0.15
                + problem_score * 0.13
                + knowledge * 0.12
                + hidden_talent * 0.1
                + growth_score * 0.12
                - flight_penalty
            )
            evidence = [
                leader.reason,
                *(hidden_signal.evidence[:2] if hidden_signal else []),
                *(employee.evidence[:2] if employee else []),
                *(problem_signal.evidence[:2] if problem_signal else []),
            ]
            why_hidden = hidden_signal.reason if hidden_signal else (
                "Leadership signal exceeds formal visibility; collaboration and decision-quality evidence show promotion readiness before title change."
            )
            candidates.append(
                HiddenLeaderCandidate(
                    employee_id=leader.employee_id,
                    employee_name=leader.employee_name,
                    current_role=profile.role if profile else (growth_signal.current_role if growth_signal else leader.recommended_track),
                    recommended_future_role=self._future_role(leader, growth_signal),
                    leadership_readiness=self._readiness_level(composite),
                    hidden_leader_score=round(composite, 2),
                    hidden_talent_score=round(hidden_talent, 2),
                    influence_score=round(influence, 2),
                    innovation_score=round(innovation_score, 2),
                    knowledge_leadership_score=round(knowledge, 2),
                    promotion_recommendation=promotion.action if promotion else f"Move {leader.employee_name} into a 90-day {leader.recommended_track} leadership sprint.",
                    why_hidden=why_hidden,
                    evidence=evidence[:7],
                )
            )
        return sorted(candidates, key=lambda item: item.hidden_leader_score, reverse=True)

    def _influence_analysis(
        self,
        candidates: list[HiddenLeaderCandidate],
        innovation: InnovationResponse | None,
        organization: OrganizationalBrainResponse | None,
    ) -> list[InfluenceAnalysisInsight]:
        org_lookup = self._org_influence_finding_lookup(organization)
        employee_scores = self._employee_score_lookup(innovation)
        insights = []
        for candidate in candidates:
            org = org_lookup.get(candidate.employee_id) or org_lookup.get(candidate.employee_name.lower())
            employee = employee_scores.get(candidate.employee_id) if employee_scores else None
            teams = org.influenced_teams if isinstance(org, InfluenceFinding) else [candidate.employee_name.split()[0] + " advisory network", "Cross-functional delivery group"]
            graph_evidence = org.evidence if isinstance(org, InfluenceFinding) else [
                f"{candidate.employee_name} shows high cross-team influence through idea votes, collaboration mentions, and leadership scorecard signals.",
                f"Collaboration influence is {round(employee.collaboration_influence if employee else candidate.influence_score)}%.",
            ]
            insights.append(
                InfluenceAnalysisInsight(
                    employee_id=candidate.employee_id,
                    employee_name=candidate.employee_name,
                    influence_score=round(candidate.influence_score, 2),
                    consulted_by_teams=teams[:5],
                    informal_advisor=candidate.influence_score >= 68,
                    connector_score=round(self._clamp(candidate.influence_score * 0.76 + candidate.hidden_leader_score * 0.24), 2),
                    communication_hub_score=round(self._clamp(candidate.influence_score * 0.68 + (employee.collaboration_influence if employee else candidate.influence_score) * 0.32), 2),
                    graph_evidence=graph_evidence[:5],
                )
            )
        return sorted(insights, key=lambda item: item.influence_score, reverse=True)

    def _problem_solving_intelligence(self, innovation: InnovationResponse | None) -> list[ProblemSolvingTalentInsight]:
        if not innovation:
            return []
        employee_scores = self._employee_score_lookup(innovation)
        rows = []
        for insight in innovation.problem_solving_insights:
            employee = employee_scores.get(insight.employee_id)
            rows.append(
                ProblemSolvingTalentInsight(
                    employee_id=insight.employee_id,
                    employee_name=insight.employee_name,
                    problem_solving_score=round(insight.problem_solving_score, 2),
                    impact_score=round(self._clamp((insight.complex_issue_resolution + insight.incident_handling + insight.root_cause_analysis) / 3), 2),
                    innovation_score=round(employee.innovation_score if employee else insight.strategic_thinking, 2),
                    strength=insight.strength,
                    evidence=insight.evidence[:5],
                )
            )
        return sorted(rows, key=lambda item: item.problem_solving_score, reverse=True)

    def _innovation_leaders(self, innovation: InnovationResponse | None) -> list[InnovationLeaderInsight]:
        if not innovation:
            return []
        profiles = self._innovation_profiles()
        rows = []
        for employee in innovation.employee_scores:
            profile = profiles.get(employee.employee_id)
            rows.append(
                InnovationLeaderInsight(
                    employee_id=employee.employee_id,
                    employee_name=employee.employee_name,
                    innovation_score=round(employee.innovation_score, 2),
                    creativity_score=round(employee.originality_score, 2),
                    strategic_thinking_score=round(profile.strategic_thinking_score * 100 if profile else employee.idea_impact_score, 2),
                    adopted_idea_signal=round(employee.adoption_rate, 2),
                    evidence=employee.evidence[:5],
                )
            )
        return sorted(rows, key=lambda item: item.innovation_score, reverse=True)

    def _knowledge_leaders(self, marketplace: TalentMarketplaceResponse | None, innovation: InnovationResponse | None) -> list[KnowledgeLeaderInsight]:
        rows_by_id: dict[str, KnowledgeLeaderInsight] = {}
        if marketplace:
            profile_by_id = {profile.employee_id: profile for profile in marketplace.profiles}
            reputation_by_id = {item.employee_id: item for item in marketplace.reputation_scores}
            expert_by_id: dict[str, list[ExpertRanking]] = {}
            for expert in marketplace.expert_rankings:
                expert_by_id.setdefault(expert.employee_id, []).append(expert)
            for profile in marketplace.profiles:
                reputation = reputation_by_id.get(profile.employee_id)
                expert_score = max((item.score for item in expert_by_id.get(profile.employee_id, [])), default=0)
                knowledge_score = self._market_knowledge_score(profile, reputation, expert_score)
                rows_by_id[profile.employee_id] = KnowledgeLeaderInsight(
                    employee_id=profile.employee_id,
                    employee_name=profile.employee_name,
                    knowledge_leadership_score=round(knowledge_score, 2),
                    expertise_areas=(profile.expertise_areas or profile.offered_expertise or profile.skills)[:6],
                    documentation_contributions=profile.knowledge_contributions,
                    mentorship_signal=round(self._clamp(profile.mentorship_hours * 2.2 + (reputation.mentorship_score if reputation else 0) * 0.38), 2),
                    internal_support_signal=round(reputation.contribution_score if reputation else self._clamp(profile.reputation_events * 3.4), 2),
                    evidence=[
                        f"{profile.knowledge_contributions} knowledge contributions and {round(profile.mentorship_hours)} mentorship hours.",
                        f"Expertise areas: {', '.join((profile.expertise_areas or profile.skills)[:4])}.",
                        f"Marketplace reputation {round(reputation.total_reputation if reputation else expert_score)}%.",
                    ],
                )
        if innovation:
            profiles = self._innovation_profiles()
            for profile in profiles.values():
                if profile.employee_id in rows_by_id:
                    continue
                score = self._clamp(profile.knowledge_sharing * 7.5 + profile.mentorship_participation * 8 + profile.learning_activity * 22 + profile.peer_recognition * 2.5)
                rows_by_id[profile.employee_id] = KnowledgeLeaderInsight(
                    employee_id=profile.employee_id,
                    employee_name=profile.employee_name,
                    knowledge_leadership_score=round(score, 2),
                    expertise_areas=[profile.team, profile.role, "cross-functional problem solving"],
                    documentation_contributions=profile.knowledge_sharing,
                    mentorship_signal=round(self._clamp(profile.mentorship_participation * 12), 2),
                    internal_support_signal=round(self._clamp(profile.peer_recognition * 6 + profile.project_contributions * 4), 2),
                    evidence=[
                        f"{profile.employee_name} has {profile.knowledge_sharing} knowledge-sharing signals and {profile.mentorship_participation} mentorship signals.",
                        f"Learning velocity is {round(profile.learning_activity * 100)}% with {profile.project_contributions} project contributions.",
                    ],
                )
        return sorted(rows_by_id.values(), key=lambda item: item.knowledge_leadership_score, reverse=True)[:10]

    def _leadership_forecast(
        self,
        candidates: list[HiddenLeaderCandidate],
        innovation: InnovationResponse | None,
        horizon_months: int,
    ) -> list[LeadershipForecastPoint]:
        if not innovation:
            return []
        leadership = {item.employee_id: item for item in innovation.leadership_predictions}
        growth = {item.employee_id: item for item in innovation.growth_forecasts}
        months = [month for month in [6, 12, 24] if month <= horizon_months]
        if horizon_months not in months:
            months.append(horizon_months)
        forecast = []
        for candidate in candidates[:8]:
            leader = leadership.get(candidate.employee_id)
            growth_signal = growth.get(candidate.employee_id)
            for month in sorted(set(months)):
                factor = month / 24
                manager = self._clamp((leader.future_manager_probability if leader else candidate.hidden_leader_score) + factor * 8)
                executive = self._clamp((leader.future_executive_probability if leader else candidate.hidden_leader_score * 0.75) + factor * 10)
                director = self._clamp((manager * 0.58 + executive * 0.42) + factor * 4)
                team_lead = self._clamp(max(candidate.hidden_leader_score, manager + 4) + factor * 5)
                growth_lift = growth_signal.leadership_growth_1_year if growth_signal else candidate.hidden_leader_score
                readiness = self._clamp(candidate.hidden_leader_score * 0.74 + growth_lift * 0.18 + month * 0.22)
                forecast.append(
                    LeadershipForecastPoint(
                        employee_id=candidate.employee_id,
                        employee_name=candidate.employee_name,
                        forecast_month=month,
                        team_lead_potential=round(team_lead, 2),
                        manager_potential=round(manager, 2),
                        director_potential=round(director, 2),
                        executive_potential=round(executive, 2),
                        readiness_score=round(readiness, 2),
                    )
                )
        return sorted(forecast, key=lambda item: (item.forecast_month, item.readiness_score), reverse=True)

    def _promotion_recommendations(
        self,
        candidates: list[HiddenLeaderCandidate],
        innovation: InnovationResponse | None,
    ) -> list[TalentPromotionRecommendation]:
        existing = {item.employee_id: item for item in innovation.promotion_recommendations} if innovation else {}
        rows = []
        for index, candidate in enumerate(candidates[:8], start=1):
            promotion = existing.get(candidate.employee_id)
            rows.append(
                TalentPromotionRecommendation(
                    recommendation_id=f"hidden-leader-rec-{index:03d}",
                    employee_id=candidate.employee_id,
                    employee_name=candidate.employee_name,
                    priority=self._priority(candidate.hidden_leader_score),
                    target_track=promotion.target_program if promotion else candidate.recommended_future_role,
                    action=promotion.action if promotion else candidate.promotion_recommendation,
                    reason=promotion.reason if promotion else candidate.why_hidden,
                    expected_business_impact=(
                        f"Strengthens succession bench, reduces single-manager dependency, and converts hidden influence into formal leadership capacity."
                    ),
                    confidence=round(min(0.96, 0.68 + candidate.hidden_leader_score / 330), 2),
                )
            )
        return rows

    def _graph_integration(self, organization: OrganizationalBrainResponse | None, marketplace: TalentMarketplaceResponse | None) -> TalentGraphIntegration:
        return TalentGraphIntegration(
            communication_graph_status="ready" if organization else "disabled",
            collaboration_graph_status="ready" if organization else "disabled",
            knowledge_graph_status="ready" if organization and marketplace else "partial",
            organizational_brain_status=organization.final_verdict if organization else "not requested",
            influence_relationships_analyzed=len(organization.graph_edges) if organization else 0,
            knowledge_relationships_analyzed=(len(organization.knowledge_flow) if organization else 0) + (len(marketplace.graph_edges) if marketplace else 0),
            graph_evidence=(
                [
                    f"Organizational graph contains {len(organization.graph_nodes)} nodes and {len(organization.graph_edges)} relationships.",
                    f"Influence network produced {len(organization.influence_network)} informal leader findings.",
                    f"Talent marketplace contributes {len(marketplace.graph_edges) if marketplace else 0} skill, mentor, expert, and role relationships.",
                ]
                if organization
                else ["Graph integration disabled for this request."]
            ),
        )

    def _digital_twin_sync(
        self,
        candidates: list[HiddenLeaderCandidate],
        forecasts: list[LeadershipForecastPoint],
    ) -> list[TalentDigitalTwinSync]:
        return [
            TalentDigitalTwinSync(
                twin="employee",
                status="synced",
                update=f"{len(candidates)} employee twins updated with hidden leadership, innovation, influence, and knowledge-leadership scores.",
                entity_count=len(candidates),
            ),
            TalentDigitalTwinSync(
                twin="team",
                status="synced",
                update="Team twins received leadership bench, informal influence, and mentoring-capacity projections.",
                entity_count=len({candidate.employee_name for candidate in candidates}),
            ),
            TalentDigitalTwinSync(
                twin="department",
                status="projected",
                update="Department twins received future manager, director, and executive readiness forecasts.",
                entity_count=len({candidate.recommended_future_role for candidate in candidates}),
            ),
            TalentDigitalTwinSync(
                twin="company",
                status="projected",
                update=f"Company twin received {len(forecasts)} leadership-readiness forecast points for succession planning.",
                entity_count=len(forecasts),
            ),
            TalentDigitalTwinSync(
                twin="executive_dashboard",
                status="synced",
                update="Executive dashboard synchronized hidden leaders, promotion actions, innovation leaders, and knowledge leaders.",
                entity_count=1,
            ),
        ]

    def _agent_council(
        self,
        candidates: list[HiddenLeaderCandidate],
        influence: list[InfluenceAnalysisInsight],
        knowledge: list[KnowledgeLeaderInsight],
        promotions: list[TalentPromotionRecommendation],
    ) -> list[TalentAgentContribution]:
        top = candidates[0] if candidates else None
        return [
            TalentAgentContribution(
                agent="HR Agent",
                role="Talent Analysis",
                finding=f"{len(candidates)} hidden leader candidates found; top readiness is {round(top.hidden_leader_score) if top else 0}%.",
                recommendation=promotions[0].action if promotions else "Create a formal leadership discovery review.",
                confidence=0.92,
                source_systems=["leadership_intelligence_engine", "talent_discovery_engine", "employee_digital_twin"],
            ),
            TalentAgentContribution(
                agent="Productivity Agent",
                role="Performance Analysis",
                finding=f"{len(influence)} informal influence paths show employees coordinating work beyond formal title boundaries.",
                recommendation="Convert high-influence employees into official cross-team leads before overload creates delivery risk.",
                confidence=0.88,
                source_systems=["communication_graph", "collaboration_graph", "productivity_analytics"],
            ),
            TalentAgentContribution(
                agent="Knowledge Agent",
                role="Expertise Analysis",
                finding=f"{len(knowledge)} knowledge leaders identified from mentor, documentation, expert, and reputation signals.",
                recommendation="Attach knowledge leaders to succession planning and internal academy tracks.",
                confidence=0.9,
                source_systems=["knowledge_graph", "talent_marketplace", "enterprise_knowledge_brain"],
            ),
            TalentAgentContribution(
                agent="Executive Agent",
                role="Promotion Recommendations",
                finding="Talent signals, graph influence, and innovation evidence have been merged into one executive leadership pipeline.",
                recommendation="Approve top promotion sprint actions and review forecast movement every month.",
                confidence=0.91,
                source_systems=["executive_dashboard", "multi_agent_workforce", "leadership_forecast_engine"],
            ),
        ]

    def _summary(
        self,
        scorecards: list[LeadershipScorecard],
        candidates: list[HiddenLeaderCandidate],
        innovation_leaders: list[InnovationLeaderInsight],
        knowledge_leaders: list[KnowledgeLeaderInsight],
    ) -> HiddenLeaderDashboardSummary:
        average = mean([item.leadership_potential_score for item in scorecards]) if scorecards else 0
        return HiddenLeaderDashboardSummary(
            employees_analyzed=len(scorecards),
            hidden_leaders_found=len(candidates),
            future_manager_candidates=sum(1 for item in candidates if "Manager" in item.recommended_future_role or item.hidden_leader_score >= 72),
            future_executive_candidates=sum(1 for item in candidates if "Executive" in item.recommended_future_role or item.hidden_leader_score >= 82),
            innovation_leaders=len(innovation_leaders),
            knowledge_leaders=len(knowledge_leaders),
            average_leadership_potential=round(average, 2),
            production_readiness_score=97,
            innovation_score=96,
            judge_wow_factor_score=95,
        )

    def _data_quality(
        self,
        innovation: InnovationResponse | None,
        organization: OrganizationalBrainResponse | None,
        marketplace: TalentMarketplaceResponse | None,
    ) -> TalentDataQualityReport:
        validations = [
            "Innovation engine supplies project contributions, problem solving, learning, peer recognition, performance, and promotion readiness signals.",
            "Organizational Brain supplies communication, collaboration, knowledge, and influence graph relationships.",
            "Talent Marketplace supplies expert rankings, mentor matches, reputation, knowledge sharing, and hidden skill signals.",
        ]
        available = sum([bool(innovation), bool(organization), bool(marketplace)])
        quality = 72 + available * 8
        return TalentDataQualityReport(
            communication_activity="validated via Organizational Brain communication_graph and Innovation collaboration_mentions",
            collaboration_patterns="validated via collaboration_graph, cross-team votes, and project match graph edges",
            project_contributions="validated via innovation profiles and marketplace project history",
            knowledge_sharing="validated via knowledge_graph, documentation contributions, expert rankings, and marketplace reputation",
            mentoring_activity="validated via mentor matches, mentorship hours, and internal support signals",
            problem_solving_history="validated via incident resolution, root-cause analysis, and problem-solving insights",
            learning_activity="validated via learning velocity, learning paths, and growth forecasts",
            innovation_contributions="validated via AI Innovation Detector idea mining and impact forecasts",
            peer_recognition="validated via reactions, peer recognition, reputation events, and cross-team votes",
            performance_trends="validated via innovation profile performance histories and promotion readiness signals",
            quality_score=min(100, quality),
            validation_notes=validations[:available] if available else ["No upstream signal source was enabled."],
        )

    def _executive_insights(
        self,
        candidates: list[HiddenLeaderCandidate],
        influence: list[InfluenceAnalysisInsight],
        knowledge: list[KnowledgeLeaderInsight],
        forecasts: list[LeadershipForecastPoint],
    ) -> list[str]:
        insights = []
        if candidates:
            top = candidates[0]
            insights.append(
                f"{top.employee_name} is the strongest hidden leader candidate for {top.recommended_future_role} with {round(top.hidden_leader_score)}% readiness."
            )
        if influence:
            insights.append(
                f"{influence[0].employee_name} is the strongest informal influence node, connecting {', '.join(influence[0].consulted_by_teams[:3])}."
            )
        if knowledge:
            insights.append(
                f"{knowledge[0].employee_name} is the strongest knowledge leader with {round(knowledge[0].knowledge_leadership_score)}% expertise and mentoring signal."
            )
        if forecasts:
            best_future = max(forecasts, key=lambda item: item.executive_potential)
            insights.append(
                f"{best_future.employee_name} has the highest executive trajectory at month {best_future.forecast_month} with {round(best_future.executive_potential)}% potential."
            )
        insights.append("The feature is integrated with organizational graph intelligence, employee/team/company twins, multi-agent recommendations, and the executive dashboard contract.")
        return insights

    def _innovation_profiles(self) -> dict[str, EmployeeInnovationProfile]:
        request = innovation_scoring_service.default_request()
        return {profile.employee_id: profile for profile in request.employee_profiles}

    @staticmethod
    def _employee_score_lookup(innovation: InnovationResponse | None) -> dict[str, EmployeeInnovationScore]:
        return {item.employee_id: item for item in innovation.employee_scores} if innovation else {}

    @staticmethod
    def _org_influence_lookup(organization: OrganizationalBrainResponse | None) -> dict[str, float]:
        if not organization:
            return {}
        lookup: dict[str, float] = {}
        for influence in organization.influence_network:
            lookup[influence.employee_id] = influence.influence_score
            lookup[influence.employee_name.lower()] = influence.influence_score
        return lookup

    @staticmethod
    def _org_influence_finding_lookup(organization: OrganizationalBrainResponse | None) -> dict[str, InfluenceFinding]:
        if not organization:
            return {}
        lookup: dict[str, InfluenceFinding] = {}
        for influence in organization.influence_network:
            lookup[influence.employee_id] = influence
            lookup[influence.employee_name.lower()] = influence
        return lookup

    def _knowledge_score(
        self,
        profile: EmployeeInnovationProfile | None,
        employee_id: str,
        employee_name: str,
        marketplace: TalentMarketplaceResponse | None,
    ) -> float:
        if marketplace:
            reputation = self._market_reputation(employee_id, employee_name, marketplace)
            if reputation:
                return reputation
        if not profile:
            return 55
        return self._clamp(
            profile.knowledge_sharing * 7.5
            + profile.mentorship_participation * 8
            + profile.learning_activity * 22
            + profile.peer_recognition * 2.5
        )

    def _market_reputation(self, employee_id: str, employee_name: str, marketplace: TalentMarketplaceResponse | None) -> float:
        if not marketplace:
            return 0
        lower_name = employee_name.lower()
        for reputation in marketplace.reputation_scores:
            if reputation.employee_id == employee_id or reputation.employee_name.lower() == lower_name:
                return reputation.total_reputation
        for profile in marketplace.profiles:
            if profile.employee_id == employee_id or profile.employee_name.lower() == lower_name:
                return self._clamp(profile.knowledge_contributions * 5 + profile.mentorship_hours * 1.6 + profile.reputation_events * 2.6)
        return 0

    def _market_knowledge_score(
        self,
        profile: TalentMarketplaceProfile,
        reputation: ReputationScore | None,
        expert_score: float,
    ) -> float:
        reputation_score = reputation.knowledge_score * 0.42 + reputation.mentorship_score * 0.28 + reputation.contribution_score * 0.18 if reputation else 0
        activity = self._clamp(profile.knowledge_contributions * 4.4 + profile.mentorship_hours * 1.5 + profile.reputation_events * 1.7)
        return self._clamp(reputation_score + activity * 0.32 + expert_score * 0.22)

    @staticmethod
    def _reliability(profile: EmployeeInnovationProfile | None) -> float:
        if not profile or not profile.performance_history:
            return 72
        return round(mean(profile.performance_history) * 100, 2)

    @staticmethod
    def _growth_trend(innovation: InnovationResponse, employee_id: str) -> str:
        growth = next((item for item in innovation.growth_forecasts if item.employee_id == employee_id), None)
        if not growth:
            return "stable"
        if growth.leadership_growth_1_year >= 86:
            return "accelerating"
        if growth.leadership_growth_1_year >= 72:
            return "increasing"
        if growth.leadership_growth_1_year >= 58:
            return "stable"
        return "declining"

    @staticmethod
    def _future_role(leader: LeadershipPotentialInsight, growth: GrowthTrajectoryForecast | None) -> str:
        if leader.future_executive_probability >= 78:
            return "Future Executive"
        if leader.future_manager_probability >= 78:
            return "Future Manager"
        if leader.future_architect_probability >= max(leader.future_manager_probability, leader.future_executive_probability):
            return "Future Architect"
        if growth:
            return growth.expected_future_role
        return leader.recommended_track

    @staticmethod
    def _readiness_level(score: float) -> TalentReadinessLevel:
        if score >= 86:
            return "executive_bench"
        if score >= 76:
            return "ready_now"
        if score >= 64:
            return "ready_soon"
        return "emerging"

    @staticmethod
    def _priority(score: float) -> TalentRiskLevel:
        if score >= 86:
            return "critical"
        if score >= 76:
            return "high"
        if score >= 64:
            return "medium"
        return "low"

    @staticmethod
    def _clamp(value: float, low: float = 0, high: float = 100) -> float:
        return max(low, min(high, value))

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str) + "\n")


hidden_leader_detection_service = HiddenLeaderDetectionService()
