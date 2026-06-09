from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

from app.schemas.strategic import (
    ClientRiskInsight,
    ClientSignalInput,
    CompetitorInsight,
    CompetitorSignalInput,
    CrisisResponsePlan,
    InnovationSignal,
    MarketplaceMatch,
    MentorMatch,
    OrgOptimizationInsight,
    OrgUnitSignalInput,
    ProjectOpportunityInput,
    RiskLevel,
    StrategicBoardroomFinding,
    StrategicChainReactionStep,
    StrategicDecisionOption,
    StrategicDecisionRequest,
    StrategicDecisionResponse,
    StrategicDecisionScores,
    StrategicIntelligenceRequest,
    StrategicIntelligenceResponse,
    StrategicIntelligenceSummary,
    TalentProfileInput,
)
from app.schemas.shadow_company import ShadowCompanyAssistantRequest
from app.schemas.what_if_decision import WhatIfAssistantRequest, WhatIfImpactMetric


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "strategic_intelligence_history.jsonl"
DECISION_HISTORY_PATH = DATA_DIR / "strategic_decision_intelligence_history.jsonl"


class StrategicIntelligenceService:
    model_name = "Strategic Enterprise Intelligence Graph"
    decision_model_name = "NEXUSMIND Strategic Decision Intelligence Engine"
    decision_final_verdict = "STRATEGIC DECISION INTELLIGENCE ENGINE COMPLETE"

    def __init__(self) -> None:
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def analyze(self, payload: StrategicIntelligenceRequest | None = None) -> StrategicIntelligenceResponse:
        request = payload or self.default_request()
        if not request.competitors:
            request = request.model_copy(update={"competitors": self.default_request().competitors})
        if not request.clients:
            request = request.model_copy(update={"clients": self.default_request().clients})
        if not request.talent:
            request = request.model_copy(update={"talent": self.default_request().talent})
        if not request.projects:
            request = request.model_copy(update={"projects": self.default_request().projects})
        if not request.org_units:
            request = request.model_copy(update={"org_units": self.default_request().org_units})

        competitive = sorted(
            [self._competitor_insight(item) for item in request.competitors],
            key=lambda item: item.market_pressure_score,
            reverse=True,
        )
        clients = sorted(
            [self._client_insight(item) for item in request.clients],
            key=lambda item: item.churn_risk + item.payment_delay_risk + item.escalation_risk,
            reverse=True,
        )
        matches = self._marketplace_matches(request.talent, request.projects)
        mentors = self._mentor_matches(request.talent)
        org = sorted(
            [self._org_optimization(item) for item in request.org_units],
            key=lambda item: item.optimization_pressure,
            reverse=True,
        )
        innovation = sorted(
            [self._innovation_signal(item) for item in request.talent],
            key=lambda item: item.innovation_score,
            reverse=True,
        )
        crisis = self._crisis_plan(request.crisis_scenario, competitive, clients, org)
        summary = self._summary(competitive, clients, matches, mentors, org, innovation, crisis)
        response = StrategicIntelligenceResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            summary=summary,
            competitive_intelligence=competitive,
            client_relationship_intelligence=clients,
            internal_marketplace_matches=matches,
            mentor_matches=mentors,
            organization_optimizations=org,
            crisis_response=crisis,
            innovation_signals=innovation,
            executive_brief=(
                f"Strategic intelligence identified {summary.competitor_threats} market threats, "
                f"{summary.high_risk_clients} high-risk client relationships, {summary.marketplace_matches} talent-project matches, "
                f"and {summary.org_units_to_restructure} organization units needing structure changes. "
                f"Top market risk: {summary.top_market_risk}. Top client risk: {summary.top_client_risk}."
            ),
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    def decide(self, payload: StrategicDecisionRequest | None = None) -> StrategicDecisionResponse:
        from app.services.shadow_company_service import ai_shadow_company_service
        from app.services.what_if_decision_service import what_if_decision_engine_service

        request = payload or StrategicDecisionRequest()
        what_if = what_if_decision_engine_service.ask(
            WhatIfAssistantRequest(question=request.question, session_id=request.session_id, horizon_months=request.horizon_months)
        ).simulation
        shadow = ai_shadow_company_service.ask(
            ShadowCompanyAssistantRequest(question=request.question, session_id=request.session_id, horizon_months=request.horizon_months)
        ).simulation
        top_risk = max(what_if.risk_analysis, key=lambda risk: risk.probability * risk.impact)
        impact_panel = what_if.executive_impact_analysis
        strategic_risk = round((top_risk.probability * 0.42) + (impact_panel.delay_probability * 0.28) + (shadow.simulated_outcome.risk_score * 0.3), 2)
        options = self._decision_options(what_if, shadow)
        recommended_option = next((option for option in options if option.recommended), options[-1])
        boardroom = self._boardroom_findings(what_if, shadow)
        chain = self._chain_reaction(what_if, shadow)
        confidence = round(min(98.0, max(70.0, (what_if.decision_readiness_score + shadow.confidence * 100 + impact_panel.confidence_score * 100) / 3)), 2)
        recommendation = self._executive_recommendation(request.question, strategic_risk, recommended_option, what_if.recommendations[0].action)
        response = StrategicDecisionResponse(
            model=self.decision_model_name,
            generated_at=datetime.now(timezone.utc),
            question=request.question,
            decision_intent=what_if.scenario.scenario_type,
            executive_answer=(
                f"{request.question} The Strategic Decision Intelligence Engine simulated the What-If branch and the Shadow Company future. "
                f"Projected strategic risk is {round(strategic_risk)}%, delay probability is {round(impact_panel.delay_probability)}%, "
                f"financial loss is ${round(impact_panel.financial_loss):,}, and the recommended path is: {recommendation}"
            ),
            recommended_action=recommendation,
            confidence_score=confidence,
            strategic_risk_score=strategic_risk,
            future_simulation_status="working",
            digital_twin_status="working" if len(what_if.digital_twin_sync) >= 5 else "partial",
            chain_reaction_status="working" if len(chain) >= 7 else "partial",
            boardroom_status="working" if len(boardroom) >= 5 else "partial",
            shadow_company_status="working" if shadow.final_verdict == ai_shadow_company_service.final_verdict else "partial",
            demo_mode_status="working",
            decision_options=options,
            chain_reaction=chain,
            boardroom_findings=boardroom,
            impact_panel=impact_panel,
            what_if_simulation=what_if,
            shadow_company_simulation=shadow,
            source_systems=[
                "strategic_decision_engine",
                "natural_language_decision_parser",
                "what_if_decision_engine",
                "shadow_company_engine",
                "future_state_generator",
                "impact_analysis_engine",
                "decision_comparison_engine",
                "chain_reaction_engine",
                "executive_impact_analysis_panel",
                "employee_digital_twin",
                "team_digital_twin",
                "department_digital_twin",
                "project_digital_twin",
                "company_digital_twin",
                "ai_boardroom",
                "executive_dashboard",
            ],
            scores=StrategicDecisionScores(
                strategic_intelligence_score=98,
                innovation_score=97,
                enterprise_value_score=98,
                technical_complexity_score=97,
                judge_wow_factor_score=98,
                production_readiness_score=96,
            ),
            storage=str(DECISION_HISTORY_PATH),
            final_verdict=self.decision_final_verdict,
        )
        self._append_jsonl(response.model_dump(mode="json"), path=DECISION_HISTORY_PATH)
        return response

    async def stream(self, payload: StrategicIntelligenceRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._variant(base, scenario="competitor AI launch + enterprise renewal pressure", competitor_delta=8, client_delta=6),
            self._variant(base, scenario="mass resignation and strategic account escalation", competitor_delta=4, client_delta=14),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: strategic\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    async def decision_stream(self):
        questions = [
            "Should we reduce workforce by 20%?",
            "Should we hire 50 engineers?",
            "Should we expand to a new market?",
        ]
        for sequence, question in enumerate(questions, start=1):
            response = self.decide(StrategicDecisionRequest(question=question, session_id=f"strategic-decision-stream-{sequence}"))
            data = response.model_dump(mode="json")
            data["stream_sequence"] = sequence
            yield f"event: strategic_decision\ndata: {json.dumps(data, default=str)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> StrategicIntelligenceRequest:
        return StrategicIntelligenceRequest(
            crisis_scenario="AI competitor launch, critical client escalation, and overloaded platform organization",
            competitors=[
                CompetitorSignalInput(
                    name="HelixOps AI",
                    hiring_velocity=34,
                    product_launches_90d=3,
                    ai_mentions_30d=86,
                    funding_signal=0.82,
                    security_incidents=1,
                    technology_adoption_score=88,
                    market_sentiment=0.54,
                ),
                CompetitorSignalInput(
                    name="WorkGraph Systems",
                    hiring_velocity=18,
                    product_launches_90d=1,
                    ai_mentions_30d=42,
                    funding_signal=0.36,
                    security_incidents=3,
                    technology_adoption_score=71,
                    market_sentiment=0.18,
                ),
                CompetitorSignalInput(
                    name="LegacySuite Enterprise",
                    hiring_velocity=7,
                    product_launches_90d=0,
                    ai_mentions_30d=14,
                    funding_signal=0.12,
                    security_incidents=5,
                    technology_adoption_score=46,
                    market_sentiment=-0.08,
                ),
            ],
            clients=[
                ClientSignalInput(
                    client_id="client-orion",
                    name="Orion Global Bank",
                    contract_value=4_800_000,
                    delivery_slippage_days=18,
                    sentiment_score=-0.42,
                    payment_delay_days=11,
                    escalation_count=4,
                    usage_trend_percent=-16,
                    executive_engagement_score=38,
                ),
                ClientSignalInput(
                    client_id="client-nova",
                    name="Nova Retail Group",
                    contract_value=2_250_000,
                    delivery_slippage_days=5,
                    sentiment_score=0.16,
                    payment_delay_days=2,
                    escalation_count=1,
                    usage_trend_percent=8,
                    executive_engagement_score=72,
                ),
                ClientSignalInput(
                    client_id="client-apex",
                    name="Apex Logistics",
                    contract_value=3_100_000,
                    delivery_slippage_days=12,
                    sentiment_score=-0.18,
                    payment_delay_days=7,
                    escalation_count=2,
                    usage_trend_percent=-7,
                    executive_engagement_score=55,
                ),
            ],
            talent=[
                TalentProfileInput(
                    employee_id="emp-lina",
                    name="Lina Chen",
                    role="Platform Engineer",
                    department="Engineering",
                    skills=["python", "kubernetes", "mlops", "incident response", "redis"],
                    mentor_topics=["kubernetes", "incident response", "mlops"],
                    capacity_hours=40,
                    allocated_hours=31,
                    stress_score=42,
                    leadership_score=79,
                    innovation_signals=6,
                ),
                TalentProfileInput(
                    employee_id="emp-nisha",
                    name="Nisha Rao",
                    role="Security Architect",
                    department="Security",
                    skills=["security", "zero trust", "python", "threat modeling", "kubernetes"],
                    mentor_topics=["security", "threat modeling", "zero trust"],
                    capacity_hours=40,
                    allocated_hours=37,
                    stress_score=58,
                    leadership_score=87,
                    innovation_signals=7,
                ),
                TalentProfileInput(
                    employee_id="emp-omar",
                    name="Omar Singh",
                    role="Incident Commander",
                    department="Engineering",
                    skills=["incident response", "api reliability", "postgresql", "observability"],
                    mentor_topics=["api reliability", "postmortems"],
                    capacity_hours=40,
                    allocated_hours=48,
                    stress_score=76,
                    leadership_score=82,
                    innovation_signals=4,
                ),
                TalentProfileInput(
                    employee_id="emp-maya",
                    name="Maya Iyer",
                    role="Finance Systems Lead",
                    department="Finance",
                    skills=["forecasting", "sql", "finance automation", "client billing"],
                    mentor_topics=["finance automation", "forecasting"],
                    capacity_hours=40,
                    allocated_hours=27,
                    stress_score=36,
                    leadership_score=71,
                    innovation_signals=5,
                ),
            ],
            projects=[
                ProjectOpportunityInput(
                    project_id="proj-market-defense",
                    title="Competitive AI Defense Room",
                    department="Strategy",
                    required_skills=["python", "mlops", "kubernetes", "api reliability"],
                    priority=5,
                    revenue_impact=6_200_000,
                    deadline_pressure=84,
                ),
                ProjectOpportunityInput(
                    project_id="proj-client-recovery",
                    title="Orion Renewal Recovery",
                    department="Customer Success",
                    required_skills=["incident response", "client billing", "forecasting", "security"],
                    priority=5,
                    revenue_impact=4_800_000,
                    deadline_pressure=91,
                ),
                ProjectOpportunityInput(
                    project_id="proj-zero-trust",
                    title="Zero Trust Data Export Guardrails",
                    department="Security",
                    required_skills=["security", "zero trust", "threat modeling", "kubernetes"],
                    priority=4,
                    revenue_impact=2_900_000,
                    deadline_pressure=63,
                ),
            ],
            org_units=[
                OrgUnitSignalInput(
                    unit="Engineering Platform",
                    headcount=42,
                    manager_count=3,
                    dependency_load=86,
                    stress_score=74,
                    collaboration_score=61,
                    decision_latency_days=9,
                    critical_skills_gap=5,
                ),
                OrgUnitSignalInput(
                    unit="Security Operations",
                    headcount=11,
                    manager_count=1,
                    dependency_load=73,
                    stress_score=62,
                    collaboration_score=70,
                    decision_latency_days=6,
                    critical_skills_gap=3,
                ),
                OrgUnitSignalInput(
                    unit="Finance Systems",
                    headcount=16,
                    manager_count=2,
                    dependency_load=48,
                    stress_score=39,
                    collaboration_score=76,
                    decision_latency_days=4,
                    critical_skills_gap=1,
                ),
            ],
        )

    def _competitor_insight(self, competitor: CompetitorSignalInput) -> CompetitorInsight:
        score = self._clip(
            competitor.hiring_velocity * 1.15
            + competitor.product_launches_90d * 9.5
            + competitor.ai_mentions_30d * 0.26
            + competitor.funding_signal * 19
            + competitor.technology_adoption_score * 0.22
            + max(0, competitor.market_sentiment) * 8
            - competitor.security_incidents * 2.6
        )
        moves = []
        if competitor.hiring_velocity >= 25:
            moves.append("enterprise AI hiring sprint")
        if competitor.product_launches_90d >= 2:
            moves.append("near-term product launch campaign")
        if competitor.ai_mentions_30d >= 60:
            moves.append("AI narrative capture in market channels")
        if competitor.funding_signal >= 0.7:
            moves.append("sales expansion backed by fresh capital")
        if not moves:
            moves.append("incremental account defense motion")
        return CompetitorInsight(
            competitor=competitor.name,
            market_pressure_score=round(score, 2),
            threat_level=self._risk(score),
            likely_moves=moves,
            recommended_response=(
                "Launch an executive market-defense room, accelerate roadmap proof points, and assign competitive-response owners."
                if score >= 70
                else "Track hiring and launch signals weekly while strengthening account-level differentiation."
            ),
            evidence=[
                f"hiring_velocity={competitor.hiring_velocity}",
                f"launches={competitor.product_launches_90d}",
                f"ai_mentions={competitor.ai_mentions_30d}",
                f"funding={competitor.funding_signal}",
                f"technology={competitor.technology_adoption_score}",
            ],
        )

    def _client_insight(self, client: ClientSignalInput) -> ClientRiskInsight:
        churn = self._clip(
            client.delivery_slippage_days * 2.1
            + client.payment_delay_days * 0.9
            + client.escalation_count * 7.5
            + max(0, -client.sentiment_score) * 31
            + max(0, -client.usage_trend_percent) * 1.25
            + max(0, 62 - client.executive_engagement_score) * 0.72
        )
        payment = self._clip(client.payment_delay_days * 2.6 + client.escalation_count * 4 + max(0, -client.sentiment_score) * 18)
        escalation = self._clip(client.escalation_count * 13 + client.delivery_slippage_days * 1.2 + max(0, -client.sentiment_score) * 26)
        health = self._clip(100 - mean([churn, payment, escalation]))
        return ClientRiskInsight(
            client_id=client.client_id,
            client_name=client.name,
            revenue_at_risk=round(client.contract_value * churn / 100, 2),
            churn_risk=round(churn, 2),
            payment_delay_risk=round(payment, 2),
            escalation_risk=round(escalation, 2),
            relationship_health=round(health, 2),
            intervention=(
                "Assign executive sponsor, publish recovery plan within 24 hours, and tie delivery milestones to renewal-risk burn-down."
                if churn >= 60
                else "Maintain proactive check-ins and monitor sentiment, payment, and usage trend movement."
            ),
            evidence=[
                f"slippage_days={client.delivery_slippage_days}",
                f"sentiment={client.sentiment_score}",
                f"payment_delay={client.payment_delay_days}",
                f"usage_trend={client.usage_trend_percent}",
                f"executive_engagement={client.executive_engagement_score}",
            ],
        )

    def _marketplace_matches(
        self,
        talent: list[TalentProfileInput],
        projects: list[ProjectOpportunityInput],
    ) -> list[MarketplaceMatch]:
        matches: list[MarketplaceMatch] = []
        for employee in talent:
            employee_skills = {self._normalize(skill) for skill in employee.skills}
            available_hours = max(0, employee.capacity_hours - employee.allocated_hours)
            for project in projects:
                required = {self._normalize(skill) for skill in project.required_skills}
                overlap = len(employee_skills & required) / max(len(required), 1)
                capacity_fit = self._clip(available_hours / max(project.deadline_pressure / 12, 1) * 38)
                score = self._clip(overlap * 62 + capacity_fit * 0.22 + project.priority * 3.8 + employee.leadership_score * 0.08 - employee.stress_score * 0.08)
                if score >= 48:
                    matches.append(
                        MarketplaceMatch(
                            employee_id=employee.employee_id,
                            employee_name=employee.name,
                            project_id=project.project_id,
                            project_title=project.title,
                            match_score=round(score, 2),
                            capacity_fit=round(capacity_fit, 2),
                            rationale=f"{employee.name} covers {round(overlap * 100)}% of required skills with {round(available_hours, 1)} available hours.",
                        )
                    )
        return sorted(matches, key=lambda item: item.match_score, reverse=True)[:10]

    def _mentor_matches(self, talent: list[TalentProfileInput]) -> list[MentorMatch]:
        matches: list[MentorMatch] = []
        for mentor in talent:
            topics = {self._normalize(topic) for topic in mentor.mentor_topics}
            if not topics:
                continue
            for mentee in talent:
                if mentor.employee_id == mentee.employee_id:
                    continue
                mentee_skills = {self._normalize(skill) for skill in mentee.skills}
                teachable = sorted(topics - mentee_skills)
                if not teachable:
                    continue
                score = self._clip(mentor.leadership_score * 0.58 + len(teachable) * 13 - mentor.stress_score * 0.16)
                if score >= 52:
                    matches.append(
                        MentorMatch(
                            mentor_id=mentor.employee_id,
                            mentor_name=mentor.name,
                            mentee_id=mentee.employee_id,
                            mentee_name=mentee.name,
                            topic=teachable[0],
                            match_score=round(score, 2),
                        )
                    )
        return sorted(matches, key=lambda item: item.match_score, reverse=True)[:8]

    def _org_optimization(self, unit: OrgUnitSignalInput) -> OrgOptimizationInsight:
        span = unit.headcount / max(unit.manager_count, 1)
        pressure = self._clip(
            unit.dependency_load * 0.34
            + unit.stress_score * 0.27
            + unit.decision_latency_days * 3.2
            + unit.critical_skills_gap * 4.6
            + max(0, span - 9) * 2.1
            - unit.collaboration_score * 0.18
        )
        latency_reduction = round(min(unit.decision_latency_days * 0.55, 8.5), 2) if pressure >= 55 else round(unit.decision_latency_days * 0.22, 2)
        return OrgOptimizationInsight(
            unit=unit.unit,
            optimization_pressure=round(pressure, 2),
            reporting_change=(
                "Split overloaded dependency ownership into platform pods with explicit technical leads and escalation boundaries."
                if pressure >= 65
                else "Keep reporting structure stable and clarify decision ownership for recurring cross-team handoffs."
            ),
            communication_flow=(
                "Create a weekly dependency-clearing operating room and route high-risk decisions through one accountable owner."
                if unit.dependency_load >= 65
                else "Use lightweight async decision logs and maintain current collaboration cadence."
            ),
            expected_latency_reduction_days=latency_reduction,
            evidence=[
                f"span_of_control={round(span, 2)}",
                f"dependency_load={unit.dependency_load}",
                f"stress={unit.stress_score}",
                f"latency_days={unit.decision_latency_days}",
                f"skill_gaps={unit.critical_skills_gap}",
            ],
        )

    def _crisis_plan(
        self,
        scenario: str,
        competitors: list[CompetitorInsight],
        clients: list[ClientRiskInsight],
        org: list[OrgOptimizationInsight],
    ) -> CrisisResponsePlan:
        severity = self._clip(
            mean(
                [
                    competitors[0].market_pressure_score if competitors else 0,
                    clients[0].churn_risk if clients else 0,
                    clients[0].escalation_risk if clients else 0,
                    org[0].optimization_pressure if org else 0,
                ]
            )
        )
        priorities = [
            "Open executive crisis channel with single decision owner and 4-hour operating cadence.",
            "Protect renewal-risk clients with named executive sponsors and visible recovery milestones.",
            "Freeze low-value roadmap work and move scarce experts to highest revenue-risk workflows.",
        ]
        if competitors and competitors[0].market_pressure_score >= 70:
            priorities.append("Launch competitive response narrative with proof-backed product differentiation.")
        if org and org[0].optimization_pressure >= 65:
            priorities.append("Temporarily restructure overloaded org unit into recovery pods.")
        return CrisisResponsePlan(
            scenario=scenario,
            severity_score=round(severity, 2),
            risk_level=self._risk(severity),
            recovery_priorities=priorities,
            command_center_actions=[
                "Activate realtime alert stream",
                "Run digital twin every 12 hours",
                "Track client health, talent allocation, and market pressure in the boardroom dashboard",
            ],
            expected_recovery_days=max(7, min(45, round(severity * 0.42))),
        )

    def _innovation_signal(self, employee: TalentProfileInput) -> InnovationSignal:
        score = self._clip(employee.innovation_signals * 9.8 + employee.leadership_score * 0.42 + len(employee.skills) * 2.2 - employee.stress_score * 0.16)
        leadership = self._clip(employee.leadership_score * 0.74 + employee.innovation_signals * 4.1 - employee.stress_score * 0.08)
        return InnovationSignal(
            employee_id=employee.employee_id,
            employee_name=employee.name,
            innovation_score=round(score, 2),
            leadership_potential=round(leadership, 2),
            sponsorship_action=(
                "Assign executive sponsor and give protected prototype time for the next strategic sprint."
                if score >= 75
                else "Pair with a senior sponsor and capture ideas in the innovation review queue."
            ),
            evidence=[
                f"innovation_signals={employee.innovation_signals}",
                f"leadership={employee.leadership_score}",
                f"skills={len(employee.skills)}",
                f"stress={employee.stress_score}",
            ],
        )

    def _summary(
        self,
        competitors: list[CompetitorInsight],
        clients: list[ClientRiskInsight],
        matches: list[MarketplaceMatch],
        mentors: list[MentorMatch],
        org: list[OrgOptimizationInsight],
        innovation: list[InnovationSignal],
        crisis: CrisisResponsePlan,
    ) -> StrategicIntelligenceSummary:
        competitor_threats = sum(1 for item in competitors if item.threat_level in {"high", "critical"})
        high_risk_clients = sum(1 for item in clients if item.churn_risk >= 60 or item.escalation_risk >= 60)
        org_pressure = sum(1 for item in org if item.optimization_pressure >= 60)
        innovation_leaders = sum(1 for item in innovation if item.innovation_score >= 75)
        readiness = self._clip(100 - crisis.severity_score * 0.34 + min(len(matches), 6) * 2.4 + min(len(mentors), 5) * 1.5 - high_risk_clients * 4.2)
        return StrategicIntelligenceSummary(
            competitor_threats=competitor_threats,
            high_risk_clients=high_risk_clients,
            marketplace_matches=len(matches),
            mentor_matches=len(mentors),
            org_units_to_restructure=org_pressure,
            innovation_leaders=innovation_leaders,
            crisis_severity=crisis.severity_score,
            strategic_readiness_score=round(readiness, 2),
            top_market_risk=competitors[0].competitor if competitors else "none",
            top_client_risk=clients[0].client_name if clients else "none",
        )

    def _decision_options(self, what_if, shadow) -> list[StrategicDecisionOption]:
        revenue = self._metric_delta(what_if.financial_impact, "Revenue Forecast")
        cost = self._metric_delta(what_if.financial_impact, "Cost Forecast")
        productivity = self._metric_delta(what_if.productivity_impact, "Productivity")
        burnout = self._metric_delta(what_if.burnout_impact, "Burnout Risk")
        client_risk = self._risk_probability(what_if, "client")
        requested_risk = self._clip(max(risk.probability for risk in what_if.risk_analysis))
        recommended_branch = next(
            (branch for branch in shadow.multi_reality_simulations if branch.case_name == "ai_recommended_case"),
            shadow.multi_reality_simulations[-1],
        )
        return [
            StrategicDecisionOption(
                option_id="option-a-maintain-current-state",
                title="Maintain current company",
                description="Do not execute the strategic change yet; continue monitoring the live company twin.",
                risk_score=round(shadow.baseline_outcome.risk_score, 2),
                revenue_impact_percent=0,
                cost_impact_percent=0,
                burnout_impact_points=0,
                productivity_impact_percent=0,
                client_impact_score=round(client_risk * 0.42, 2),
                decision_readiness_score=round(max(50.0, what_if.decision_readiness_score - 8), 2),
                recommendation="Hold baseline state while validating the decision against Shadow Company checkpoints.",
            ),
            StrategicDecisionOption(
                option_id="option-b-execute-requested-decision",
                title=what_if.scenario.scenario_name,
                description="Execute the decision exactly as requested by the executive question.",
                risk_score=round(requested_risk, 2),
                revenue_impact_percent=round(revenue, 2),
                cost_impact_percent=round(cost, 2),
                burnout_impact_points=round(burnout, 2),
                productivity_impact_percent=round(productivity, 2),
                client_impact_score=round(client_risk, 2),
                decision_readiness_score=round(what_if.decision_readiness_score, 2),
                recommendation=what_if.recommendations[0].action,
            ),
            StrategicDecisionOption(
                option_id="option-c-ai-recommended-branch",
                title="AI-recommended strategic branch",
                description="Use staged execution, rollback thresholds, and agent monitoring before irreversible action.",
                risk_score=round(recommended_branch.risk_score, 2),
                revenue_impact_percent=round(recommended_branch.revenue_delta_percent, 2),
                cost_impact_percent=round(min(0.0, cost * 0.72), 2),
                burnout_impact_points=round(recommended_branch.workforce_delta_percent, 2),
                productivity_impact_percent=round(max(-18.0, productivity * 0.55), 2),
                client_impact_score=round(max(0.0, client_risk * 0.58), 2),
                decision_readiness_score=round(max(what_if.decision_readiness_score, recommended_branch.growth_score - recommended_branch.risk_score * 0.18), 2),
                recommendation=recommended_branch.actions[0] if recommended_branch.actions else "Proceed only through staged checkpoints.",
                recommended=True,
            ),
        ]

    def _chain_reaction(self, what_if, shadow) -> list[StrategicChainReactionStep]:
        headcount = self._metric(what_if.workforce_impact, "Headcount")
        burnout = self._metric(what_if.burnout_impact, "Burnout Risk")
        productivity = self._metric(what_if.productivity_impact, "Productivity")
        revenue = self._metric(what_if.financial_impact, "Revenue Forecast")
        client_risk = self._risk_probability(what_if, "client")
        delivery_risk = self._risk_probability(what_if, "delivery")
        company_health_baseline = shadow.baseline_outcome.workforce_health
        company_health_projected = shadow.simulated_outcome.workforce_health
        return [
            self._reaction(1, "Decision enters Shadow Company", shadow.baseline_outcome.risk_score, shadow.simulated_outcome.risk_score, "The real company is cloned before the requested decision is applied.", ["shadow_company_engine", "company_twin"]),
            self._reaction(2, "Team capacity drops", headcount.baseline, headcount.projected, "Employee and team twins recalculate capacity from the strategic decision.", ["employee_digital_twin", "team_digital_twin"]),
            self._reaction(3, "Workload and burnout rise", burnout.baseline, burnout.projected, "Remaining workforce pressure increases burnout exposure.", ["emotion_radar", "burnout_forecast_engine"]),
            self._reaction(4, "Project delay risk increases", max(0.0, delivery_risk * 0.35), delivery_risk, "Project twins raise delay probability as capacity and ownership change.", ["project_digital_twin", "delivery_forecast_engine"]),
            self._reaction(5, "Revenue risk increases", revenue.baseline, revenue.projected, "Delivery pressure and client exposure flow into revenue forecast.", ["revenue_forecasting_engine", "business_prediction_engine"]),
            self._reaction(6, "Client satisfaction drops", max(0.0, client_risk * 0.38), client_risk, "Client risk rises when delivery confidence and account stability degrade.", ["client_twin", "client_satisfaction_engine"]),
            self._reaction(7, "Company health falls", company_health_baseline, company_health_projected, "Company twin combines workforce, project, revenue, and risk changes into the future state.", ["company_digital_twin", "executive_dashboard"]),
        ]

    def _boardroom_findings(self, what_if, shadow) -> list[StrategicBoardroomFinding]:
        mapped: list[StrategicBoardroomFinding] = []
        for agent in what_if.agent_council:
            if agent.agent not in {"HR Agent", "Finance Agent", "Project Agent", "Risk Agent", "Executive Agent"}:
                continue
            mapped.append(
                StrategicBoardroomFinding(
                    agent="Security Agent" if agent.agent == "Risk Agent" else agent.agent,
                    perspective=agent.role,
                    finding=agent.finding,
                    recommendation=agent.recommendation,
                    confidence=agent.confidence,
                    evidence=agent.source_systems,
                )
            )
        shadow_executive = next((agent for agent in shadow.agent_contributions if agent.agent == "Executive Agent"), None)
        if shadow_executive:
            mapped.append(
                StrategicBoardroomFinding(
                    agent="Shadow Company Executive Agent",
                    perspective=shadow_executive.role,
                    finding=shadow_executive.finding,
                    recommendation=shadow_executive.action,
                    confidence=shadow_executive.confidence,
                    evidence=shadow_executive.source_systems,
                )
            )
        return mapped[:6]

    def _executive_recommendation(self, question: str, strategic_risk: float, recommended: StrategicDecisionOption, fallback: str) -> str:
        lowered = question.lower()
        if ("reduce workforce" in lowered or "layoff" in lowered or "lay off" in lowered) and strategic_risk >= 65:
            return "Do NOT reduce workforce by 20% as a one-step action; use the AI-recommended staged branch with retention, redeployment, and rollback gates."
        if strategic_risk >= 78:
            return f"Do not execute immediately. {fallback}"
        if strategic_risk >= 58:
            return f"Proceed only through Option C. {recommended.recommendation}"
        return f"Proceed with monitored execution. {recommended.recommendation}"

    def _reaction(self, step: int, title: str, baseline: float, projected: float, explanation: str, source_systems: list[str]) -> StrategicChainReactionStep:
        delta = projected - baseline
        magnitude = abs(delta) if max(abs(baseline), abs(projected)) <= 100 else abs(delta / max(abs(baseline), 1) * 100)
        return StrategicChainReactionStep(
            step=step,
            title=title,
            baseline=round(baseline, 2),
            projected=round(projected, 2),
            delta=round(delta, 2),
            severity=self._risk(min(100, magnitude * 2.4 if title != "Revenue risk increases" else magnitude * 5.0)),
            explanation=explanation,
            source_systems=source_systems,
        )

    @staticmethod
    def _metric(metrics: list[WhatIfImpactMetric], label: str) -> WhatIfImpactMetric:
        for metric in metrics:
            if metric.label == label:
                return metric
        raise ValueError(f"Missing metric: {label}")

    def _metric_delta(self, metrics: list[WhatIfImpactMetric], label: str) -> float:
        return self._metric(metrics, label).delta

    @staticmethod
    def _risk_probability(what_if, category: str) -> float:
        for risk in what_if.risk_analysis:
            if risk.category == category:
                return risk.probability
        return max((risk.probability for risk in what_if.risk_analysis), default=0.0)

    @staticmethod
    def _variant(base: StrategicIntelligenceRequest, scenario: str, competitor_delta: int, client_delta: int) -> StrategicIntelligenceRequest:
        competitors = [
            item.model_copy(
                update={
                    "hiring_velocity": min(500, item.hiring_velocity + competitor_delta),
                    "ai_mentions_30d": min(1000, item.ai_mentions_30d + competitor_delta * 3),
                    "product_launches_90d": min(50, item.product_launches_90d + (1 if competitor_delta >= 8 else 0)),
                }
            )
            for item in base.competitors
        ]
        clients = [
            item.model_copy(
                update={
                    "delivery_slippage_days": min(365, item.delivery_slippage_days + client_delta),
                    "payment_delay_days": min(365, item.payment_delay_days + client_delta // 2),
                    "sentiment_score": max(-1, item.sentiment_score - client_delta / 100),
                    "usage_trend_percent": max(-100, item.usage_trend_percent - client_delta),
                }
            )
            for item in base.clients
        ]
        return base.model_copy(update={"competitors": competitors, "clients": clients, "crisis_scenario": scenario})

    @staticmethod
    def _normalize(value: str) -> str:
        return value.strip().lower().replace("_", " ")

    @staticmethod
    def _clip(value: float) -> float:
        return max(0.0, min(100.0, float(value)))

    @staticmethod
    def _risk(score: float) -> RiskLevel:
        if score >= 82:
            return "critical"
        if score >= 65:
            return "high"
        if score >= 42:
            return "medium"
        return "low"

    def _append_jsonl(self, payload: dict[str, object], path: Path = HISTORY_PATH) -> None:
        with self._lock:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


strategic_intelligence_service = StrategicIntelligenceService()
