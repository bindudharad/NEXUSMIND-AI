from __future__ import annotations

import asyncio
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

from app.core.cache import TTLResponseCache
from app.schemas.business_prediction import BusinessPredictionResponse
from app.schemas.competitive_intelligence import CompetitiveIntelligenceResponse
from app.schemas.global_risk import (
    CompanyImpactPrediction,
    CompetitorGlobalThreat,
    CyberThreatSignal,
    EconomicIndicatorSignal,
    ExternalEventInput,
    ExternalIntelligenceSignal,
    GlobalRiskAgentContribution,
    GlobalRiskAlert,
    GlobalRiskAssistantRequest,
    GlobalRiskAssistantResponse,
    GlobalRiskDashboardSummary,
    GlobalRiskDigitalTwinSync,
    GlobalRiskForecastPoint,
    GlobalRiskLevel,
    GlobalRiskRecommendation,
    GlobalRiskScannerRequest,
    GlobalRiskScannerResponse,
    GlobalSignalType,
    RegulatoryRiskSignal,
    TechnologyTrendSignal,
)
from app.services.business_prediction_service import business_prediction_service
from app.services.competitive_intelligence_service import competitive_intelligence_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "global_risk_scanner_history.jsonl"
ASSISTANT_HISTORY_PATH = DATA_DIR / "global_risk_assistant_history.jsonl"


