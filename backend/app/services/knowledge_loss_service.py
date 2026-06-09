from __future__ import annotations

import asyncio
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

import networkx as nx
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.ai.knowledge_loss_engine import knowledge_loss_engine
from app.core.cache import TTLResponseCache
from app.schemas.knowledge_loss import (
    ExpertiseProfile,
    GeneratedKnowledgeDocument,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    KnowledgeLossRequest,
    KnowledgeLossResponse,
    KnowledgeLossSummary,
    KnowledgePriority,
    KnowledgeRiskAlert,
    KnowledgeRiskForecastPoint,
    KnowledgeSourceSignal,
    KnowledgeTransferRecommendation,
    OnboardingRoadmap,
    OrganizationalMemoryHeatmapPoint,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "knowledge_loss_history.jsonl"
GRAPH_PATH = DATA_DIR / "knowledge_graph_neo4j_export.json"

SKILL_ALIASES = {
    "kubernetes": ["kubernetes", "cluster", "helm", "ingress", "eks", "aks"],
    "mlops": ["mlops", "model registry", "feature store", "training pipeline", "inference"],
    "incident response": ["incident", "outage", "sev", "rollback", "root cause"],
    "security": ["security", "privileged", "token", "zero trust", "vulnerability"],
    "postgresql": ["postgres", "postgresql", "database", "schema", "replication"],
    "redis": ["redis", "cache", "stream", "pubsub"],
    "rag": ["rag", "retrieval", "embedding", "vector", "qdrant", "chroma"],
    "fastapi": ["fastapi", "api", "endpoint", "async service"],
    "frontend": ["react", "next.js", "dashboard", "typescript", "ui"],
    "deployment": ["deployment", "release", "pipeline", "blue green", "canary"],
}


class KnowledgeLossService:
    model_name = "AI Knowledge Loss Prevention System"
    source_systems = [
        "tfidf_expertise_extraction",
        "networkx_knowledge_graph",
        "neo4j_compatible_graph_export",
        "random_forest_knowledge_loss_forecaster",
        "gradient_boosting_disruption_forecaster",
        "documentation_generation_engine",
        "organizational_memory_jsonl",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[KnowledgeLossResponse] = TTLResponseCache(ttl_seconds=8)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def analyze(self, payload: KnowledgeLossRequest | None = None) -> KnowledgeLossResponse:
        if payload is None:
            return self._cache.get_or_set(self._default_uncached)
        return self._analyze_uncached(payload)

    def _default_uncached(self) -> KnowledgeLossResponse:
        return self._analyze_uncached(self.default_request())

    def _analyze_uncached(self, payload: KnowledgeLossRequest) -> KnowledgeLossResponse:
        request = payload if payload.sources else self.default_request()
        sources = request.sources or self.default_request().sources
        enriched = [self._enrich_source(source) for source in sources]
        graph = self._knowledge_graph(enriched)
        centrality = nx.pagerank(graph, weight="weight") if graph.number_of_nodes() else {}
        feature_rows = self._employee_feature_rows(enriched, centrality)
        model_predictions = knowledge_loss_engine.predict([row["features"] for row in feature_rows])
        profiles = [
            self._expertise_profile(row, prediction)
            for row, prediction in zip(feature_rows, model_predictions)
        ]
        profiles.sort(key=lambda item: (item.knowledge_loss_probability, item.operational_disruption_risk, item.knowledge_criticality), reverse=True)
        graph_nodes = self._graph_nodes(graph, profiles)
        graph_edges = self._graph_edges(graph, profiles)
        documents = self._generated_documents(enriched, profiles)
        forecasts = self._forecasts(request.horizon_days, profiles, model_predictions)
        heatmap = self._memory_heatmap(enriched, profiles)
        onboarding = self._onboarding_roadmaps(request.target_role, documents, profiles)
        recommendations = self._recommendations(profiles, documents, heatmap)
        alerts = self._alerts(profiles, heatmap)
        response = KnowledgeLossResponse(
            model=knowledge_loss_engine.model_name,
            generated_at=datetime.now(timezone.utc),
            cycle_name=request.cycle_name,
            horizon_days=request.horizon_days,
            target_role=request.target_role,
            expertise_profiles=profiles,
            graph_nodes=graph_nodes,
            graph_edges=graph_edges,
            generated_documents=documents,
            forecasts=forecasts,
            memory_heatmap=heatmap,
            onboarding_roadmaps=onboarding,
            recommendations=recommendations,
            alerts=alerts,
            executive_insights=self._executive_insights(profiles, heatmap, documents),
            summary=self._summary(sources, profiles, graph_nodes, graph_edges, documents),
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
            graph_store=str(GRAPH_PATH),
        )
        self._persist_graph(graph_nodes, graph_edges)
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: KnowledgeLossRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, attrition_delta=0.05, doc_delta=-0.05, handoff_delta=-0.04),
            self._scenario_variant(base, attrition_delta=0.12, doc_delta=-0.12, handoff_delta=-0.1),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: knowledge_loss\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def _enrich_source(self, source: KnowledgeSourceSignal) -> KnowledgeSourceSignal:
        skills = set(source.skills)
        systems = set(source.systems)
        text = source.content.lower()
        for skill, aliases in SKILL_ALIASES.items():
            if any(alias in text for alias in aliases):
                skills.add(skill)
        for candidate in ["nexusmind ai", "kubernetes platform", "rag assistant", "payment api", "model registry", "postgresql cluster", "redis stream", "security gateway", "deployment pipeline"]:
            if candidate in text:
                systems.add(candidate.title())
        if not systems:
            systems.add("Enterprise Workflow")
        return source.model_copy(update={"skills": sorted(skills), "systems": sorted(systems)})

    def _knowledge_graph(self, sources: list[KnowledgeSourceSignal]) -> nx.Graph:
        graph = nx.Graph()
        for source in sources:
            employee_node = f"employee:{source.employee_id}"
            team_node = f"team:{self._slug(source.team)}"
            document_node = f"document:{source.source_id}"
            graph.add_node(employee_node, label=source.employee_name, node_type="employee", department=source.department, team=source.team)
            graph.add_node(team_node, label=source.team, node_type="team", department=source.department)
            graph.add_node(document_node, label=source.title, node_type="document", source_type=source.source_type)
            self._add_edge(graph, employee_node, team_node, "member_of", 54 + source.seniority * 24, source.business_criticality * 100, source.team)
            self._add_edge(graph, employee_node, document_node, "authored_or_discussed", 42 + source.docs_authored * 8 + source.meeting_mentions * 2, (1 - source.documentation_quality) * 100, source.title)
            for skill in source.skills:
                skill_node = f"skill:{self._slug(skill)}"
                graph.add_node(skill_node, label=skill.title(), node_type="skill")
                strength = min(100, 45 + source.contribution_count * 2 + source.incident_resolutions * 5 + source.commit_count * 0.5)
                risk = max(source.attrition_risk, 1 - min(1, source.redundancy_count / 4)) * 100
                self._add_edge(graph, employee_node, skill_node, "owns_expertise", strength, risk, source.title)
                self._add_edge(graph, document_node, skill_node, "documents_skill", 35 + source.documentation_quality * 55, (1 - source.documentation_quality) * 100, source.title)
            for system in source.systems:
                system_node = f"system:{self._slug(system)}"
                graph.add_node(system_node, label=system, node_type="system", business_criticality=source.business_criticality)
                strength = min(100, 48 + source.incident_resolutions * 8 + source.contribution_count * 2 + source.business_criticality * 16)
                risk = max(source.attrition_risk, 1 - min(1, source.redundancy_count / 4), 1 - source.handoff_readiness) * 100
                self._add_edge(graph, employee_node, system_node, "owns_system_knowledge", strength, risk, source.title)
                self._add_edge(graph, document_node, system_node, "documents_system", 38 + source.documentation_quality * 52, (1 - source.documentation_quality) * 100, source.title)
                for skill in source.skills[:4]:
                    skill_node = f"skill:{self._slug(skill)}"
                    self._add_edge(graph, system_node, skill_node, "requires_skill", 48 + source.business_criticality * 38, risk * 0.55, source.title)
        return graph

    @staticmethod
    def _add_edge(graph: nx.Graph, source: str, target: str, relation: str, strength: float, risk: float, evidence: str) -> None:
        strength = float(np.clip(strength, 0, 100))
        risk = float(np.clip(risk, 0, 100))
        if graph.has_edge(source, target):
            existing = graph[source][target]
            existing["weight"] = max(existing["weight"], strength / 100)
            existing["strength"] = max(existing["strength"], strength)
            existing["risk"] = max(existing["risk"], risk)
            existing["evidence"] = f"{existing['evidence']}; {evidence}"
            return
        graph.add_edge(source, target, relation=relation, weight=strength / 100, strength=strength, risk=risk, evidence=evidence)

    def _employee_feature_rows(self, sources: list[KnowledgeSourceSignal], centrality: dict[str, float]) -> list[dict[str, object]]:
        grouped: dict[str, list[KnowledgeSourceSignal]] = defaultdict(list)
        for source in sources:
            grouped[source.employee_id].append(source)
        rows: list[dict[str, object]] = []
        max_centrality = max(centrality.values(), default=0.001)
        for employee_id, employee_sources in grouped.items():
            first = employee_sources[0]
            skills = sorted({skill for source in employee_sources for skill in source.skills})
            systems = sorted({system for source in employee_sources for system in source.systems})
            contribution = sum(source.contribution_count for source in employee_sources)
            incidents = sum(source.incident_resolutions for source in employee_sources)
            docs = sum(source.docs_authored for source in employee_sources)
            commits = sum(source.commit_count for source in employee_sources)
            mentions = sum(source.meeting_mentions for source in employee_sources)
            avg_attrition = mean(source.attrition_risk for source in employee_sources)
            avg_seniority = mean(source.seniority for source in employee_sources)
            avg_doc = mean(source.documentation_quality for source in employee_sources)
            avg_criticality = mean(source.business_criticality for source in employee_sources)
            avg_handoff = mean(source.handoff_readiness for source in employee_sources)
            avg_redundancy = mean(source.redundancy_count for source in employee_sources)
            recency = mean(source.last_updated_days for source in employee_sources)
            graph_node = f"employee:{employee_id}"
            graph_centrality = centrality.get(graph_node, 0) / max_centrality
            expertise_depth = self._clip01((contribution / 42) * 0.2 + (incidents / 12) * 0.24 + (docs / 16) * 0.16 + (commits / 120) * 0.16 + len(skills) / 20 * 0.12 + graph_centrality * 0.12)
            features = {
                "expertise_depth": expertise_depth,
                "criticality": self._clip01(avg_criticality * 0.74 + graph_centrality * 0.26),
                "attrition_risk": self._clip01(avg_attrition),
                "documentation_gap": self._clip01(1 - avg_doc),
                "redundancy_gap": self._clip01(1 - min(1, avg_redundancy / 4)),
                "recency_pressure": self._clip01(recency / 120),
                "incident_ownership": self._clip01(incidents / 12),
                "commit_ownership": self._clip01(commits / 140),
                "meeting_dependency": self._clip01(mentions / 16),
                "handoff_gap": self._clip01(1 - avg_handoff),
                "seniority": self._clip01(avg_seniority),
                "business_criticality": self._clip01(avg_criticality),
            }
            rows.append(
                {
                    "employee_id": employee_id,
                    "employee_name": first.employee_name,
                    "department": first.department,
                    "team": first.team,
                    "role": first.role,
                    "skills": skills,
                    "systems": systems,
                    "sources": employee_sources,
                    "features": features,
                    "centrality": graph_centrality,
                }
            )
        return rows

    def _expertise_profile(self, row: dict[str, object], prediction: dict[str, float]) -> ExpertiseProfile:
        features = row["features"]
        assert isinstance(features, dict)
        skills = row["skills"]
        systems = row["systems"]
        assert isinstance(skills, list)
        assert isinstance(systems, list)
        expertise = self._clip(features["expertise_depth"] * 100)
        criticality = self._clip(features["criticality"] * 100)
        doc_coverage = self._clip((1 - features["documentation_gap"]) * 100)
        ownership = self._clip((features["expertise_depth"] * 0.48 + features["redundancy_gap"] * 0.36 + features["criticality"] * 0.16) * 100)
        loss = self._clip(prediction["knowledge_loss_probability"] + max(0, ownership - 65) * 0.12)
        disruption = self._clip(prediction["operational_disruption_risk"] + max(0, criticality - 70) * 0.08)
        employee_name = str(row["employee_name"])
        systems_list = [str(system) for system in systems[:5]]
        skills_list = [str(skill) for skill in skills[:6]]
        return ExpertiseProfile(
            employee_id=str(row["employee_id"]),
            employee_name=employee_name,
            department=str(row["department"]),
            team=str(row["team"]),
            role=str(row["role"]),
            top_expertise=skills_list,
            owned_systems=systems_list,
            expertise_score=round(expertise, 2),
            knowledge_criticality=round(criticality, 2),
            ownership_concentration=round(ownership, 2),
            documentation_coverage=round(doc_coverage, 2),
            attrition_risk=round(features["attrition_risk"] * 100, 2),
            knowledge_loss_probability=round(loss, 2),
            operational_disruption_risk=round(disruption, 2),
            confidence=round(float(prediction["confidence"]), 3),
            evidence=[
                f"{employee_name} owns {len(systems_list)} system area(s) and {len(skills_list)} expertise domain(s).",
                f"Documentation coverage {doc_coverage:.0f}% with redundancy gap {features['redundancy_gap'] * 100:.0f}%.",
                f"Graph centrality projection {float(row['centrality']) * 100:.0f}% from enterprise knowledge relationships.",
            ],
            transfer_actions=self._transfer_actions(employee_name, systems_list, skills_list, loss, doc_coverage),
        )

    def _graph_nodes(self, graph: nx.Graph, profiles: list[ExpertiseProfile]) -> list[KnowledgeGraphNode]:
        profile_risk = {f"employee:{profile.employee_id}": profile.knowledge_loss_probability for profile in profiles}
        degree = dict(graph.degree(weight="weight"))
        max_degree = max(degree.values(), default=1)
        nodes: list[KnowledgeGraphNode] = []
        for node_id, attrs in graph.nodes(data=True):
            node_type = attrs.get("node_type", "skill")
            risk = profile_risk.get(node_id, 0)
            if not risk:
                neighbor_risks = [profile_risk.get(neighbor, 0) for neighbor in graph.neighbors(node_id)]
                risk = max(neighbor_risks, default=0) * 0.72
            nodes.append(
                KnowledgeGraphNode(
                    node_id=str(node_id),
                    label=str(attrs.get("label", node_id)),
                    node_type=node_type,
                    risk_score=round(self._clip(risk), 2),
                    size=round(12 + degree.get(node_id, 0) / max_degree * 72, 2),
                    metadata={key: value for key, value in attrs.items() if isinstance(value, (str, int, float)) and key not in {"label", "node_type"}},
                )
            )
        return sorted(nodes, key=lambda item: (item.risk_score, item.size), reverse=True)[:80]

    def _graph_edges(self, graph: nx.Graph, profiles: list[ExpertiseProfile]) -> list[KnowledgeGraphEdge]:
        profile_risk = {f"employee:{profile.employee_id}": profile.knowledge_loss_probability for profile in profiles}
        edges: list[KnowledgeGraphEdge] = []
        for source, target, attrs in graph.edges(data=True):
            risk = max(float(attrs.get("risk", 0)), profile_risk.get(source, 0), profile_risk.get(target, 0))
            edges.append(
                KnowledgeGraphEdge(
                    source=str(source),
                    target=str(target),
                    relation=str(attrs.get("relation", "related")),
                    strength=round(self._clip(float(attrs.get("strength", 0))), 2),
                    risk=round(self._clip(risk), 2),
                    evidence=str(attrs.get("evidence", ""))[:300],
                )
            )
        return sorted(edges, key=lambda item: (item.risk, item.strength), reverse=True)[:120]

    def _generated_documents(self, sources: list[KnowledgeSourceSignal], profiles: list[ExpertiseProfile]) -> list[GeneratedKnowledgeDocument]:
        if not profiles:
            return []
        by_system: dict[str, list[KnowledgeSourceSignal]] = defaultdict(list)
        for source in sources:
            for system in source.systems:
                by_system[system].append(source)
        top_systems = sorted(by_system, key=lambda system: max(source.business_criticality for source in by_system[system]), reverse=True)[:4]
        documents: list[GeneratedKnowledgeDocument] = []
        profile_by_name = {profile.employee_name: profile for profile in profiles}
        for index, system in enumerate(top_systems, start=1):
            system_sources = by_system[system]
            owner_counts = Counter(source.employee_name for source in system_sources)
            owner = owner_counts.most_common(1)[0][0]
            owner_profile = profile_by_name.get(owner)
            skills = sorted({skill for source in system_sources for skill in source.skills})
            coverage = mean(source.documentation_quality for source in system_sources) * 100
            snippets = self._summarize_sources(system_sources)
            avg_doc = mean(source.documentation_quality for source in system_sources)
            max_criticality = max(source.business_criticality for source in system_sources)
            doc_type = "sop" if index == 1 or (max_criticality >= 0.9 and avg_doc < 0.55) else ("deployment_guide" if "deployment" in " ".join(skills) else "architecture_summary")
            title = f"{system} Knowledge Transfer SOP" if doc_type == "sop" else f"{system} Architecture Knowledge Guide"
            content = (
                f"Owner: {owner}. Critical system: {system}. "
                f"Core expertise: {', '.join(skills[:6]) or 'operational workflow'}. "
                f"Operating context: {snippets}. "
                f"Transfer protocol: record a walkthrough, document rollback steps, identify two backup owners, "
                f"run a scenario review, and validate the guide through a new-hire dry run. "
                f"Current risk: {owner_profile.knowledge_loss_probability if owner_profile else 0:.0f}% knowledge-loss probability."
            )
            documents.append(
                GeneratedKnowledgeDocument(
                    document_id=f"knowledge-doc-{self._slug(system)}",
                    title=title,
                    document_type=doc_type,
                    owner=owner,
                    systems=[system],
                    content=content,
                    coverage_score=round(self._clip(coverage), 2),
                    confidence=round(float(np.clip(0.72 + len(system_sources) * 0.04 + coverage / 500, 0.72, 0.94)), 3),
                    source_count=len(system_sources),
                )
            )
        return documents

    def _forecasts(self, horizon_days: int, profiles: list[ExpertiseProfile], predictions: list[dict[str, float]]) -> list[KnowledgeRiskForecastPoint]:
        points: list[KnowledgeRiskForecastPoint] = []
        for profile, prediction in zip(profiles[:5], predictions[:5]):
            transfer = float(prediction["transfer_completion_probability"])
            pressure = (profile.knowledge_criticality * 0.035 + profile.attrition_risk * 0.045 + max(0, 60 - profile.documentation_coverage) * 0.035) / 6
            for index in range(6):
                day = max(1, round((index + 1) * horizon_days / 6))
                drift = index * pressure
                points.append(
                    KnowledgeRiskForecastPoint(
                        employee_name=profile.employee_name,
                        day=day,
                        knowledge_loss_probability=round(self._clip(profile.knowledge_loss_probability + drift), 2),
                        operational_disruption_risk=round(self._clip(profile.operational_disruption_risk + drift * 0.84), 2),
                        transfer_completion_probability=round(self._clip(transfer - drift * 0.72), 2),
                        confidence=round(float(np.clip(profile.confidence - index * 0.02, 0.64, 0.95)), 3),
                    )
                )
        return points

    def _memory_heatmap(self, sources: list[KnowledgeSourceSignal], profiles: list[ExpertiseProfile]) -> list[OrganizationalMemoryHeatmapPoint]:
        profile_by_employee = {profile.employee_id: profile for profile in profiles}
        grouped: dict[tuple[str, str], list[KnowledgeSourceSignal]] = defaultdict(list)
        for source in sources:
            for system in source.systems:
                grouped[(source.department, system)].append(source)
        heatmap: list[OrganizationalMemoryHeatmapPoint] = []
        for (department, system), items in grouped.items():
            owners = {item.employee_id for item in items}
            max_owner_share = max(Counter(item.employee_id for item in items).values()) / len(items)
            coverage = mean(item.documentation_quality for item in items) * 100
            redundancy = min(100, len(owners) / 4 * 100 + mean(item.redundancy_count for item in items) * 8)
            owner_risk = max((profile_by_employee.get(owner).knowledge_loss_probability for owner in owners if profile_by_employee.get(owner)), default=0)
            risk = self._clip(max_owner_share * 38 + (100 - coverage) * 0.28 + (100 - redundancy) * 0.22 + owner_risk * 0.42)
            heatmap.append(
                OrganizationalMemoryHeatmapPoint(
                    department=department,
                    system=system,
                    expertise_concentration=round(max_owner_share * 100, 2),
                    documentation_coverage=round(coverage, 2),
                    redundancy_score=round(self._clip(redundancy), 2),
                    knowledge_loss_risk=round(risk, 2),
                    priority=self._severity(risk),
                )
            )
        return sorted(heatmap, key=lambda item: item.knowledge_loss_risk, reverse=True)[:24]

    def _onboarding_roadmaps(self, target_role: str, documents: list[GeneratedKnowledgeDocument], profiles: list[ExpertiseProfile]) -> list[OnboardingRoadmap]:
        top_profile = profiles[0] if profiles else None
        docs = documents[:3]
        roadmaps: list[OnboardingRoadmap] = []
        for doc in docs:
            roadmaps.append(
                OnboardingRoadmap(
                    role=target_role,
                    focus_area=doc.systems[0] if doc.systems else doc.title,
                    steps=[
                        f"Read {doc.title} and validate architecture vocabulary.",
                        f"Shadow {doc.owner} during one operational workflow review.",
                        "Run a guided incident simulation and record unresolved questions.",
                        "Create a backup-owner checklist and update the generated SOP.",
                    ],
                    estimated_days_saved=round(float(np.clip(4 + doc.coverage_score / 12 + doc.source_count * 1.2, 5, 28)), 2),
                    confidence=doc.confidence,
                )
            )
        if top_profile:
            roadmaps.append(
                OnboardingRoadmap(
                    role=target_role,
                    focus_area=f"{top_profile.employee_name} expertise transfer",
                    steps=[
                        f"Map {', '.join(top_profile.top_expertise[:4])} into role-specific exercises.",
                        "Schedule two paired troubleshooting sessions.",
                        "Confirm backup ownership with a manager-reviewed readiness checklist.",
                    ],
                    estimated_days_saved=round(float(np.clip(top_profile.expertise_score / 5, 6, 24)), 2),
                    confidence=top_profile.confidence,
                )
            )
        return roadmaps[:5]

    def _recommendations(
        self,
        profiles: list[ExpertiseProfile],
        documents: list[GeneratedKnowledgeDocument],
        heatmap: list[OrganizationalMemoryHeatmapPoint],
    ) -> list[KnowledgeTransferRecommendation]:
        recommendations: list[KnowledgeTransferRecommendation] = []
        for profile in profiles[:3]:
            if profile.knowledge_loss_probability >= 50:
                recommendations.append(
                    KnowledgeTransferRecommendation(
                        title=f"Protect {profile.employee_name} critical expertise",
                        category="session",
                        priority=self._severity(profile.knowledge_loss_probability),
                        action=f"Run a recorded knowledge-transfer session for {', '.join(profile.owned_systems[:3]) or 'critical systems'} with two backup owners.",
                        expected_impact=f"Reduces operational disruption risk from {profile.operational_disruption_risk:.0f}% by increasing redundancy and handoff readiness.",
                        affected_employees=[profile.employee_name],
                        target_systems=profile.owned_systems,
                        confidence=profile.confidence,
                    )
                )
        for doc in documents[:2]:
            if doc.coverage_score < 70:
                recommendations.append(
                    KnowledgeTransferRecommendation(
                        title=f"Expand {doc.title}",
                        category="documentation",
                        priority="high",
                        action=f"Add rollback, validation, incident triage, and architecture-decision sections to {doc.title}.",
                        expected_impact="Improves onboarding readiness and reduces single-owner dependency.",
                        affected_employees=[doc.owner],
                        target_systems=doc.systems,
                        confidence=doc.confidence,
                    )
                )
        for item in heatmap[:2]:
            if item.knowledge_loss_risk >= 55:
                recommendations.append(
                    KnowledgeTransferRecommendation(
                        title=f"Create backup ownership for {item.system}",
                        category="backup_owner",
                        priority=item.priority,
                        action=f"Assign cross-training owners in {item.department} and verify runbook execution for {item.system}.",
                        expected_impact=f"Improves redundancy from {item.redundancy_score:.0f}% and lowers concentration risk.",
                        affected_employees=[],
                        target_systems=[item.system],
                        confidence=0.84,
                    )
                )
        return recommendations[:8]

    def _alerts(self, profiles: list[ExpertiseProfile], heatmap: list[OrganizationalMemoryHeatmapPoint]) -> list[KnowledgeRiskAlert]:
        alerts: list[KnowledgeRiskAlert] = []
        for profile in profiles[:5]:
            if profile.knowledge_loss_probability >= 48:
                alerts.append(
                    KnowledgeRiskAlert(
                        title=f"{profile.employee_name} knowledge-loss risk",
                        severity=self._severity(profile.knowledge_loss_probability),
                        probability=profile.knowledge_loss_probability,
                        impact=f"{profile.employee_name} holds {', '.join(profile.owned_systems[:3]) or 'critical workflow'} knowledge with {profile.documentation_coverage:.0f}% documentation coverage.",
                        recommendation=f"Initiate knowledge-transfer and backup-owner creation for {profile.employee_name}.",
                    )
                )
        for item in heatmap[:5]:
            if item.knowledge_loss_risk >= 58:
                alerts.append(
                    KnowledgeRiskAlert(
                        title=f"{item.system} organizational-memory concentration",
                        severity=item.priority,
                        probability=item.knowledge_loss_risk,
                        impact=f"{item.department} has {item.expertise_concentration:.0f}% expertise concentration and {item.documentation_coverage:.0f}% documentation coverage.",
                        recommendation=f"Generate SOP coverage and cross-train backup owners for {item.system}.",
                    )
                )
        return alerts[:10]

    def _executive_insights(
        self,
        profiles: list[ExpertiseProfile],
        heatmap: list[OrganizationalMemoryHeatmapPoint],
        documents: list[GeneratedKnowledgeDocument],
    ) -> list[str]:
        if not profiles:
            return ["No knowledge signals were available for analysis."]
        top = profiles[0]
        insight = [
            f"{top.employee_name} is the highest knowledge-loss risk owner at {top.knowledge_loss_probability:.0f}% across {', '.join(top.owned_systems[:3]) or 'critical workflows'}.",
            f"Knowledge graph analysis found {len([profile for profile in profiles if profile.ownership_concentration >= 65])} concentrated expertise owner(s) requiring backup coverage.",
            f"Auto-documentation generated {len(documents)} SOP or architecture artifact(s) from chats, meetings, code, and support signals.",
            f"{heatmap[0].system if heatmap else 'Enterprise workflow'} is the highest organizational-memory heatmap risk area.",
            "The pipeline combines TF-IDF expertise extraction, NetworkX graph centrality, Neo4j-compatible graph export, RandomForest risk forecasting, and dynamic documentation generation.",
        ]
        return insight

    def _summary(
        self,
        sources: list[KnowledgeSourceSignal],
        profiles: list[ExpertiseProfile],
        graph_nodes: list[KnowledgeGraphNode],
        graph_edges: list[KnowledgeGraphEdge],
        documents: list[GeneratedKnowledgeDocument],
    ) -> KnowledgeLossSummary:
        avg_doc = mean(profile.documentation_coverage for profile in profiles) if profiles else 0
        avg_risk = mean(profile.knowledge_loss_probability for profile in profiles) if profiles else 0
        top = profiles[0].employee_name if profiles else "No owner"
        return KnowledgeLossSummary(
            sources_analyzed=len(sources),
            experts_identified=len(profiles),
            graph_nodes=len(graph_nodes),
            graph_edges=len(graph_edges),
            high_risk_dependencies=sum(1 for profile in profiles if profile.knowledge_loss_probability >= 55),
            generated_documents=len(documents),
            average_documentation_coverage=round(avg_doc, 2),
            knowledge_loss_risk=round(avg_risk, 2),
            top_risk_owner=top,
        )

    @staticmethod
    def _summarize_sources(sources: list[KnowledgeSourceSignal]) -> str:
        texts = [source.content for source in sources]
        if not texts:
            return "No source text available."
        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
            matrix = vectorizer.fit_transform(texts)
            centroid = np.asarray(matrix.mean(axis=0))
            scores = cosine_similarity(matrix, centroid).ravel()
            top_index = int(np.argmax(scores))
            text = texts[top_index]
        except ValueError:
            text = texts[0]
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return " ".join(sentences[:2])[:700]

    @staticmethod
    def _transfer_actions(employee_name: str, systems: list[str], skills: list[str], loss: float, coverage: float) -> list[str]:
        actions = [
            f"Record {employee_name} explaining {systems[0] if systems else 'critical workflow'} ownership and failure modes.",
            f"Create backup-owner drills for {', '.join(skills[:3]) or 'core expertise'}.",
        ]
        if loss >= 65:
            actions.append("Schedule immediate manager-reviewed knowledge-transfer workshop.")
        if coverage < 55:
            actions.append("Generate SOP sections for rollback, validation, escalation, and known failure patterns.")
        return actions

    def _scenario_variant(self, payload: KnowledgeLossRequest, attrition_delta: float, doc_delta: float, handoff_delta: float) -> KnowledgeLossRequest:
        return payload.model_copy(
            update={
                "sources": [
                    source.model_copy(
                        update={
                            "attrition_risk": self._clip01(source.attrition_risk + attrition_delta),
                            "documentation_quality": self._clip01(source.documentation_quality + doc_delta),
                            "handoff_readiness": self._clip01(source.handoff_readiness + handoff_delta),
                            "last_updated_days": min(730, source.last_updated_days + 6),
                        }
                    )
                    for source in (payload.sources or self.default_request().sources)
                ]
            }
        )

    def _persist_graph(self, nodes: list[KnowledgeGraphNode], edges: list[KnowledgeGraphEdge]) -> None:
        GRAPH_PATH.write_text(
            json.dumps(
                {
                    "store": "neo4j_compatible_export",
                    "nodes": [node.model_dump(mode="json") for node in nodes],
                    "edges": [edge.model_dump(mode="json") for edge in edges],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload) + "\n")

    @staticmethod
    def _clip(value: float, lower: float = 0, upper: float = 100) -> float:
        return float(np.clip(value, lower, upper))

    @staticmethod
    def _clip01(value: float) -> float:
        return float(np.clip(value, 0, 1))

    @staticmethod
    def _severity(score: float) -> KnowledgePriority:
        if score >= 78:
            return "critical"
        if score >= 58:
            return "high"
        if score >= 36:
            return "medium"
        return "low"

    @staticmethod
    def _slug(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or "unknown"

    @staticmethod
    def default_request() -> KnowledgeLossRequest:
        return KnowledgeLossRequest(
            sources=[
                KnowledgeSourceSignal(
                    source_id="klp-001",
                    title="Kubernetes Production Recovery Discussion",
                    source_type="meeting",
                    employee_id="emp-bianca",
                    employee_name="Bianca Shah",
                    department="Platform",
                    team="Infrastructure Reliability",
                    role="Senior DevOps Reliability Engineer",
                    content="Bianca explained the Kubernetes platform rollback sequence, ingress failover, Helm release validation, Redis stream recovery, and production cluster node-drain process after the checkout outage.",
                    systems=["Kubernetes Platform", "Redis Stream", "Deployment Pipeline"],
                    skills=["kubernetes", "deployment", "incident response", "redis"],
                    contribution_count=22,
                    incident_resolutions=8,
                    docs_authored=1,
                    commit_count=74,
                    meeting_mentions=11,
                    attrition_risk=0.72,
                    seniority=0.92,
                    documentation_quality=0.38,
                    last_updated_days=48,
                    business_criticality=0.96,
                    redundancy_count=0,
                    handoff_readiness=0.22,
                    onboarding_relevance=0.88,
                ),
                KnowledgeSourceSignal(
                    source_id="klp-002",
                    title="Model Registry Release Notes",
                    source_type="documentation",
                    employee_id="emp-devika",
                    employee_name="Devika Nair",
                    department="AI",
                    team="Model Platform",
                    role="ML Platform Lead",
                    content="Devika documented the model registry promotion workflow, MLOps rollback criteria, feature-store lineage checks, and inference service validation for regulated model deployments.",
                    systems=["Model Registry", "RAG Assistant"],
                    skills=["mlops", "rag", "deployment", "security"],
                    contribution_count=18,
                    incident_resolutions=4,
                    docs_authored=5,
                    commit_count=48,
                    meeting_mentions=6,
                    attrition_risk=0.28,
                    seniority=0.84,
                    documentation_quality=0.78,
                    last_updated_days=9,
                    business_criticality=0.86,
                    redundancy_count=2,
                    handoff_readiness=0.72,
                    onboarding_relevance=0.91,
                ),
                KnowledgeSourceSignal(
                    source_id="klp-003",
                    title="Security Gateway Incident Ticket",
                    source_type="support",
                    employee_id="emp-aarav",
                    employee_name="Aarav Mehta",
                    department="Engineering",
                    team="Backend Platform",
                    role="Principal Backend Engineer",
                    content="Aarav resolved privileged token rotation, FastAPI gateway throttling, PostgreSQL audit queries, and zero trust session validation during the admin-export incident.",
                    systems=["Security Gateway", "PostgreSQL Cluster"],
                    skills=["fastapi", "security", "postgresql", "incident response"],
                    contribution_count=16,
                    incident_resolutions=6,
                    docs_authored=2,
                    commit_count=65,
                    meeting_mentions=7,
                    attrition_risk=0.46,
                    seniority=0.88,
                    documentation_quality=0.55,
                    last_updated_days=31,
                    business_criticality=0.9,
                    redundancy_count=1,
                    handoff_readiness=0.46,
                    onboarding_relevance=0.76,
                ),
                KnowledgeSourceSignal(
                    source_id="klp-004",
                    title="Frontend Dashboard Architecture Review",
                    source_type="design",
                    employee_id="emp-nina",
                    employee_name="Nina Kapoor",
                    department="Experience",
                    team="Enterprise UI",
                    role="Design Systems Engineer",
                    content="Nina described the Next.js dashboard composition, executive chart patterns, accessibility constraints, client-side stream handling, and reusable enterprise panel layout.",
                    systems=["Executive Dashboard"],
                    skills=["frontend", "deployment", "documentation"],
                    contribution_count=12,
                    incident_resolutions=1,
                    docs_authored=4,
                    commit_count=38,
                    meeting_mentions=5,
                    attrition_risk=0.18,
                    seniority=0.72,
                    documentation_quality=0.82,
                    last_updated_days=6,
                    business_criticality=0.64,
                    redundancy_count=3,
                    handoff_readiness=0.78,
                    onboarding_relevance=0.83,
                ),
                KnowledgeSourceSignal(
                    source_id="klp-005",
                    title="Payment API Jira Escalation",
                    source_type="jira",
                    employee_id="emp-rina",
                    employee_name="Rina Shah",
                    department="Quality",
                    team="Release Quality",
                    role="QA Automation Lead",
                    content="Rina captured payment API regression patterns, test automation rollback checks, deployment gate criteria, and known failure signatures for checkout release validation.",
                    systems=["Payment API", "Deployment Pipeline"],
                    skills=["incident response", "deployment", "fastapi"],
                    contribution_count=14,
                    incident_resolutions=3,
                    docs_authored=3,
                    commit_count=28,
                    meeting_mentions=4,
                    attrition_risk=0.21,
                    seniority=0.7,
                    documentation_quality=0.74,
                    last_updated_days=12,
                    business_criticality=0.78,
                    redundancy_count=2,
                    handoff_readiness=0.69,
                    onboarding_relevance=0.74,
                ),
            ]
        )


knowledge_loss_service = KnowledgeLossService()
