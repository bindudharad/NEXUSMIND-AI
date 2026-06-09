from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

from app.core.cache import TTLResponseCache
from app.schemas.competitive_intelligence import (
    CompetitiveAssistantRequest,
    CompetitiveAssistantResponse,
    CompetitiveDashboardSummary,
    CompetitiveIntelligenceRequest,
    CompetitiveIntelligenceResponse,
    CompetitiveRiskLevel,
    CompetitiveRiskScore,
    CompetitorComparisonCard,
    CompetitorComparisonMetric,
    CompetitorProfile,
    CompetitorProfileInput,
    HiringTrendSignal,
    IndustryTrendSignal,
    MarketExpansionSignal,
    ProductLaunchSignal,
    StrategicRecommendation,
    TechnologyAdoptionSignal,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "competitive_intelligence_history.jsonl"


class CompetitiveIntelligenceService:
    model_name = "NEXUSMIND AI Competitive Intelligence System"
    assistant_model = "Competitive AI Assistant"
    source_systems = [
        "competitor_monitoring_engine",
        "market_intelligence_engine",
        "hiring_intelligence_engine",
        "technology_intelligence_engine",
        "product_launch_intelligence_engine",
        "industry_trend_analysis_engine",
        "competitive_risk_engine",
        "executive_strategy_engine",
        "competitor_comparison_engine",
        "competitive_ai_assistant",
        "competitive_intelligence_history_jsonl",
    ]

    company_baseline = {
        "hiring_growth": 34.0,
        "product_velocity": 84.0,
        "technology_adoption": 88.0,
        "innovation_rate": 86.0,
        "workforce_growth": 74.0,
        "market_reach": 72.0,
    }

    def __init__(self) -> None:
        self._cache: TTLResponseCache[CompetitiveIntelligenceResponse] = TTLResponseCache(ttl_seconds=10)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def analyze(self, payload: CompetitiveIntelligenceRequest | None = None) -> CompetitiveIntelligenceResponse:
        if payload is None:
            return self._cache.get_or_set(lambda: self._analyze_uncached(self.default_request()))
        return self._analyze_uncached(payload)

    def ask(self, payload: CompetitiveAssistantRequest) -> CompetitiveAssistantResponse:
        analysis = self.analyze(CompetitiveIntelligenceRequest(horizon_months=payload.horizon_months))
        question = payload.question.lower()
        intent = self._intent(question)
        top = analysis.risk_scores[0]
        recommendations = analysis.recommendations[:4]

        if intent == "threat":
            answer = (
                f"{top.competitor} is the highest competitive threat at {round(top.threat_score)} percent. "
                f"The primary threat is {top.primary_threat}, with market disruption risk at "
                f"{round(top.market_disruption_risk)} percent and talent acquisition risk at {round(top.talent_acquisition_risk)} percent."
            )
            cited = top.evidence
            competitors = [top.competitor]
        elif intent == "product_launches":
            launches = analysis.product_launches[:4]
            answer = "Tracked launches this quarter: " + "; ".join(
                f"{item.competitor} launched {item.launch_name} ({item.risk_level} risk)" for item in launches
            )
            cited = [evidence for item in launches for evidence in item.evidence[:2]]
            competitors = list(dict.fromkeys(item.competitor for item in launches))
        elif intent == "technology":
            tech = analysis.technology_adoption[:4]
            answer = "Competitors are adopting " + "; ".join(
                f"{item.competitor}: {', '.join(item.technologies[:4])} at {round(item.adoption_score)} adoption score"
                for item in tech
            )
            cited = [item.strategic_insight for item in tech]
            competitors = [item.competitor for item in tech]
        elif intent == "hiring":
            hiring = analysis.hiring_trends[:4]
            answer = "Aggressive hiring signals: " + "; ".join(
                f"{item.competitor} is up {round(item.hiring_growth_percent)} percent with focus on {item.focus}"
                for item in hiring
            )
            cited = [item.strategic_interpretation for item in hiring]
            competitors = [item.competitor for item in hiring]
        elif intent == "market_expansion":
            expansion = analysis.market_expansions[:4]
            answer = "Market expansion pressure: " + "; ".join(
                f"{item.competitor} is expanding into {', '.join(item.regions[:3])} ({item.potential_market_threat} threat)"
                for item in expansion
            )
            cited = [item.strategic_interpretation for item in expansion]
            competitors = [item.competitor for item in expansion]
        elif intent == "comparison":
            comparison = analysis.comparison[:3]
            answer = "Comparative scorecards: " + "; ".join(
                f"{item.competitor} overall score {round(item.overall_score)} with rank {item.rank}" for item in comparison
            )
            cited = [metric.interpretation for item in comparison for metric in item.metrics[:2]]
            competitors = [item.competitor for item in comparison]
        else:
            answer = (
                f"Recommended strategy: {recommendations[0].action} "
                f"Reason: {recommendations[0].reason} Current top threat is {top.competitor}."
            )
            cited = [recommendations[0].reason, *top.evidence[:3]]
            competitors = [top.competitor, *recommendations[0].related_competitors]

        return CompetitiveAssistantResponse(
            model=self.assistant_model,
            generated_at=datetime.now(timezone.utc),
            question=payload.question,
            intent=intent,
            answer=answer,
            confidence=max(0.78, min(0.96, analysis.summary.strategic_readiness_score / 100)),
            cited_evidence=list(dict.fromkeys(cited))[:8],
            competitors=list(dict.fromkeys(competitors))[:6],
            recommendations=recommendations,
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )

    async def stream(self):
        scenarios = [
            self.default_request(),
            self._variant(self.default_request(), "ai-hiring-surge"),
            self._variant(self.default_request(), "market-expansion-pressure"),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: competitive_intelligence\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def _analyze_uncached(self, payload: CompetitiveIntelligenceRequest) -> CompetitiveIntelligenceResponse:
        request = payload if payload.competitors else payload.model_copy(update={"competitors": self.default_request().competitors})
        risk_scores = sorted([self._risk_score(profile) for profile in request.competitors], key=lambda item: item.threat_score, reverse=True)
        risk_by_name = {item.competitor: item for item in risk_scores}
        ranked_inputs = sorted(request.competitors, key=lambda item: risk_by_name[item.company_name].threat_score, reverse=True)
        profiles = [
            self._profile(profile, risk_by_name[profile.company_name], rank)
            for rank, profile in enumerate(ranked_inputs, start=1)
        ]
        product_launches = sorted(
            [launch for profile in ranked_inputs for launch in self._product_launches(profile, risk_by_name[profile.company_name])],
            key=lambda item: (self._risk_rank(item.risk_level), item.launch_frequency_score),
            reverse=True,
        )
        hiring_trends = sorted(
            [self._hiring_trend(profile) for profile in ranked_inputs],
            key=lambda item: item.hiring_growth_percent,
            reverse=True,
        )
        technology = sorted(
            [self._technology_adoption(profile) for profile in ranked_inputs],
            key=lambda item: item.adoption_score,
            reverse=True,
        )
        expansion = sorted(
            [self._market_expansion(profile) for profile in ranked_inputs],
            key=lambda item: item.expansion_score,
            reverse=True,
        )
        trends = self._industry_trends(request.competitors)
        comparison = [self._comparison_card(profile, rank) for rank, profile in enumerate(ranked_inputs, start=1)]
        recommendations = self._recommendations(risk_scores, hiring_trends, technology, product_launches, expansion, trends)
        summary = self._summary(risk_scores, product_launches, hiring_trends, technology, expansion, recommendations)
        response = CompetitiveIntelligenceResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            horizon_months=request.horizon_months,
            summary=summary,
            profiles=profiles,
            product_launches=product_launches,
            hiring_trends=hiring_trends,
            technology_adoption=technology,
            market_expansions=expansion,
            risk_scores=risk_scores,
            industry_trends=trends,
            comparison=comparison,
            recommendations=recommendations,
            supported_questions=[
                "Show biggest competitor threat.",
                "What products did competitors launch this quarter?",
                "Which technologies are competitors adopting?",
                "Who is hiring aggressively?",
                "Which markets are competitors entering?",
                "Compare us against top competitors.",
                "What strategic actions should we take?",
            ],
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    @staticmethod
    def default_request() -> CompetitiveIntelligenceRequest:
        return CompetitiveIntelligenceRequest(
            horizon_months=12,
            focus_markets=["India", "Singapore", "UAE", "United States"],
            competitors=[
                CompetitorProfileInput(
                    company_name="HelixOps AI",
                    industry="Enterprise AI Operations",
                    products=["AI Workflow Automator", "Security Copilot", "Workforce Command Graph"],
                    market_position="AI-native challenger",
                    revenue_estimate_millions=186,
                    employee_count=780,
                    technology_stack=["Kubernetes", "Generative AI", "Multi-Agent Systems", "Qdrant", "Neo4j", "Kafka"],
                    regions=["India", "Singapore", "UAE"],
                    job_roles=["AI Engineer", "MLOps Engineer", "Security Analyst", "Enterprise Sales"],
                    hiring_growth_percent=45,
                    product_launches_90d=4,
                    ai_mentions_30d=128,
                    funding_signal=0.82,
                    partnership_signal=0.62,
                    pricing_pressure=0.58,
                    customer_sentiment=0.64,
                    market_share_growth=11,
                    technology_adoption_score=92,
                    product_velocity_score=89,
                    recent_activities=[
                        "Released AI Workflow Automator for enterprise operations teams",
                        "Opened Singapore and UAE sales pods",
                        "Published agentic SOC partnership announcement",
                    ],
                ),
                CompetitorProfileInput(
                    company_name="WorkGraph Systems",
                    industry="Workforce Analytics",
                    products=["Team Graph Analytics", "Org Design Studio", "Talent Marketplace"],
                    market_position="analytics suite incumbent",
                    revenue_estimate_millions=142,
                    employee_count=640,
                    technology_stack=["Graph AI", "Snowflake", "Python", "Vector Search", "React"],
                    regions=["United States", "Canada", "United Kingdom"],
                    job_roles=["Data Scientist", "Graph Engineer", "People Analytics Consultant"],
                    hiring_growth_percent=28,
                    product_launches_90d=2,
                    ai_mentions_30d=74,
                    funding_signal=0.36,
                    partnership_signal=0.42,
                    pricing_pressure=0.37,
                    customer_sentiment=0.36,
                    market_share_growth=6,
                    technology_adoption_score=78,
                    product_velocity_score=74,
                    recent_activities=[
                        "Added relationship-graph scoring to team analytics product",
                        "Expanded people analytics consulting in North America",
                    ],
                ),
                CompetitorProfileInput(
                    company_name="Orion PeopleCloud",
                    industry="HR Cloud Platform",
                    products=["PeopleCloud Core", "Engagement Pulse", "Compensation Planner"],
                    market_position="enterprise HR incumbent",
                    revenue_estimate_millions=760,
                    employee_count=3600,
                    technology_stack=["AWS", "PostgreSQL", "Machine Learning", "Data Warehouse"],
                    regions=["United States", "Germany", "India"],
                    job_roles=["Enterprise Account Executive", "Compensation Analyst", "ML Product Manager"],
                    hiring_growth_percent=18,
                    product_launches_90d=1,
                    ai_mentions_30d=48,
                    funding_signal=0.08,
                    partnership_signal=0.35,
                    pricing_pressure=0.72,
                    customer_sentiment=0.12,
                    market_share_growth=3,
                    technology_adoption_score=61,
                    product_velocity_score=55,
                    recent_activities=[
                        "Bundled AI engagement summaries into core HR suite",
                        "Introduced price incentives for multi-year enterprise renewals",
                    ],
                ),
                CompetitorProfileInput(
                    company_name="Apex Strategy Labs",
                    industry="Market Intelligence Software",
                    products=["Strategy Radar", "Market Expansion Model", "Pricing Intelligence"],
                    market_position="strategy analytics specialist",
                    revenue_estimate_millions=96,
                    employee_count=410,
                    technology_stack=["Generative AI", "Spark", "Kafka", "Market Graphs", "Python"],
                    regions=["Singapore", "Japan", "Australia"],
                    job_roles=["Market Analyst", "AI Research Engineer", "Pricing Strategist"],
                    hiring_growth_percent=34,
                    product_launches_90d=3,
                    ai_mentions_30d=92,
                    funding_signal=0.55,
                    acquisition_signal=0.24,
                    partnership_signal=0.5,
                    pricing_pressure=0.41,
                    customer_sentiment=0.46,
                    market_share_growth=8,
                    technology_adoption_score=84,
                    product_velocity_score=81,
                    recent_activities=[
                        "Released market-expansion simulation module",
                        "Hired AI research team for pricing intelligence",
                        "Signed APAC channel partnership",
                    ],
                ),
            ],
        )

    def _risk_score(self, profile: CompetitorProfileInput) -> CompetitiveRiskScore:
        product_pressure = self._clip(profile.product_launches_90d * 16 + profile.product_velocity_score * 0.42 + profile.ai_mentions_30d * 0.08)
        hiring_pressure = self._clip(max(profile.hiring_growth_percent, 0) * 1.35 + len(profile.job_roles) * 4.5)
        tech_pressure = self._clip(profile.technology_adoption_score + self._ai_tech_count(profile.technology_stack) * 2.5)
        expansion_pressure = self._clip(len(profile.regions) * 14 + max(profile.market_share_growth, 0) * 2.4 + profile.partnership_signal * 16)
        capital_pressure = self._clip(profile.funding_signal * 76 + profile.acquisition_signal * 34)
        sentiment_pressure = self._clip(max(profile.customer_sentiment, 0) * 44 + profile.pricing_pressure * 28)
        threat = self._clip(
            product_pressure * 0.25
            + hiring_pressure * 0.18
            + tech_pressure * 0.2
            + expansion_pressure * 0.15
            + capital_pressure * 0.1
            + sentiment_pressure * 0.07
            + max(profile.market_share_growth, 0) * 0.5
        )
        primary = self._primary_threat(
            {
                "product launch velocity": product_pressure,
                "aggressive hiring": hiring_pressure,
                "technology adoption": tech_pressure,
                "market expansion": expansion_pressure,
                "funding and acquisition activity": capital_pressure,
            }
        )
        return CompetitiveRiskScore(
            competitor=profile.company_name,
            threat_score=round(threat, 2),
            threat_level=self._risk(threat),
            market_disruption_risk=round(self._clip(product_pressure * 0.46 + expansion_pressure * 0.36 + sentiment_pressure * 0.18), 2),
            innovation_risk=round(self._clip(product_pressure * 0.5 + tech_pressure * 0.38 + profile.ai_mentions_30d * 0.08), 2),
            talent_acquisition_risk=round(hiring_pressure, 2),
            technology_risk=round(tech_pressure, 2),
            primary_threat=primary,
            evidence=[
                f"launches_90d={profile.product_launches_90d}",
                f"hiring_growth={round(profile.hiring_growth_percent)}%",
                f"tech_adoption={round(profile.technology_adoption_score)}",
                f"market_share_growth={round(profile.market_share_growth, 1)}%",
                f"ai_mentions_30d={profile.ai_mentions_30d}",
            ],
        )

    def _profile(self, profile: CompetitorProfileInput, risk: CompetitiveRiskScore, rank: int) -> CompetitorProfile:
        strategic_risks = [
            risk.primary_threat,
            f"{round(risk.talent_acquisition_risk)}% talent acquisition pressure",
            f"{round(risk.technology_risk)}% technology-adoption pressure",
        ]
        if profile.pricing_pressure >= 0.55:
            strategic_risks.append("pricing pressure against enterprise renewals")
        if profile.regions:
            strategic_risks.append(f"regional expansion into {', '.join(profile.regions[:3])}")
        source_signals = ["product_launch", "hiring_trend", "technology_adoption", "market_expansion", "customer_sentiment"]
        if profile.funding_signal >= 0.45:
            source_signals.append("funding_activity")
        if profile.partnership_signal >= 0.45:
            source_signals.append("partnership")
        if profile.pricing_pressure >= 0.55:
            source_signals.append("pricing_change")
        return CompetitorProfile(
            competitor_id=self._slug(profile.company_name),
            company_name=profile.company_name,
            industry=profile.industry,
            products=profile.products,
            market_position=profile.market_position,
            revenue_estimate_millions=profile.revenue_estimate_millions,
            employee_count=profile.employee_count,
            technology_stack=profile.technology_stack,
            recent_activities=profile.recent_activities or self._fallback_activities(profile),
            strategic_risks=strategic_risks,
            rank=rank,
            threat_score=risk.threat_score,
            threat_level=risk.threat_level,
            source_signals=source_signals,
        )

    def _product_launches(self, profile: CompetitorProfileInput, risk: CompetitiveRiskScore) -> list[ProductLaunchSignal]:
        if profile.product_launches_90d <= 0:
            return []
        launches = []
        products = profile.products or [f"{profile.company_name} AI Platform"]
        categories = ["AI Platform", "Workflow Automation", "Security Intelligence", "Analytics Expansion"]
        for index in range(min(profile.product_launches_90d, 4)):
            product = products[index % len(products)]
            score = self._clip(profile.product_velocity_score * 0.58 + profile.ai_mentions_30d * 0.12 + profile.product_launches_90d * 7 + index * 3)
            launches.append(
                ProductLaunchSignal(
                    competitor=profile.company_name,
                    launch_name=f"{product} {['Release', 'Expansion', 'Copilot', 'Enterprise Edition'][index % 4]}",
                    category=categories[index % len(categories)],
                    release_window=f"last {30 + index * 15} days",
                    launch_frequency_score=round(score, 2),
                    product_strategy_shift=(
                        "Accelerating AI-native workflow coverage and board-level operating intelligence."
                        if "AI" in product.upper() or profile.technology_adoption_score >= 82
                        else "Expanding suite coverage to defend enterprise accounts."
                    ),
                    impact=(
                        "Potential threat to current analytics and operating-system differentiation."
                        if risk.threat_score >= 68
                        else "Monitor for account-level positioning overlap."
                    ),
                    risk_level=self._risk(score),
                    evidence=[
                        f"product_velocity={round(profile.product_velocity_score)}",
                        f"launch_count_90d={profile.product_launches_90d}",
                        f"ai_mentions_30d={profile.ai_mentions_30d}",
                    ],
                )
            )
        return launches

    def _hiring_trend(self, profile: CompetitorProfileInput) -> HiringTrendSignal:
        roles = profile.job_roles or ["AI Product Manager", "Enterprise Engineer"]
        skills = sorted(set(profile.technology_stack[:5] + [role.split()[0] for role in roles]))[:8]
        departments = self._departments_from_roles(roles)
        level = self._risk(self._clip(max(profile.hiring_growth_percent, 0) * 1.4 + len(roles) * 5))
        focus = ", ".join(roles[:2])
        return HiringTrendSignal(
            competitor=profile.company_name,
            hiring_growth_percent=round(profile.hiring_growth_percent, 2),
            focus=focus,
            roles=roles,
            departments_expanding=departments,
            geographic_hiring=profile.regions,
            skill_demand=skills,
            forecast=(
                f"Headcount pressure may expand by {round(max(profile.hiring_growth_percent, 0) * 0.45 + len(profile.regions) * 3, 1)}% over the next planning window."
            ),
            strategic_interpretation=(
                "Expansion of AI product line and enterprise go-to-market capacity."
                if profile.hiring_growth_percent >= 30
                else "Selective capability buildout, likely focused on retention and account defense."
            ),
            risk_level=level,
        )

    def _technology_adoption(self, profile: CompetitorProfileInput) -> TechnologyAdoptionSignal:
        tech_count = self._ai_tech_count(profile.technology_stack)
        investment = self._clip(profile.technology_adoption_score * 0.68 + tech_count * 8 + profile.funding_signal * 18)
        return TechnologyAdoptionSignal(
            competitor=profile.company_name,
            technologies=profile.technology_stack,
            adoption_score=round(self._clip(profile.technology_adoption_score + tech_count * 2), 2),
            investment_signal=round(investment, 2),
            strategic_insight=(
                f"{profile.company_name} is moving toward AI-native operations with {', '.join(profile.technology_stack[:4])}."
                if profile.technology_adoption_score >= 75
                else f"{profile.company_name} is modernizing selectively, but adoption velocity remains manageable."
            ),
            risk_level=self._risk(investment),
        )

    def _market_expansion(self, profile: CompetitorProfileInput) -> MarketExpansionSignal:
        score = self._clip(len(profile.regions) * 15 + max(profile.market_share_growth, 0) * 2.2 + profile.partnership_signal * 22 + profile.customer_sentiment * 18)
        return MarketExpansionSignal(
            competitor=profile.company_name,
            regions=profile.regions,
            expansion_score=round(score, 2),
            customer_acquisition_signal=round(self._clip(profile.customer_sentiment * 42 + profile.market_share_growth * 3 + profile.pricing_pressure * 18), 2),
            potential_market_threat=self._risk(score),
            strategic_interpretation=(
                f"{profile.company_name} can pressure enterprise accounts in {', '.join(profile.regions[:3])}."
                if profile.regions
                else f"{profile.company_name} has no material regional expansion signal."
            ),
        )

    def _industry_trends(self, competitors: list[CompetitorProfileInput]) -> list[IndustryTrendSignal]:
        all_tech = [tech.lower() for profile in competitors for tech in profile.technology_stack]
        all_products = " ".join(product.lower() for profile in competitors for product in profile.products)
        avg_hiring = mean([max(profile.hiring_growth_percent, 0) for profile in competitors]) if competitors else 0
        avg_ai_mentions = mean([profile.ai_mentions_30d for profile in competitors]) if competitors else 0
        trends = [
            (
                "Agentic workflow automation",
                self._clip(avg_ai_mentions * 0.32 + all_products.count("workflow") * 12 + all_tech.count("multi-agent systems") * 18),
                "AI agents are becoming the operating interface for cross-functional enterprise work.",
                "6-12 months",
                "Ship differentiated workflow automation tied to real workforce data.",
                "Competitors may commoditize basic analytics dashboards.",
            ),
            (
                "AI security operations convergence",
                self._clip(all_products.count("security") * 18 + all_tech.count("kafka") * 8 + all_tech.count("neo4j") * 8 + avg_ai_mentions * 0.14),
                "Security, anomaly detection, and workforce monitoring are converging into one executive risk layer.",
                "3-9 months",
                "Bundle security intelligence into the AI operating-system narrative.",
                "Security-focused rivals can sell urgency into executive accounts.",
            ),
            (
                "Vector and graph knowledge systems",
                self._clip(all_tech.count("qdrant") * 16 + all_tech.count("neo4j") * 16 + all_tech.count("vector search") * 12 + avg_ai_mentions * 0.1),
                "Enterprise memory, retrieval, and graph evidence are becoming standard buying criteria.",
                "6-18 months",
                "Use Company Brain and knowledge-loss prevention as a board-level differentiator.",
                "RAG-only competitors may claim parity unless graph evidence is visible.",
            ),
            (
                "AI talent arms race",
                self._clip(avg_hiring * 1.35 + sum(1 for profile in competitors if profile.hiring_growth_percent >= 30) * 9),
                "Competitors are using hiring velocity as a proxy for near-term AI roadmap acceleration.",
                "current quarter",
                "Prioritize senior AI, MLOps, and enterprise strategy hires.",
                "Talent scarcity can slow roadmap execution and sales proof points.",
            ),
        ]
        return [
            IndustryTrendSignal(
                trend=name,
                traction_score=round(score, 2),
                forecast_impact=impact,
                likely_time_horizon=horizon,
                opportunity=opportunity,
                risk=risk,
            )
            for name, score, impact, horizon, opportunity, risk in sorted(trends, key=lambda item: item[1], reverse=True)
        ]

    def _comparison_card(self, profile: CompetitorProfileInput, rank: int) -> CompetitorComparisonCard:
        metrics = [
            self._comparison_metric("hiring_growth", profile),
            self._comparison_metric("product_velocity", profile),
            self._comparison_metric("technology_adoption", profile),
            self._comparison_metric("innovation_rate", profile),
            self._comparison_metric("workforce_growth", profile),
            self._comparison_metric("market_reach", profile),
        ]
        overall = mean([metric.competitor_score for metric in metrics])
        return CompetitorComparisonCard(
            competitor=profile.company_name,
            rank=rank,
            overall_score=round(overall, 2),
            metrics=metrics,
        )

    def _recommendations(
        self,
        risk_scores: list[CompetitiveRiskScore],
        hiring: list[HiringTrendSignal],
        technology: list[TechnologyAdoptionSignal],
        launches: list[ProductLaunchSignal],
        expansion: list[MarketExpansionSignal],
        trends: list[IndustryTrendSignal],
    ) -> list[StrategicRecommendation]:
        top = risk_scores[0]
        top_hiring = hiring[0]
        top_tech = technology[0]
        top_expansion = expansion[0]
        top_launch = launches[0] if launches else None
        recommendations = [
            StrategicRecommendation(
                title="Accelerate AI operating-system roadmap",
                priority=top.threat_level,
                action=f"Create a 30-day response sprint against {top.competitor}'s {top.primary_threat}.",
                reason=f"{top.competitor} has {round(top.threat_score)}% competitive threat with evidence: {', '.join(top.evidence[:3])}.",
                expected_competitive_benefit="Protect strategic accounts and improve product-velocity narrative before next buyer cycle.",
                confidence=0.91,
                related_competitors=[top.competitor],
            ),
            StrategicRecommendation(
                title="Increase AI hiring priority",
                priority=top_hiring.risk_level,
                action=f"Prioritize senior AI, MLOps, and enterprise strategy hiring because {top_hiring.competitor} hiring is up {round(top_hiring.hiring_growth_percent)}%.",
                reason=top_hiring.strategic_interpretation,
                expected_competitive_benefit="Reduce talent acquisition risk and defend roadmap execution speed.",
                confidence=0.88,
                related_competitors=[top_hiring.competitor],
            ),
            StrategicRecommendation(
                title="Invest in visible technology proof points",
                priority=top_tech.risk_level,
                action=f"Show production proof for {', '.join(top_tech.technologies[:3])} in executive demos.",
                reason=top_tech.strategic_insight,
                expected_competitive_benefit="Make technology adoption defensible instead of a claims-based comparison.",
                confidence=0.86,
                related_competitors=[top_tech.competitor],
            ),
            StrategicRecommendation(
                title="Defend expansion markets",
                priority=top_expansion.potential_market_threat,
                action=f"Launch account-defense and partner strategy in {', '.join(top_expansion.regions[:3])}.",
                reason=top_expansion.strategic_interpretation,
                expected_competitive_benefit="Reduce market-entry disruption and protect enterprise pipeline.",
                confidence=0.84,
                related_competitors=[top_expansion.competitor],
            ),
        ]
        if top_launch:
            recommendations.append(
                StrategicRecommendation(
                    title="Counter product launch narrative",
                    priority=top_launch.risk_level,
                    action=f"Publish proof-backed differentiation against {top_launch.competitor}'s {top_launch.launch_name}.",
                    reason=top_launch.impact,
                    expected_competitive_benefit="Improve win-rate against launch-driven sales pressure.",
                    confidence=0.83,
                    related_competitors=[top_launch.competitor],
                )
            )
        if trends:
            recommendations.append(
                StrategicRecommendation(
                    title=f"Exploit trend: {trends[0].trend}",
                    priority=self._risk(trends[0].traction_score),
                    action=trends[0].opportunity,
                    reason=trends[0].forecast_impact,
                    expected_competitive_benefit="Turn external market movement into a product and sales priority.",
                    confidence=0.82,
                    related_competitors=[item.competitor for item in risk_scores[:3]],
                )
            )
        return recommendations

    def _summary(
        self,
        risks: list[CompetitiveRiskScore],
        launches: list[ProductLaunchSignal],
        hiring: list[HiringTrendSignal],
        technology: list[TechnologyAdoptionSignal],
        expansion: list[MarketExpansionSignal],
        recommendations: list[StrategicRecommendation],
    ) -> CompetitiveDashboardSummary:
        avg_threat = mean([item.threat_score for item in risks]) if risks else 0
        high_threats = sum(1 for item in risks if item.threat_level in {"high", "critical"})
        readiness = self._clip(100 - avg_threat * 0.36 + min(len(recommendations), 6) * 2.8 - high_threats * 2)
        return CompetitiveDashboardSummary(
            competitor_count=len(risks),
            high_threat_competitors=high_threats,
            top_competitor_threat=risks[0].competitor if risks else "none",
            average_threat_score=round(avg_threat, 2),
            product_launches_tracked=len(launches),
            aggressive_hiring_competitors=sum(1 for item in hiring if item.hiring_growth_percent >= 30),
            technologies_tracked=len({tech for item in technology for tech in item.technologies}),
            markets_expanding=sum(1 for item in expansion if item.expansion_score >= 45),
            strategic_readiness_score=round(readiness, 2),
        )

    def _comparison_metric(self, metric: str, profile: CompetitorProfileInput) -> CompetitorComparisonMetric:
        competitor_score = {
            "hiring_growth": self._clip(max(profile.hiring_growth_percent, 0) * 1.45 + len(profile.job_roles) * 3),
            "product_velocity": self._clip(profile.product_velocity_score * 0.78 + profile.product_launches_90d * 5),
            "technology_adoption": self._clip(profile.technology_adoption_score + self._ai_tech_count(profile.technology_stack) * 2),
            "innovation_rate": self._clip(profile.product_velocity_score * 0.5 + profile.ai_mentions_30d * 0.22 + profile.funding_signal * 14),
            "workforce_growth": self._clip(max(profile.hiring_growth_percent, 0) * 1.1 + min(profile.employee_count / 80, 22)),
            "market_reach": self._clip(len(profile.regions) * 16 + profile.market_share_growth * 2.1 + profile.partnership_signal * 18),
        }[metric]
        company_score = self.company_baseline[metric]
        delta = round(company_score - competitor_score, 2)
        label = metric.replace("_", " ")
        return CompetitorComparisonMetric(
            metric=metric,
            company_score=round(company_score, 2),
            competitor_score=round(competitor_score, 2),
            delta=delta,
            interpretation=(
                f"NEXUSMIND leads {profile.company_name} on {label} by {abs(delta):.1f} points."
                if delta >= 0
                else f"{profile.company_name} leads NEXUSMIND on {label} by {abs(delta):.1f} points."
            ),
        )

    @staticmethod
    def _departments_from_roles(roles: list[str]) -> list[str]:
        departments = []
        joined = " ".join(roles).lower()
        if any(token in joined for token in ["engineer", "mlops", "research"]):
            departments.append("AI Engineering")
        if any(token in joined for token in ["sales", "account"]):
            departments.append("Go-to-Market")
        if any(token in joined for token in ["analyst", "strategy", "pricing"]):
            departments.append("Strategy")
        if any(token in joined for token in ["security", "soc"]):
            departments.append("Security")
        return departments or ["Product"]

    @staticmethod
    def _fallback_activities(profile: CompetitorProfileInput) -> list[str]:
        return [
            f"Tracked {profile.product_launches_90d} product launch signals in 90 days",
            f"Hiring growth signal at {round(profile.hiring_growth_percent)}%",
            f"Technology adoption score at {round(profile.technology_adoption_score)}",
        ]

    @staticmethod
    def _intent(question: str) -> str:
        if any(token in question for token in ["biggest", "threat", "risk", "danger"]):
            return "threat"
        if any(token in question for token in ["launch", "product", "release"]):
            return "product_launches"
        if any(token in question for token in ["technology", "tech", "adopting", "stack", "framework"]):
            return "technology"
        if any(token in question for token in ["hiring", "hire", "roles", "talent"]):
            return "hiring"
        if any(token in question for token in ["market", "region", "expansion", "entering"]):
            return "market_expansion"
        if any(token in question for token in ["compare", "scorecard", "versus", "vs"]):
            return "comparison"
        return "strategy"

    @staticmethod
    def _ai_tech_count(technologies: list[str]) -> int:
        tokens = " ".join(technologies).lower()
        return sum(1 for keyword in ["ai", "agent", "graph", "vector", "qdrant", "neo4j", "kafka", "spark", "ml"] if keyword in tokens)

    @staticmethod
    def _primary_threat(scores: dict[str, float]) -> str:
        return max(scores.items(), key=lambda item: item[1])[0]

    @staticmethod
    def _risk(score: float) -> CompetitiveRiskLevel:
        if score >= 82:
            return "critical"
        if score >= 65:
            return "high"
        if score >= 42:
            return "medium"
        return "low"

    @staticmethod
    def _risk_rank(level: CompetitiveRiskLevel) -> int:
        return {"low": 1, "medium": 2, "high": 3, "critical": 4}[level]

    @staticmethod
    def _slug(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

    @staticmethod
    def _clip(value: float) -> float:
        return max(0.0, min(100.0, float(value)))

    @staticmethod
    def _variant(base: CompetitiveIntelligenceRequest, scenario: str) -> CompetitiveIntelligenceRequest:
        if scenario == "ai-hiring-surge":
            competitors = [
                profile.model_copy(
                    update={
                        "hiring_growth_percent": min(300, profile.hiring_growth_percent + (18 if index == 0 else 9)),
                        "ai_mentions_30d": min(5000, profile.ai_mentions_30d + 34),
                        "product_launches_90d": min(80, profile.product_launches_90d + (1 if index < 2 else 0)),
                        "technology_adoption_score": min(100, profile.technology_adoption_score + 5),
                    }
                )
                for index, profile in enumerate(base.competitors)
            ]
            return base.model_copy(update={"competitors": competitors})
        competitors = [
            profile.model_copy(
                update={
                    "regions": list(dict.fromkeys([*profile.regions, "India", "Singapore", "UAE"])),
                    "market_share_growth": min(80, profile.market_share_growth + 5),
                    "partnership_signal": min(1, profile.partnership_signal + 0.16),
                }
            )
            for profile in base.competitors
        ]
        return base.model_copy(update={"competitors": competitors})

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


competitive_intelligence_service = CompetitiveIntelligenceService()