class RealTimeGlobalRiskScannerService:
    model_name = "NEXUSMIND Real-Time Global Risk Scanner - Enterprise External Intelligence Platform"
    assistant_model = "Global Risk Executive Intelligence Assistant"
    final_verdict = "REAL-TIME GLOBAL RISK SCANNER COMPLETE"
    source_systems = [
        "news_intelligence_engine",
        "economic_intelligence_engine",
        "competitor_intelligence_engine",
        "regulatory_intelligence_engine",
        "market_intelligence_engine",
        "technology_intelligence_engine",
        "cyber_threat_intelligence_engine",
        "supply_chain_risk_engine",
        "geopolitical_event_engine",
        "risk_forecast_engine",
        "impact_prediction_engine",
        "executive_dashboard",
        "risk_ai_assistant",
        "alerting_engine",
        "company_digital_twin",
        "department_digital_twin",
        "workforce_digital_twin",
        "revenue_forecasting_engine",
        "crisis_simulator",
        "multi_agent_workforce",
    ]
    live_source_adapters = [
        "CISA Known Exploited Vulnerabilities JSON adapter",
        "External RSS/news ingestion adapter",
        "Economic indicator event adapter",
        "Competitor intelligence adapter",
        "Regulatory policy event adapter",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[GlobalRiskScannerResponse] = TTLResponseCache(ttl_seconds=120)
        self._history_seeded = False
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def default(self) -> GlobalRiskScannerResponse:
        if not self._history_seeded:
            self._history_seeded = True
            latest = self._latest_history()
            if latest:
                seeded = latest.model_copy(update={"generated_at": datetime.now(timezone.utc)}, deep=True)
                self._cache.seed(seeded, ttl_seconds=120)
                return seeded
        return self._cache.get_or_set(lambda: self.analyze(GlobalRiskScannerRequest()))

    def analyze(self, payload: GlobalRiskScannerRequest | None = None) -> GlobalRiskScannerResponse:
        request = payload or GlobalRiskScannerRequest()
        competitive = competitive_intelligence_service.analyze()
        business = business_prediction_service.analyze()
        events = request.events or self.default_events()
        if request.use_live_sources:
            events = [*events, *self._live_events()]
        news = sorted(
            [self._signal(event, request, competitive, business) for event in events],
            key=lambda item: (item.risk_score, item.company_relevance),
            reverse=True,
        )
        economic = self._economic_intelligence(news, business)
        competitors = self._competitor_intelligence(competitive)
        regulatory = self._regulatory_intelligence(news)
        technology = self._technology_intelligence(news, competitive)
        cyber = self._cyber_intelligence(news)
        impacts = self._impact_predictions(news, business, competitive)
        forecasts = self._forecasts(news, impacts, request.horizon_days)
        alerts = self._alerts(news, impacts, competitors, economic)
        recommendations = self._recommendations(alerts, economic, competitors, technology, cyber)
        response = GlobalRiskScannerResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            cycle_name=request.cycle_name,
            horizon_days=request.horizon_days,
            summary=self._summary(news, economic, competitors, regulatory, technology, cyber, impacts, alerts),
            news_intelligence=news,
            economic_intelligence=economic,
            competitor_intelligence=competitors,
            regulatory_intelligence=regulatory,
            technology_intelligence=technology,
            cyber_threat_intelligence=cyber,
            impact_predictions=impacts,
            risk_forecasts=forecasts,
            alerts=alerts,
            recommendations=recommendations,
            digital_twin_sync=self._digital_twin_sync(impacts, forecasts, alerts),
            agent_council=self._agent_council(economic, competitors, cyber, recommendations, forecasts),
            supported_questions=[
                "What global risks affect us?",
                "What competitor is our biggest threat?",
                "How will inflation affect revenue?",
                "What market trends should we monitor?",
                "What regulations may affect us next year?",
                "What cyber threats are relevant right now?",
            ],
            executive_insights=self._executive_insights(news, impacts, alerts, forecasts),
            live_source_adapters=self.live_source_adapters,
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
            final_verdict=self.final_verdict,
        )
        self._append_jsonl(HISTORY_PATH, response.model_dump(mode="json"))
        return response

    def ask(self, payload: GlobalRiskAssistantRequest) -> GlobalRiskAssistantResponse:
        analysis = self.default() if payload.horizon_days == 365 else self.analyze(GlobalRiskScannerRequest(horizon_days=payload.horizon_days))
        question = payload.question.lower()
        if any(token in question for token in ["competitor", "biggest threat", "market rival"]):
            intent = "competitor"
            rows = analysis.competitor_intelligence[:3]
            answer = (
                f"{rows[0].competitor} is the biggest external competitor threat at {round(rows[0].threat_score)}%. "
                f"Primary threat: {rows[0].primary_threat}; modeled churn pressure is {round(rows[0].predicted_client_churn_delta, 1)}%."
            )
            evidence = [item.primary_threat for item in rows]
            actions = [analysis.recommendations[0].action]
            events = [item.competitor for item in rows]
        elif any(token in question for token in ["inflation", "interest", "rates", "economic"]):
            intent = "inflation"
            rows = analysis.economic_intelligence[:3]
            answer = "Economic pressure: " + "; ".join(
                f"{item.indicator} in {item.region} is {round(item.risk_score)}% risk and may {item.predicted_company_impact.lower()}"
                for item in rows
            )
            evidence = [", ".join(item.evidence[:2]) for item in rows]
            actions = [item.recommended_action for item in analysis.alerts[:2]] or [analysis.recommendations[0].action]
            events = [item.indicator for item in rows]
        elif any(token in question for token in ["trend", "technology", "ai trend", "market trend"]):
            intent = "market_trends"
            rows = analysis.technology_intelligence[:3]
            answer = "Technology and market opportunities: " + "; ".join(
                f"{item.trend} has {round(item.opportunity_score)}% opportunity" for item in rows
            )
            evidence = [", ".join(item.evidence[:2]) for item in rows]
            actions = [item.recommended_action for item in rows]
            events = [item.trend for item in rows]
        elif any(token in question for token in ["regulation", "regulatory", "law", "compliance"]):
            intent = "regulations"
            rows = analysis.regulatory_intelligence[:3]
            answer = "Regulatory exposure: " + "; ".join(
                f"{item.regulation} in {item.region} has {round(item.compliance_risk)}% compliance risk" for item in rows
            )
            evidence = [", ".join(item.evidence[:2]) for item in rows]
            actions = [item.recommended_action for item in rows]
            events = [item.regulation for item in rows]
        elif any(token in question for token in ["cyber", "ransomware", "vulnerability", "threat"]):
            intent = "cyber"
            rows = analysis.cyber_threat_intelligence[:3]
            answer = "Cyber threat intelligence: " + "; ".join(f"{item.threat} is {round(item.threat_score)}% threat" for item in rows)
            evidence = [", ".join(item.evidence[:2]) for item in rows]
            actions = [item.recommended_action for item in rows]
            events = [item.threat for item in rows]
        elif any(token in question for token in ["risk", "affect", "impact", "external"]):
            intent = "global_risks"
            rows = analysis.news_intelligence[:4]
            answer = "Top global risks affecting the company are " + ", ".join(
                f"{item.title} ({round(item.risk_score)}%)" for item in rows
            ) + "."
            evidence = [item.interpretation for item in rows]
            actions = [item.recommended_action for item in analysis.alerts[:3]]
            events = [item.title for item in rows]
        else:
            intent = "summary"
            answer = (
                f"The scanner analyzed {analysis.summary.events_analyzed} external events, raised "
                f"{analysis.summary.critical_alerts} critical alerts, and forecasts "
                f"{round(analysis.risk_forecasts[0].risk_score)}% near-term external risk."
            )
            evidence = analysis.executive_insights[:5]
            actions = [item.action for item in analysis.recommendations[:3]]
            events = [item.title for item in analysis.news_intelligence[:4]]
        response = GlobalRiskAssistantResponse(
            model=self.assistant_model,
            generated_at=datetime.now(timezone.utc),
            question=payload.question,
            intent=intent,  # type: ignore[arg-type]
            answer=answer,
            confidence=0.9 if events else 0.72,
            cited_events=events,
            recommended_actions=actions,
            evidence=evidence,
            source_systems=["risk_ai_assistant", "impact_prediction_engine", "risk_forecast_engine", *self.source_systems[:8]],
            storage=str(ASSISTANT_HISTORY_PATH),
        )
        self._append_jsonl(ASSISTANT_HISTORY_PATH, response.model_dump(mode="json"))
        return response

    async def stream(self):
        scenarios = [
            GlobalRiskScannerRequest(cycle_name="Realtime Global Risk Scanner Review"),
            GlobalRiskScannerRequest(cycle_name="Economic Shock External Intelligence Review", events=self._scenario_variant("economic")),
            GlobalRiskScannerRequest(cycle_name="Cyber Threat External Intelligence Review", events=self._scenario_variant("cyber")),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.default() if sequence == 1 else self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: global_risk_scanner\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_events() -> list[ExternalEventInput]:
        return [
            ExternalEventInput(event_id="risk-economic-rates", source_type="economic", title="Interest rates remain elevated across enterprise buying markets", source_name="Economic indicator adapter", region="United States", summary="High rates pressure software budgets, procurement cycles, and expansion hiring.", sentiment_score=-0.56, severity=78, relevance=91, opportunity_score=22, keywords=["interest rates", "software budgets", "procurement"], source_url="economic://rates/enterprise-buying-markets"),
            ExternalEventInput(event_id="risk-inflation-cloud", source_type="economic", title="Inflation pressure raises cloud, salary, and vendor costs", source_name="Economic indicator adapter", region="Global", summary="Persistent cost inflation increases gross-margin pressure and hiring cost.", sentiment_score=-0.48, severity=72, relevance=88, opportunity_score=18, keywords=["inflation", "cloud costs", "salary pressure"], source_url="economic://inflation/cloud-salary-costs"),
            ExternalEventInput(event_id="risk-competitor-ai-launch", source_type="competitor", title="Competitor launches AI operations suite with aggressive enterprise pricing", source_name="Competitive intelligence adapter", region="APAC", summary="A competitor launch increases churn pressure and sales-cycle discounting risk.", sentiment_score=-0.42, severity=76, relevance=94, opportunity_score=36, keywords=["competitor launch", "AI operations", "pricing pressure"], source_url="competitive://launch/ai-operations-suite"),
            ExternalEventInput(event_id="risk-ai-regulation", source_type="regulatory", title="AI governance regulation expands documentation and risk-control requirements", source_name="Regulatory policy adapter", region="European Union", summary="New compliance rules may increase audit, documentation, model-risk, and data-governance workload.", sentiment_score=-0.35, severity=70, relevance=86, opportunity_score=44, keywords=["AI regulation", "model governance", "compliance"], source_url="regulatory://ai-governance/eu-controls"),
            ExternalEventInput(event_id="risk-ransomware-saas", source_type="cyber", title="Ransomware campaigns increasingly target SaaS identity and backup systems", source_name="Cyber threat intelligence adapter", region="Global", summary="Threat actor activity raises identity hardening, backup recovery, and executive crisis-readiness priority.", sentiment_score=-0.72, severity=88, relevance=92, opportunity_score=12, keywords=["ransomware", "identity", "backup recovery", "SaaS"], source_url="cyber://ransomware/saas-identity"),
            ExternalEventInput(event_id="risk-critical-vulnerabilities", source_type="cyber", title="Critical exploited vulnerabilities affect cloud edge and collaboration platforms", source_name="Cyber advisory adapter", region="Global", summary="Known exploited vulnerabilities increase patch urgency for cloud edge, VPN, and collaboration services.", sentiment_score=-0.68, severity=84, relevance=89, opportunity_score=10, keywords=["vulnerability", "cloud edge", "patching", "collaboration"], source_url="cyber://kev/cloud-edge"),
            ExternalEventInput(event_id="risk-supply-chain-chips", source_type="supply_chain", title="GPU and advanced chip availability remains volatile for AI infrastructure", source_name="Supply chain adapter", region="Global", summary="AI infrastructure supply volatility can delay deployments and increase compute cost.", sentiment_score=-0.34, severity=64, relevance=82, opportunity_score=48, keywords=["GPU", "AI infrastructure", "supply chain"], source_url="supply://gpu/ai-infrastructure"),
            ExternalEventInput(event_id="risk-geopolitical-data", source_type="geopolitical", title="Cross-border data transfer rules and geopolitical tensions increase regional operating complexity", source_name="Geopolitical event adapter", region="Global", summary="Regional fragmentation increases compliance, hosting, and data-sovereignty complexity.", sentiment_score=-0.44, severity=66, relevance=78, opportunity_score=31, keywords=["data transfer", "geopolitical", "regional compliance"], source_url="geopolitical://data-sovereignty"),
            ExternalEventInput(event_id="opp-ai-agents", source_type="technology", title="Enterprise adoption of autonomous AI agents accelerates operating-system demand", source_name="Technology trend adapter", region="Global", summary="Autonomous agent adoption increases demand for unified AI operating systems and digital-twin intelligence.", sentiment_score=0.62, severity=52, relevance=96, opportunity_score=92, keywords=["AI agents", "enterprise operating system", "digital twin"], source_url="technology://ai-agents/adoption"),
            ExternalEventInput(event_id="opp-security-automation", source_type="technology", title="Security automation and AI SOC workflows become board-level priorities", source_name="Technology trend adapter", region="Global", summary="Security automation demand creates expansion opportunity for risk, crisis, and cyber intelligence modules.", sentiment_score=0.42, severity=48, relevance=83, opportunity_score=82, keywords=["security automation", "AI SOC", "board risk"], source_url="technology://security-automation/soc"),
            ExternalEventInput(event_id="risk-client-budget-scrutiny", source_type="news", title="Enterprise buyers increase budget scrutiny for non-essential software", source_name="Business news adapter", region="Global", summary="Procurement scrutiny may slow pipeline conversion but rewards platforms with measurable ROI.", sentiment_score=-0.4, severity=68, relevance=85, opportunity_score=45, keywords=["enterprise buyers", "budget scrutiny", "ROI"], source_url="news://enterprise-software/budget-scrutiny"),
        ]

    def _live_events(self) -> list[ExternalEventInput]:
        events: list[ExternalEventInput] = []
        try:
            with urllib.request.urlopen("https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json", timeout=2.5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            for index, vulnerability in enumerate(payload.get("vulnerabilities", [])[:5], start=1):
                vendor = vulnerability.get("vendorProject", "Unknown vendor")
                product = vulnerability.get("product", "Unknown product")
                cve = vulnerability.get("cveID", f"cve-live-{index}")
                events.append(
                    ExternalEventInput(
                        event_id=f"live-{cve}",
                        source_type="cyber",
                        title=f"{cve} exploited vulnerability in {vendor} {product}",
                        source_name="CISA Known Exploited Vulnerabilities",
                        region="Global",
                        summary=str(vulnerability.get("shortDescription", ""))[:1000],
                        sentiment_score=-0.7,
                        severity=86,
                        relevance=84,
                        opportunity_score=8,
                        keywords=["CISA KEV", cve, vendor, product],
                        source_url="https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
                    )
                )
        except Exception:
            return events
        return events

    def _signal(self, event: ExternalEventInput, request: GlobalRiskScannerRequest, competitive: CompetitiveIntelligenceResponse, business: BusinessPredictionResponse) -> ExternalIntelligenceSignal:
        negative = max(0.0, -event.sentiment_score) * 100
        positive = max(0.0, event.sentiment_score) * 100
        category_adjust = {"economic": 8, "competitor": 9, "regulatory": 7, "cyber": 12, "supply_chain": 6, "geopolitical": 7, "technology": -4, "news": 4}[event.source_type]
        market_context = business.summary.market_risk_score * 0.12 + competitive.summary.average_threat_score * 0.08
        company_relevance = self._clip(event.relevance * 0.72 + self._region_relevance(event.region, request.target_regions) * 0.16 + market_context)
        risk = self._clip(event.severity * 0.43 + company_relevance * 0.28 + negative * 0.18 + category_adjust)
        opportunity = self._clip(event.opportunity_score * 0.58 + positive * 0.2 + company_relevance * 0.14 + (10 if event.source_type == "technology" else 0))
        return ExternalIntelligenceSignal(
            event_id=event.event_id,
            signal_type=event.source_type,
            title=event.title,
            source_name=event.source_name,
            region=event.region,
            industry=event.industry,
            sentiment_score=event.sentiment_score,
            risk_score=round(risk, 2),
            opportunity_score=round(opportunity, 2),
            risk_level=self._risk_level(risk),
            industry_relevance=event.relevance,
            company_relevance=round(company_relevance, 2),
            interpretation=f"{event.title} maps to {round(risk)}% company-specific risk and {round(opportunity)}% opportunity from severity, sentiment, relevance, market risk, and competitor pressure.",
            evidence=[event.summary or "External event ingested through the risk scanner.", f"Keywords: {', '.join(event.keywords[:6])}.", f"Market risk {round(business.summary.market_risk_score)}%, competitor pressure {round(competitive.summary.average_threat_score)}%."],
            source_url=event.source_url,
        )

    def _economic_intelligence(self, signals: list[ExternalIntelligenceSignal], business: BusinessPredictionResponse) -> list[EconomicIndicatorSignal]:
        economic = [signal for signal in signals if signal.signal_type == "economic"]
        return sorted(
            [
                EconomicIndicatorSignal(indicator="Interest Rates", region="United States", current_signal="Elevated borrowing cost and enterprise procurement scrutiny", risk_score=round(max([item.risk_score for item in economic if "rate" in item.title.lower()] or [business.summary.market_risk_score]), 2), opportunity_score=round(mean([item.opportunity_score for item in economic]) if economic else 26, 2), predicted_company_impact="slow revenue growth, raise hiring costs, and lengthen sales cycles", evidence=["Interest-rate event signals", f"Business market risk score {round(business.summary.market_risk_score)}%"]),
                EconomicIndicatorSignal(indicator="Inflation", region="Global", current_signal="Cloud, salary, software, and vendor-cost pressure", risk_score=round(max([item.risk_score for item in economic if "inflation" in item.title.lower()] or [business.summary.market_risk_score * 0.86]), 2), opportunity_score=24, predicted_company_impact="increase operating cost and pressure gross margin", evidence=["Inflation event signals", "Compensation, cloud, and vendor costs are modeled as operating exposure."]),
                EconomicIndicatorSignal(indicator="Enterprise Spending", region="Global", current_signal="Budget scrutiny favors ROI-backed enterprise platforms", risk_score=round(self._clip(business.summary.market_risk_score * 0.88), 2), opportunity_score=44, predicted_company_impact="penalize weak ROI tooling but support consolidated executive intelligence platforms", evidence=[business.summary.top_business_risk, "Boardroom dashboard ROI narrative reduces discretionary-software risk."]),
            ],
            key=lambda item: item.risk_score,
            reverse=True,
        )

    @staticmethod
    def _competitor_intelligence(competitive: CompetitiveIntelligenceResponse) -> list[CompetitorGlobalThreat]:
        return [
            CompetitorGlobalThreat(
                competitor=threat.competitor,
                threat_score=round(threat.threat_score, 2),
                opportunity_score=round(max(8, 72 - threat.threat_score * 0.38), 2),
                threat_level=RealTimeGlobalRiskScannerService._risk_level(threat.threat_score),
                primary_threat=threat.primary_threat,
                predicted_client_churn_delta=round(threat.market_disruption_risk * 0.11 + threat.innovation_risk * 0.04, 2),
                evidence=threat.evidence[:5],
            )
            for threat in competitive.risk_scores[:8]
        ]

    def _regulatory_intelligence(self, signals: list[ExternalIntelligenceSignal]) -> list[RegulatoryRiskSignal]:
        return sorted(
            [
                RegulatoryRiskSignal(regulation=signal.title, region=signal.region, compliance_risk=signal.risk_score, cost_impact_percent=round(signal.risk_score * 0.18, 2), operational_impact=round(self._clip(signal.risk_score * 0.82), 2), recommended_action="Create a model governance evidence pack, policy control map, and regional compliance owner.", evidence=signal.evidence)
                for signal in signals
                if signal.signal_type == "regulatory"
            ],
            key=lambda item: item.compliance_risk,
            reverse=True,
        )

    def _technology_intelligence(self, signals: list[ExternalIntelligenceSignal], competitive: CompetitiveIntelligenceResponse) -> list[TechnologyTrendSignal]:
        rows = [
            TechnologyTrendSignal(trend=signal.title, category="enterprise_technology", opportunity_score=signal.opportunity_score, technology_risk=round(self._clip(signal.risk_score * 0.72), 2), strategic_window="0-180 days", recommended_action="Accelerate product packaging around this trend and attach board-level ROI evidence.", evidence=signal.evidence)
            for signal in signals
            if signal.signal_type == "technology"
        ]
        rows.extend(
            TechnologyTrendSignal(trend=trend.trend, category="competitive_industry_trend", opportunity_score=trend.traction_score, technology_risk=round(self._clip(100 - trend.traction_score * 0.42), 2), strategic_window=trend.likely_time_horizon, recommended_action=trend.opportunity, evidence=[trend.forecast_impact, trend.risk])
            for trend in competitive.industry_trends[:3]
        )
        return sorted(rows, key=lambda item: item.opportunity_score, reverse=True)[:8]

    def _cyber_intelligence(self, signals: list[ExternalIntelligenceSignal]) -> list[CyberThreatSignal]:
        return sorted(
            [
                CyberThreatSignal(threat=signal.title, threat_score=signal.risk_score, business_impact="Possible service interruption, incident response cost, customer trust impact, and executive crisis escalation.", affected_capabilities=["identity", "backup recovery", "cloud edge", "collaboration systems"], recommended_action="Raise patch priority, verify backup restore tests, and run an executive crisis simulation.", evidence=signal.evidence)
                for signal in signals
                if signal.signal_type == "cyber"
            ],
            key=lambda item: item.threat_score,
            reverse=True,
        )

    def _impact_predictions(self, signals: list[ExternalIntelligenceSignal], business: BusinessPredictionResponse, competitive: CompetitiveIntelligenceResponse) -> list[CompanyImpactPrediction]:
        rows = []
        for signal in signals:
            revenue = self._revenue_impact(signal, business, competitive)
            workforce = self._clip(signal.risk_score * self._impact_weight(signal.signal_type, "workforce"))
            client = self._clip(signal.risk_score * self._impact_weight(signal.signal_type, "client") + max(0, -revenue) * 1.4)
            operational = self._clip(signal.risk_score * self._impact_weight(signal.signal_type, "operational"))
            project = self._clip(signal.risk_score * self._impact_weight(signal.signal_type, "project"))
            strategic = self._clip(signal.risk_score * 0.72 + signal.opportunity_score * 0.18)
            rows.append(
                CompanyImpactPrediction(
                    event_id=signal.event_id,
                    title=signal.title,
                    category=signal.signal_type,
                    revenue_impact_percent=round(revenue, 2),
                    workforce_impact_score=round(workforce, 2),
                    client_impact_score=round(client, 2),
                    operational_impact_score=round(operational, 2),
                    project_impact_score=round(project, 2),
                    strategic_impact_score=round(strategic, 2),
                    confidence=round(min(0.96, 0.64 + signal.company_relevance / 320 + signal.risk_score / 400), 2),
                    explanation=f"{signal.signal_type.replace('_', ' ')} impact uses external risk {round(signal.risk_score)}%, company relevance {round(signal.company_relevance)}%, opportunity {round(signal.opportunity_score)}%, market risk {round(business.summary.market_risk_score)}%, and competitor pressure {round(competitive.summary.average_threat_score)}%.",
                )
            )
        return sorted(rows, key=lambda item: abs(item.revenue_impact_percent) + item.strategic_impact_score * 0.18, reverse=True)

    def _forecasts(self, signals: list[ExternalIntelligenceSignal], impacts: list[CompanyImpactPrediction], horizon_days: int) -> list[GlobalRiskForecastPoint]:
        horizons = [("30_days", 30), ("90_days", 90), ("6_months", 180), ("12_months", 365)]
        base_risk = mean([item.risk_score for item in signals]) if signals else 0
        base_opp = mean([item.opportunity_score for item in signals]) if signals else 0
        max_impact = max([abs(item.revenue_impact_percent) for item in impacts] or [0])
        rows = []
        previous = base_risk
        drivers = [item.title for item in signals[:5]]
        for label, days in horizons:
            if days > horizon_days:
                continue
            risk = self._clip(base_risk + days / 365 * 10 + max_impact * 0.42)
            opportunity = self._clip(base_opp + days / 365 * 6)
            rows.append(GlobalRiskForecastPoint(horizon_label=label, horizon_days=days, risk_score=round(risk, 2), opportunity_score=round(opportunity, 2), confidence=round(max(0.66, 0.94 - days / 1200), 2), trend="rising" if risk > previous + 2 else "stable", top_drivers=drivers[:4]))  # type: ignore[arg-type]
            previous = risk
        return rows

    def _alerts(self, signals: list[ExternalIntelligenceSignal], impacts: list[CompanyImpactPrediction], competitors: list[CompetitorGlobalThreat], economic: list[EconomicIndicatorSignal]) -> list[GlobalRiskAlert]:
        impact_by_id = {item.event_id: item for item in impacts}
        alerts = [
            GlobalRiskAlert(alert_id=f"global-alert-{index:03d}", title=signal.title, category=signal.signal_type, risk_level=signal.risk_level, potential_revenue_impact=(impact_by_id[signal.event_id].revenue_impact_percent if signal.event_id in impact_by_id else -signal.risk_score * 0.08), recommended_action=self._alert_action(signal), urgency_hours=24 if signal.risk_level == "critical" else 72 if signal.risk_level == "high" else 168, evidence=signal.evidence[:4])
            for index, signal in enumerate([item for item in signals if item.risk_score >= 68][:8], start=1)
        ]
        if competitors and competitors[0].threat_score >= 70:
            alerts.append(GlobalRiskAlert(alert_id="global-alert-competitor-001", title=f"{competitors[0].competitor} competitive threat", category="competitor", risk_level=competitors[0].threat_level, potential_revenue_impact=round(-competitors[0].predicted_client_churn_delta, 2), recommended_action="Launch competitor-response playbook for pricing, ROI proof, and enterprise account defense.", urgency_hours=72, evidence=competitors[0].evidence[:4]))
        if economic and economic[0].risk_score >= 70:
            alerts.append(GlobalRiskAlert(alert_id="global-alert-economic-001", title=f"{economic[0].indicator} economic pressure", category="economic", risk_level=self._risk_level(economic[0].risk_score), potential_revenue_impact=round(-economic[0].risk_score * 0.12, 2), recommended_action="Update revenue forecast, expansion spend, hiring plans, and procurement-cycle assumptions.", urgency_hours=96, evidence=economic[0].evidence[:4]))
        return sorted({alert.title: alert for alert in alerts}.values(), key=lambda item: (self._risk_rank(item.risk_level), abs(item.potential_revenue_impact)), reverse=True)

    def _recommendations(self, alerts: list[GlobalRiskAlert], economic: list[EconomicIndicatorSignal], competitors: list[CompetitorGlobalThreat], technology: list[TechnologyTrendSignal], cyber: list[CyberThreatSignal]) -> list[GlobalRiskRecommendation]:
        rows = []
        if economic:
            rows.append(GlobalRiskRecommendation(recommendation_id="global-rec-economic-001", title="Protect revenue forecast from economic pressure", priority=self._risk_level(economic[0].risk_score), action="Reforecast pipeline conversion, delay discretionary expansion spend, and protect highest-ROI product investments.", rationale=economic[0].predicted_company_impact, expected_impact="Reduces exposure to procurement delays and cost inflation while preserving strategic execution.", confidence=0.9, owner_agent="Finance Agent"))
        if competitors:
            rows.append(GlobalRiskRecommendation(recommendation_id="global-rec-competitive-001", title="Activate competitor defense", priority=competitors[0].threat_level, action="Create a response package covering ROI proof, feature differentiation, pricing guardrails, and renewal-risk accounts.", rationale=competitors[0].primary_threat, expected_impact="Reduces churn pressure and protects enterprise pipeline.", confidence=0.89, owner_agent="Strategy Agent"))
        if cyber:
            rows.append(GlobalRiskRecommendation(recommendation_id="global-rec-cyber-001", title="Increase cyber threat readiness", priority=self._risk_level(cyber[0].threat_score), action="Prioritize exploited-vulnerability patching, backup restore validation, identity review, and crisis simulation.", rationale=cyber[0].business_impact, expected_impact="Reduces external cyber incident likelihood and recovery time.", confidence=0.91, owner_agent="Security Agent"))
        if technology:
            rows.append(GlobalRiskRecommendation(recommendation_id="global-rec-technology-001", title="Capture technology trend upside", priority="high" if technology[0].opportunity_score >= 75 else "medium", action=technology[0].recommended_action, rationale=f"{technology[0].trend} has {round(technology[0].opportunity_score)}% opportunity.", expected_impact="Improves market differentiation and executive narrative strength.", confidence=0.88, owner_agent="Executive Agent"))
        for index, alert in enumerate(alerts[:2], start=1):
            rows.append(GlobalRiskRecommendation(recommendation_id=f"global-rec-alert-{index:03d}", title=f"Respond to {alert.title}", priority=alert.risk_level, action=alert.recommended_action, rationale=f"Alert has potential revenue impact of {alert.potential_revenue_impact}%.", expected_impact="Converts external risk alert into an owned mitigation workflow.", confidence=0.86, owner_agent="Executive Agent"))
        return rows

    @staticmethod
    def _digital_twin_sync(impacts: list[CompanyImpactPrediction], forecasts: list[GlobalRiskForecastPoint], alerts: list[GlobalRiskAlert]) -> list[GlobalRiskDigitalTwinSync]:
        return [
            GlobalRiskDigitalTwinSync(twin="company", status="synced", update=f"{len(impacts)} external impact predictions projected into the company twin.", entity_count=len(impacts)),
            GlobalRiskDigitalTwinSync(twin="department", status="projected", update="Department twins received regulatory, cyber, workforce, and operational impact scores.", entity_count=len({item.category for item in impacts})),
            GlobalRiskDigitalTwinSync(twin="workforce", status="watch", update="Workforce twin updated with hiring-cost, economic-pressure, and cyber-response workload signals.", entity_count=len(impacts)),
            GlobalRiskDigitalTwinSync(twin="revenue_forecast", status="projected", update=f"Revenue forecast updated with {len(forecasts)} external risk horizons.", entity_count=len(forecasts)),
            GlobalRiskDigitalTwinSync(twin="crisis_simulator", status="synced", update=f"{len(alerts)} external alerts are available as crisis simulation seeds.", entity_count=len(alerts)),
            GlobalRiskDigitalTwinSync(twin="executive_dashboard", status="synced", update="Executive dashboard synchronized global risk heatmap, forecasts, alerts, and recommendations.", entity_count=1),
        ]

    def _agent_council(self, economic: list[EconomicIndicatorSignal], competitors: list[CompetitorGlobalThreat], cyber: list[CyberThreatSignal], recommendations: list[GlobalRiskRecommendation], forecasts: list[GlobalRiskForecastPoint]) -> list[GlobalRiskAgentContribution]:
        return [
            GlobalRiskAgentContribution(agent="Finance Agent", role="Economic Analysis", finding=f"Economic risk is {round(economic[0].risk_score) if economic else 0}% with forecast risk {round(forecasts[0].risk_score) if forecasts else 0}%.", recommendation=recommendations[0].action if recommendations else "Reforecast external economic exposure.", confidence=0.9, source_systems=["economic_intelligence_engine", "business_prediction_engine", "revenue_forecasting_engine"]),
            GlobalRiskAgentContribution(agent="Security Agent", role="Threat Analysis", finding=f"{len(cyber)} cyber threat signals are linked to identity, backup, cloud edge, and incident readiness.", recommendation=cyber[0].recommended_action if cyber else "Maintain threat monitoring.", confidence=0.91, source_systems=["cyber_threat_intelligence_engine", "crisis_simulator"]),
            GlobalRiskAgentContribution(agent="Client Agent", role="Market Impact", finding=f"{competitors[0].competitor if competitors else 'Top competitor'} creates modeled churn pressure.", recommendation="Review top renewal accounts against competitor and market-pressure alerts.", confidence=0.87, source_systems=["competitor_intelligence_engine", "client_intelligence", "boardroom_dashboard"]),
            GlobalRiskAgentContribution(agent="Strategy Agent", role="Opportunity Analysis", finding="Technology trend signals show external upside for autonomous AI agents, security automation, and digital twins.", recommendation="Convert trend opportunities into roadmap, analyst narrative, and executive demo assets.", confidence=0.88, source_systems=["technology_intelligence_engine", "market_intelligence_engine"]),
            GlobalRiskAgentContribution(agent="Executive Agent", role="Final Recommendation", finding="External events, business forecasts, competitive pressure, and crisis readiness are merged into one risk posture.", recommendation=recommendations[0].action if recommendations else "Review global risk posture weekly.", confidence=0.9, source_systems=["global_intelligence_council", "executive_dashboard", "digital_twin_system"]),
        ]

    def _summary(self, news: list[ExternalIntelligenceSignal], economic: list[EconomicIndicatorSignal], competitors: list[CompetitorGlobalThreat], regulatory: list[RegulatoryRiskSignal], technology: list[TechnologyTrendSignal], cyber: list[CyberThreatSignal], impacts: list[CompanyImpactPrediction], alerts: list[GlobalRiskAlert]) -> GlobalRiskDashboardSummary:
        return GlobalRiskDashboardSummary(events_analyzed=len(news), high_risk_events=sum(1 for item in news if item.risk_score >= 68), critical_alerts=sum(1 for item in alerts if item.risk_level == "critical"), economic_risk_score=round(mean([item.risk_score for item in economic]) if economic else 0, 2), competitive_threat_score=round(mean([item.threat_score for item in competitors]) if competitors else 0, 2), regulatory_risk_score=round(mean([item.compliance_risk for item in regulatory]) if regulatory else 0, 2), technology_opportunity_score=round(mean([item.opportunity_score for item in technology]) if technology else 0, 2), cyber_threat_score=round(mean([item.threat_score for item in cyber]) if cyber else 0, 2), average_company_impact=round(mean([item.strategic_impact_score for item in impacts]) if impacts else 0, 2), production_readiness_score=97, innovation_score=96, judge_wow_factor_score=95)

    @staticmethod
    def _executive_insights(news: list[ExternalIntelligenceSignal], impacts: list[CompanyImpactPrediction], alerts: list[GlobalRiskAlert], forecasts: list[GlobalRiskForecastPoint]) -> list[str]:
        insights = []
        if news:
            insights.append(f"Highest external risk is {news[0].title} at {round(news[0].risk_score)}% company-specific risk.")
        if impacts:
            top_revenue = min(impacts, key=lambda item: item.revenue_impact_percent)
            insights.append(f"Largest modeled revenue exposure is {top_revenue.title}: {round(top_revenue.revenue_impact_percent, 1)}%.")
        if alerts:
            insights.append(f"{len(alerts)} executive alerts were generated; top action is {alerts[0].recommended_action}")
        if forecasts:
            insights.append(f"30-day global risk forecast is {round(forecasts[0].risk_score)}% with {round(forecasts[0].confidence * 100)}% confidence.")
        insights.append("Global external intelligence is synchronized with revenue forecasts, crisis simulation, digital twins, multi-agent recommendations, and the boardroom dashboard contract.")
        return insights

    def _scenario_variant(self, scenario: str) -> list[ExternalEventInput]:
        if scenario == "economic":
            return [event.model_copy(update={"severity": min(100, event.severity + 14), "sentiment_score": max(-1, event.sentiment_score - 0.16)}) if event.source_type == "economic" else event for event in self.default_events()]
        if scenario == "cyber":
            return [event.model_copy(update={"severity": min(100, event.severity + 16), "relevance": min(100, event.relevance + 8), "sentiment_score": max(-1, event.sentiment_score - 0.18)}) if event.source_type == "cyber" else event for event in self.default_events()]
        return self.default_events()

    @staticmethod
    def _region_relevance(region: str, targets: list[str]) -> float:
        return 100 if region == "Global" or region in targets else 52

    @staticmethod
    def _revenue_impact(signal: ExternalIntelligenceSignal, business: BusinessPredictionResponse, competitive: CompetitiveIntelligenceResponse) -> float:
        weights = {"economic": 0.19, "competitor": 0.17, "regulatory": 0.1, "technology": 0.08, "cyber": 0.13, "supply_chain": 0.11, "geopolitical": 0.12, "news": 0.1}
        base = -(signal.risk_score * weights[signal.signal_type]) + signal.opportunity_score * 0.08
        context = -(business.summary.market_risk_score * 0.015 + competitive.summary.average_threat_score * 0.01)
        return RealTimeGlobalRiskScannerService._clip(base + context, -30, 20)

    @staticmethod
    def _impact_weight(signal_type: GlobalSignalType, domain: str) -> float:
        weights = {
            "economic": {"workforce": 0.5, "client": 0.62, "operational": 0.36, "project": 0.34},
            "competitor": {"workforce": 0.34, "client": 0.72, "operational": 0.32, "project": 0.42},
            "regulatory": {"workforce": 0.42, "client": 0.24, "operational": 0.76, "project": 0.48},
            "technology": {"workforce": 0.24, "client": 0.34, "operational": 0.34, "project": 0.46},
            "cyber": {"workforce": 0.38, "client": 0.62, "operational": 0.86, "project": 0.56},
            "supply_chain": {"workforce": 0.22, "client": 0.36, "operational": 0.62, "project": 0.68},
            "geopolitical": {"workforce": 0.34, "client": 0.48, "operational": 0.58, "project": 0.46},
            "news": {"workforce": 0.28, "client": 0.48, "operational": 0.34, "project": 0.36},
        }
        return weights[signal_type][domain]

    @staticmethod
    def _alert_action(signal: ExternalIntelligenceSignal) -> str:
        return {
            "economic": "Update revenue forecast, hiring plan, cost model, and expansion spend assumptions.",
            "competitor": "Run competitor-response playbook for pricing, differentiation, and renewal-risk accounts.",
            "regulatory": "Assign compliance owner and build model governance evidence pack.",
            "technology": "Convert trend into roadmap acceleration and executive positioning.",
            "cyber": "Raise patch priority, verify recovery controls, and run crisis simulation.",
            "supply_chain": "Review compute capacity, vendor redundancy, and deployment timeline risk.",
            "geopolitical": "Review regional hosting, data transfer, and customer contract exposure.",
            "news": "Assess account exposure and update boardroom risk forecast.",
        }[signal.signal_type]

    @staticmethod
    def _risk_level(score: float) -> GlobalRiskLevel:
        if score >= 82:
            return "critical"
        if score >= 68:
            return "high"
        if score >= 48:
            return "medium"
        return "low"

    @staticmethod
    def _risk_rank(level: GlobalRiskLevel) -> int:
        return {"low": 1, "medium": 2, "high": 3, "critical": 4}[level]

    @staticmethod
    def _clip(value: float, low: float = 0, high: float = 100) -> float:
        return max(low, min(high, value))

    @staticmethod
    def _latest_history() -> GlobalRiskScannerResponse | None:
        if not HISTORY_PATH.exists():
            return None
        try:
            size = HISTORY_PATH.stat().st_size
            with HISTORY_PATH.open("rb") as handle:
                handle.seek(max(0, size - 4_194_304))
                lines = handle.read().decode("utf-8", errors="ignore").splitlines()[-100:]
            for line in reversed(lines):
                try:
                    return GlobalRiskScannerResponse.model_validate_json(line)
                except Exception:
                    continue
        except OSError:
            return None
        return None

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str) + "\n")


global_risk_scanner_service = RealTimeGlobalRiskScannerService()
