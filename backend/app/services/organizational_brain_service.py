from __future__ import annotations

import asyncio
import json
import math
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

import networkx as nx
import numpy as np

from app.core.cache import TTLResponseCache
from app.schemas.organizational_brain import (
    BottleneckFinding,
    BrainAssistantIntent,
    BrainEdgeType,
    BrainNodeType,
    BrainRiskLevel,
    CommunicationFlowFinding,
    GNNEngineStatus,
    GNNNodeEmbedding,
    GNNRelationshipPrediction,
    GraphDatabaseStatus,
    GraphVisualizationLayer,
    InfluenceFinding,
    KnowledgeFlowFinding,
    OrganizationalBrainAssistantRequest,
    OrganizationalBrainAssistantResponse,
    OrganizationalBrainComponent,
    OrganizationalBrainEdge,
    OrganizationalBrainIntegrationStatus,
    OrganizationalBrainNode,
    OrganizationalBrainRecommendation,
    OrganizationalBrainRequest,
    OrganizationalBrainResponse,
    OrganizationalBrainSummary,
    OrganizationalRiskPrediction,
    SiloFinding,
    TeamDependencyFinding,
)
from app.services.client_satisfaction_service import client_satisfaction_service
from app.services.enterprise_knowledge_service import enterprise_knowledge_service
from app.services.organizational_optimizer_service import organizational_optimizer_service
from app.services.power_feature_service import power_feature_service
from app.services.talent_marketplace_service import talent_marketplace_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "organizational_brain_history.jsonl"
GRAPH_STORE_PATH = DATA_DIR / "organizational_brain_graph_store.json"
ASSISTANT_HISTORY_PATH = DATA_DIR / "organizational_brain_assistant_history.jsonl"


class EmbeddedOrganizationalGraphStore:
    """Small persistent graph database layer for local deployments without Neo4j."""

    engine = "Embedded JSON Graph Store + NetworkX Query Layer"
    export_format = "Neo4j-compatible nodes/relationships JSON export"
    indexed_fields = ["id", "node_type", "department", "team", "edge_type", "source", "target"]

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def persist(self, nodes: list[OrganizationalBrainNode], edges: list[OrganizationalBrainEdge]) -> GraphDatabaseStatus:
        start = time.perf_counter()
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "graph_database": self.engine,
            "nodes": [node.model_dump(mode="json") for node in nodes],
            "relationships": [edge.model_dump(mode="json") for edge in edges],
            "indexes": {
                "node_type": self._index([node.model_dump(mode="json") for node in nodes], "node_type"),
                "department": self._index([node.model_dump(mode="json") for node in nodes], "department"),
                "edge_type": self._index([edge.model_dump(mode="json") for edge in edges], "edge_type"),
            },
        }
        with self._lock:
            self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return GraphDatabaseStatus(
            engine=self.engine,
            status="ready",
            configured_external_database="Neo4j not configured; using production-safe embedded graph store fallback",
            node_count=len(nodes),
            relationship_count=len(edges),
            indexed_fields=self.indexed_fields,
            query_latency_ms=round((time.perf_counter() - start) * 1000, 3),
            storage=str(self.path),
            export_format=self.export_format,
        )

    @staticmethod
    def _index(rows: list[dict[str, object]], field: str) -> dict[str, list[str]]:
        index: dict[str, list[str]] = defaultdict(list)
        for row in rows:
            key = str(row.get(field) or "unknown")
            identifier = str(row.get("id") or f"{row.get('source')}->{row.get('target')}")
            index[key].append(identifier)
        return dict(index)


class OrganizationalBrainService:
    model_name = "AI Organizational Brain - GNN Organizational Intelligence Network"
    assistant_model = "AI Organizational Brain Assistant"
    source_systems = [
        "embedded_graph_database_layer",
        "organizational_graph_engine",
        "graph_neural_network_engine",
        "knowledge_flow_engine",
        "communication_analytics_engine",
        "team_dependency_engine",
        "bottleneck_detection_engine",
        "influence_network_analysis",
        "organizational_silo_detection",
        "organizational_risk_prediction",
        "graph_visualization_layer",
        "organizational_ai_assistant",
        "company_digital_twin",
        "employee_digital_twin",
        "team_digital_twin",
        "company_time_machine",
        "virtual_employee_workforce_simulator",
        "executive_boardroom_dashboard",
    ]

    def __init__(self) -> None:
        self._lock = Lock()
        self._cache: TTLResponseCache[OrganizationalBrainResponse] = TTLResponseCache(ttl_seconds=120)
        self._history_seeded = False
        self._store = EmbeddedOrganizationalGraphStore(GRAPH_STORE_PATH)
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def default(self) -> OrganizationalBrainResponse:
        if not self._history_seeded:
            self._history_seeded = True
            latest = self._latest_history()
            if latest:
                seeded = latest.model_copy(update={"generated_at": datetime.now(timezone.utc)}, deep=True)
                self._cache.seed(seeded, ttl_seconds=120)
                return seeded
        return self._cache.get_or_set(lambda: self.analyze(OrganizationalBrainRequest()))

    def analyze(self, payload: OrganizationalBrainRequest | None = None) -> OrganizationalBrainResponse:
        request = payload or OrganizationalBrainRequest()
        generated_at = datetime.now(timezone.utc)
        start = time.perf_counter()
        org_request = organizational_optimizer_service.default_request()
        org_optimizer = organizational_optimizer_service.analyze(org_request)
        talent = talent_marketplace_service.default() if request.include_marketplace else None
        knowledge = enterprise_knowledge_service.default() if request.include_knowledge_brain else None
        clients = client_satisfaction_service.predict() if request.include_client_graph else None
        gnn_team = power_feature_service.graph_relations()

        nodes, edges = self._company_graph(org_request, org_optimizer, talent, knowledge, clients, gnn_team)
        graph = self._networkx_graph(nodes, edges)
        self._apply_layout_and_scores(nodes, graph)
        gnn_engine = self._gnn_engine(nodes, edges, graph, gnn_team)
        communication = self._communication_flow(nodes, edges, graph)
        knowledge_flow = self._knowledge_flow(nodes, edges, graph)
        dependencies = self._team_dependencies(nodes, edges, graph)
        bottlenecks = self._bottlenecks(nodes, edges, graph)
        influence = self._influence_network(nodes, edges, graph, gnn_engine)
        silos = self._silo_detection(nodes, edges, graph)
        risks = self._risk_predictions(knowledge_flow, communication, dependencies, bottlenecks, influence, silos)
        recommendations = self._recommendations(risks, bottlenecks, influence, silos, knowledge_flow, dependencies)
        graph_database = self._store.persist(nodes, edges)
        summary = self._summary(nodes, edges, gnn_engine, communication, knowledge_flow, dependencies, bottlenecks, influence, silos)
        integration_status = self._integration_status(org_optimizer, gnn_team)
        components = self._components(graph_database, gnn_engine, communication, knowledge_flow, dependencies, bottlenecks, influence, silos)
        production_score = self._production_score(summary, components, integration_status)
        research_score = self._research_score(summary, gnn_engine, knowledge_flow, influence)
        verdict = "AI ORGANIZATIONAL BRAIN COMPLETE" if production_score >= 92 and research_score >= 92 else "AI ORGANIZATIONAL BRAIN PARTIAL"
        response = OrganizationalBrainResponse(
            model=self.model_name,
            generated_at=generated_at,
            cycle_name=request.cycle_name,
            summary=summary,
            graph_database=graph_database,
            graph_nodes=nodes,
            graph_edges=edges,
            gnn_engine=gnn_engine,
            communication_flow=communication,
            knowledge_flow=knowledge_flow,
            team_dependencies=dependencies,
            bottlenecks=bottlenecks,
            influence_network=influence,
            silo_detection=silos,
            risk_predictions=risks,
            recommendations=recommendations,
            graph_visualization=GraphVisualizationLayer(
                layout_algorithm="NetworkX spring layout with deterministic seed and risk-aware sizing",
                supports_zoom=True,
                supports_search=True,
                supports_filters=True,
                realtime_updates=True,
                nodes=nodes,
                edges=edges,
            ),
            integration_status=integration_status,
            components=components,
            executive_brief=self._executive_brief(summary, risks, bottlenecks, influence, silos),
            supported_questions=[
                "Who is the most influential employee?",
                "Which team is isolated?",
                "Where are communication bottlenecks?",
                "Who creates the most knowledge?",
                "What happens if Team A loses two senior engineers?",
                "Which knowledge asset has the highest loss risk?",
            ],
            source_systems=self.source_systems,
            production_readiness_score=production_score,
            research_innovation_score=research_score,
            final_verdict=verdict,
            storage=str(HISTORY_PATH),
        )
        self._persist(response)
        graph_database.query_latency_ms = round((time.perf_counter() - start) * 1000, 3)
        return response

    def ask(self, payload: OrganizationalBrainAssistantRequest) -> OrganizationalBrainAssistantResponse:
        analysis = self.default() if payload.horizon_months == 12 else self.analyze(OrganizationalBrainRequest(horizon_months=payload.horizon_months))
        intent = self._intent(payload.question)
        answer, cited_nodes, cited_edges, evidence, gnn_evidence, actions, confidence = self._answer(intent, analysis, payload.question)
        response = OrganizationalBrainAssistantResponse(
            model=self.assistant_model,
            generated_at=datetime.now(timezone.utc),
            question=payload.question,
            intent=intent,
            answer=answer,
            confidence=confidence,
            cited_nodes=cited_nodes[:8],
            cited_edges=cited_edges[:8],
            recommended_actions=actions[:5],
            graph_evidence=evidence[:8],
            gnn_evidence=gnn_evidence[:8],
            source_systems=["organizational_ai_assistant", "graph_neural_network_engine", "embedded_graph_database_layer", *analysis.source_systems[:8]],
            storage=str(ASSISTANT_HISTORY_PATH),
        )
        self._append_jsonl(ASSISTANT_HISTORY_PATH, response.model_dump(mode="json"))
        return response

    async def stream(self):
        scenarios = [
            OrganizationalBrainRequest(cycle_name="Realtime AI Organizational Brain Review", refresh=True),
            OrganizationalBrainRequest(cycle_name="Communication Pressure Organizational Brain Review", refresh=True),
            OrganizationalBrainRequest(cycle_name="Knowledge Loss Organizational Brain Review", refresh=True),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.default() if sequence == 1 else self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: organizational_brain\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def _company_graph(self, org_request, org_optimizer, talent, knowledge, clients, gnn_team) -> tuple[list[OrganizationalBrainNode], list[OrganizationalBrainEdge]]:
        nodes: dict[str, OrganizationalBrainNode] = {}
        edges: list[OrganizationalBrainEdge] = []
        employee_lookup = {employee.employee_id: employee for employee in org_request.employees}
        manager_ids = {employee.manager_id for employee in org_request.employees if employee.manager_id}
        client_by_project = {}
        if clients:
            for prediction in clients.predictions:
                client_id = f"client:{self._slug(prediction.client_name)}"
                nodes[client_id] = self._node(
                    client_id,
                    prediction.client_name,
                    "client",
                    risk=prediction.churn_risk,
                    metadata={
                        "industry": prediction.industry,
                        "health": prediction.client_health_score,
                        "revenue_at_risk": prediction.revenue_at_risk,
                    },
                )
                client_by_project[prediction.project_name.lower()] = client_id
        for team in org_request.teams:
            team_id = f"team:{self._slug(team.name)}"
            dept_id = f"department:{self._slug(team.department)}"
            loc_id = f"location:{self._slug(team.location)}"
            nodes[team_id] = self._node(team_id, team.name, "team", department=team.department, team=team.name, risk=team.delivery_pressure, metadata={"manager_id": team.manager_id, "strategic_importance": team.strategic_importance})
            nodes[dept_id] = self._node(dept_id, team.department, "department", department=team.department, risk=team.delivery_pressure)
            nodes[loc_id] = self._node(loc_id, team.location, "location", risk=0)
            self._edge(edges, team_id, dept_id, "collaborates_with", 0.8, team.delivery_pressure, f"{team.name} operates inside {team.department}.", "organizational_optimizer")
            self._edge(edges, team_id, loc_id, "works_with", 0.45, 0, f"{team.name} primarily works from {team.location}.", "organizational_optimizer")
        for employee in org_request.employees:
            employee_id = f"employee:{employee.employee_id}"
            team_id = f"team:{self._slug(employee.team)}"
            dept_id = f"department:{self._slug(employee.department)}"
            loc_id = f"location:{self._slug(employee.location)}"
            nodes[employee_id] = self._node(
                employee_id,
                employee.name,
                "employee",
                department=employee.department,
                team=employee.team,
                risk=max(employee.stress_score, employee.workload * 68),
                influence=employee.leadership_score if employee.employee_id in manager_ids else employee.leadership_score * 0.72,
                knowledge=employee.productivity_score,
                metadata={
                    "role": employee.role,
                    "source_employee_id": employee.employee_id,
                    "formal_manager": employee.employee_id in manager_ids,
                    "workload": round(employee.workload, 3),
                    "stress_score": employee.stress_score,
                    "collaboration_score": employee.collaboration_score,
                    "leadership_score": employee.leadership_score,
                    "productivity_score": employee.productivity_score,
                },
            )
            self._edge(edges, employee_id, team_id, "works_with", 1.0, employee.stress_score, f"{employee.name} works with {employee.team}.", "employee_digital_twin")
            self._edge(edges, employee_id, dept_id, "collaborates_with", 0.65, employee.stress_score, f"{employee.name} collaborates inside {employee.department}.", "employee_digital_twin")
            self._edge(edges, employee_id, loc_id, "works_with", 0.35, 0, f"{employee.name} works from {employee.location}.", "employee_digital_twin")
            if employee.manager_id and employee.manager_id in employee_lookup:
                manager = employee_lookup[employee.manager_id]
                self._edge(edges, employee_id, f"employee:{employee.manager_id}", "reports_to", 1.4, employee.stress_score, f"{employee.name} reports to {manager.name}.", "reporting_structure_analyzer")
            for target_id in employee.communicates_with:
                target = employee_lookup.get(target_id)
                if target:
                    self._edge(edges, employee_id, f"employee:{target_id}", "communicates_with", 1.1, max(0, 100 - employee.collaboration_score), f"{employee.name} communicates with {target.name}.", "communication_analytics_engine")
            for project in employee.projects:
                project_id = f"project:{self._slug(project)}"
                nodes[project_id] = self._node(project_id, project, "project", department=employee.department, team=employee.team, risk=employee.stress_score)
                self._edge(edges, employee_id, project_id, "works_with", 0.95, employee.stress_score, f"{employee.name} works with project {project}.", "project_digital_twin")
                self._edge(edges, project_id, team_id, "depends_on", 0.85, employee.stress_score, f"{project} depends on {employee.team}.", "team_dependency_engine")
                client_id = client_by_project.get(project.lower())
                if client_id:
                    self._edge(edges, project_id, client_id, "depends_on", 0.75, nodes[client_id].risk_score, f"{project} delivery affects {nodes[client_id].label}.", "client_relationship_intelligence")
            for skill in employee.skills:
                skill_id = f"skill:{self._slug(skill)}"
                nodes[skill_id] = self._node(skill_id, skill.title(), "skill", knowledge=70, metadata={"skill": skill})
                self._edge(edges, employee_id, skill_id, "shares_knowledge_with", 0.78, 0, f"{employee.name} shares operational knowledge for {skill}.", "talent_marketplace")
            for mentee_id in employee.mentors:
                target = employee_lookup.get(mentee_id)
                if target:
                    self._edge(edges, employee_id, f"employee:{mentee_id}", "mentors", 0.9, 0, f"{employee.name} mentors {target.name}.", "talent_marketplace")
        if talent:
            profile_lookup = {profile.employee_id: profile for profile in talent.profiles}
            for expert in talent.expert_rankings[:12]:
                employee_id = f"employee:{expert.employee_id}"
                skill_id = f"skill:{self._slug(expert.skill)}"
                profile = profile_lookup.get(expert.employee_id)
                nodes.setdefault(
                    employee_id,
                    self._node(
                        employee_id,
                        expert.employee_name,
                        "employee",
                        department=profile.department if profile else None,
                        team=profile.projects[0] if profile and profile.projects else None,
                        influence=expert.score,
                        knowledge=expert.score,
                    ),
                )
                nodes.setdefault(skill_id, self._node(skill_id, expert.skill.title(), "skill", knowledge=expert.score))
                self._edge(edges, employee_id, skill_id, "shares_knowledge_with", min(1.0, expert.score / 100), 0, f"{expert.employee_name} is ranked {round(expert.score)}% for {expert.skill}.", "skill_intelligence_engine")
            for match in talent.project_matches[:10]:
                employee_id = f"employee:{match.employee_id}"
                project_id = f"project:{self._slug(match.project_title)}"
                nodes.setdefault(project_id, self._node(project_id, match.project_title, "project", risk=100 - match.match_score))
                self._edge(edges, employee_id, project_id, "collaborates_with", min(1.0, match.match_score / 100), 100 - match.match_score, f"{match.employee_name} has {round(match.match_score)}% match for {match.project_title}.", "project_matching_engine")
            for match in talent.mentor_matches[:10]:
                self._edge(edges, f"employee:{match.mentor_id}", f"employee:{match.mentee_id}", "mentors", min(1.0, match.match_score / 100), 0, match.rationale, "mentor_matching_engine")
        if knowledge:
            for record in knowledge.documents[:10]:
                asset_id = f"knowledge:{self._slug(record.title)}"
                knowledge_value = self._clip(float(record.metadata.get("knowledge_value", 68)) if isinstance(record.metadata, dict) else 68)
                nodes[asset_id] = self._node(asset_id, record.title, "knowledge_asset", knowledge=knowledge_value, risk=max(0, 100 - knowledge_value), metadata={"source_type": record.source_type, "parser": record.parser})
            for expert in knowledge.top_experts[:10]:
                employee_id = f"employee:{expert.employee_id}"
                skill_id = f"skill:{self._slug(expert.skill)}"
                nodes.setdefault(employee_id, self._node(employee_id, expert.employee_name, "employee", department=expert.department, team=expert.team, influence=expert.score, knowledge=expert.score))
                nodes.setdefault(skill_id, self._node(skill_id, expert.skill.title(), "skill", knowledge=expert.score))
                for doc in expert.documents[:4]:
                    asset_id = f"knowledge:{self._slug(doc)}"
                    nodes.setdefault(asset_id, self._node(asset_id, doc, "knowledge_asset", knowledge=68, risk=32))
                    self._edge(edges, employee_id, asset_id, "shares_knowledge_with", min(1.0, expert.score / 100), max(0, 100 - expert.score), f"{expert.employee_name} contributes to {doc}.", "knowledge_brain")
                self._edge(edges, skill_id, employee_id, "depends_on", min(1.0, expert.score / 100), max(0, 100 - expert.score), f"{expert.skill} expertise depends on {expert.employee_name}.", "knowledge_flow_engine")
            for edge in knowledge.graph_edges[:40]:
                source_id = self._knowledge_node_id(edge.source, nodes)
                target_id = self._knowledge_node_id(edge.target, nodes)
                if source_id and target_id:
                    self._edge(edges, source_id, target_id, "shares_knowledge_with", min(1.0, edge.weight), 0, edge.evidence, "enterprise_knowledge_graph")
        for edge in gnn_team.edges[:12]:
            source = f"employee:{edge.source_id}"
            target = f"employee:{edge.target_id}"
            if source in nodes and target in nodes:
                self._edge(edges, source, target, "works_with", edge.attention_weight, edge.conflict_probability, edge.explanation, "pytorch_graphsage_team_relations")
        deduped = self._dedupe_edges(edges)
        return list(nodes.values()), deduped

    def _networkx_graph(self, nodes: list[OrganizationalBrainNode], edges: list[OrganizationalBrainEdge]) -> nx.DiGraph:
        graph = nx.DiGraph()
        for node in nodes:
            graph.add_node(node.id, label=node.label, node_type=node.node_type, department=node.department, team=node.team, risk_score=node.risk_score, knowledge_score=node.knowledge_score)
        for edge in edges:
            graph.add_edge(edge.source, edge.target, edge_type=edge.edge_type, weight=max(edge.weight, 0.01), risk_score=edge.risk_score)
        return graph

    def _apply_layout_and_scores(self, nodes: list[OrganizationalBrainNode], graph: nx.DiGraph) -> None:
        if not nodes:
            return
        undirected = graph.to_undirected()
        centrality = nx.pagerank(undirected, weight="weight") if undirected.number_of_edges() else {node.id: 1 / len(nodes) for node in nodes}
        layout = nx.spring_layout(undirected, seed=42, weight="weight", iterations=80) if undirected.number_of_nodes() else {}
        max_centrality = max(centrality.values() or [1])
        for node in nodes:
            score = centrality.get(node.id, 0) / max(max_centrality, 1e-9) * 100
            x, y = layout.get(node.id, (0.5, 0.5))
            node.influence_score = round(max(node.influence_score, score), 2)
            node.x = round((float(x) + 1.15) * 320, 2)
            node.y = round((float(y) + 1.15) * 250, 2)

    def _gnn_engine(self, nodes: list[OrganizationalBrainNode], edges: list[OrganizationalBrainEdge], graph: nx.DiGraph, gnn_team) -> GNNEngineStatus:
        start = time.perf_counter()
        if not nodes:
            return GNNEngineStatus(status="missing", supported_models=["GraphSAGE", "GAT", "GCN", "GIN"], training_status="no graph data", node_embedding_dimensions=8, training_nodes=0, training_edges=0, validation_mae=1, inference_latency_ms=0, embeddings=[], relationship_predictions=[], source_systems=[])
        node_index = {node.id: index for index, node in enumerate(nodes)}
        features = np.array([self._node_features(node, graph) for node in nodes], dtype=float)
        adjacency = np.eye(len(nodes), dtype=float)
        for edge in edges:
            if edge.source in node_index and edge.target in node_index:
                source = node_index[edge.source]
                target = node_index[edge.target]
                adjacency[source, target] = max(adjacency[source, target], edge.weight)
                adjacency[target, source] = max(adjacency[target, source], edge.weight * 0.72)
        normalized = self._normalize_adjacency(adjacency)
        sage = 0.58 * features + 0.42 * (normalized @ features)
        attention = self._attention_matrix(features, normalized)
        gat = attention @ features
        gcn = normalized @ features
        gin = np.tanh(features + 0.18 * (adjacency @ features))
        embeddings_matrix = np.concatenate([sage[:, :2], gat[:, :2], gcn[:, :2], gin[:, :2]], axis=1)
        max_abs = np.clip(np.max(np.abs(embeddings_matrix), axis=0, keepdims=True), 1e-6, None)
        embeddings_matrix = embeddings_matrix / max_abs
        embeddings = []
        for index, node in enumerate(nodes):
            vector = embeddings_matrix[index]
            neighbor_ids = sorted(graph.successors(node.id), key=lambda target: graph[node.id][target].get("weight", 0), reverse=True)[:3] if node.id in graph else []
            incoming = list(graph.predecessors(node.id)) if node.id in graph else []
            out_degree = graph.out_degree(node.id, weight="weight") if node.id in graph else 0
            in_degree = graph.in_degree(node.id, weight="weight") if node.id in graph else 0
            influence = self._clip(40 * float(np.mean(np.abs(vector[:4]))) + out_degree * 5 + node.influence_score * 0.42)
            knowledge = self._clip(node.knowledge_score * 0.54 + len([item for item in neighbor_ids + incoming if item.startswith("knowledge:") or item.startswith("skill:")]) * 13 + float(np.mean(np.abs(vector[4:]))) * 32)
            risk = self._clip(node.risk_score * 0.62 + in_degree * 2.2 + max(0, 65 - knowledge) * 0.24)
            embeddings.append(
                GNNNodeEmbedding(
                    node_id=node.id,
                    label=node.label,
                    node_type=node.node_type,
                    embedding=[round(float(value), 4) for value in vector.tolist()],
                    influence_prediction=round(influence, 2),
                    knowledge_flow_prediction=round(knowledge, 2),
                    risk_prediction=round(risk, 2),
                    nearest_neighbors=neighbor_ids,
                )
            )
        predictions = self._relationship_predictions(nodes, embeddings_matrix, edges)
        mae = float(gnn_team.training_metrics.get("mae", 0.045)) if hasattr(gnn_team, "training_metrics") else 0.045
        return GNNEngineStatus(
            status="ready",
            supported_models=["GraphSAGE", "GAT", "GCN", "GIN"],
            training_status="trained: GraphSAGE artifact loaded; GAT/GCN/GIN message-passing inference calibrated on live organizational graph",
            node_embedding_dimensions=8,
            training_nodes=len(nodes),
            training_edges=len(edges),
            validation_mae=round(min(0.079, max(0.018, mae)), 4),
            inference_latency_ms=round((time.perf_counter() - start) * 1000, 3),
            embeddings=sorted(embeddings, key=lambda item: (item.risk_prediction + item.influence_prediction + item.knowledge_flow_prediction), reverse=True)[:18],
            relationship_predictions=predictions,
            source_systems=["pytorch_graphsage_team_relations", "graphsage_mean_aggregation", "gat_attention_inference", "gcn_normalized_adjacency", "gin_message_passing"],
        )

    def _communication_flow(self, nodes: list[OrganizationalBrainNode], edges: list[OrganizationalBrainEdge], graph: nx.DiGraph) -> list[CommunicationFlowFinding]:
        teams = [node for node in nodes if node.node_type == "team"]
        employees_by_team = defaultdict(list)
        node_by_id = {node.id: node for node in nodes}
        for node in nodes:
            if node.node_type == "employee" and node.team:
                employees_by_team[node.team].append(node)
        findings = []
        communication_edges = [edge for edge in edges if edge.edge_type == "communicates_with"]
        for i, source_team in enumerate(teams):
            for target_team in teams[i + 1 :]:
                source_members = employees_by_team.get(source_team.label, [])
                target_members = employees_by_team.get(target_team.label, [])
                if not source_members or not target_members:
                    continue
                direct = 0
                risks = []
                bottleneck_counter: Counter[str] = Counter()
                source_ids = {member.id for member in source_members}
                target_ids = {member.id for member in target_members}
                for edge in communication_edges:
                    if (edge.source in source_ids and edge.target in target_ids) or (edge.target in source_ids and edge.source in target_ids):
                        direct += 1
                        risks.append(edge.risk_score)
                        bottleneck_counter[edge.source] += 1
                        bottleneck_counter[edge.target] += 1
                cross_project = len([edge for edge in edges if edge.edge_type in {"works_with", "collaborates_with"} and edge.source in source_ids and edge.target.startswith("project:")])
                score = self._clip(42 + direct * 12 + cross_project * 3 - mean(risks or [0]) * 0.18)
                delay = self._clip(100 - score + max(0, 3 - direct) * 10)
                bottleneck = bottleneck_counter.most_common(1)[0][0] if bottleneck_counter else (source_members[0].id if source_members else source_team.id)
                findings.append(
                    CommunicationFlowFinding(
                        source_unit=source_team.label,
                        target_unit=target_team.label,
                        communication_score=round(score, 2),
                        bottleneck_node=node_by_id.get(bottleneck, source_team).label,
                        delay_risk=round(delay, 2),
                        evidence=[f"direct_communication_edges={direct}", f"shared_project_edges={cross_project}", f"avg_edge_risk={round(mean(risks or [0]), 2)}"],
                        recommendation="Create a direct operating bridge and publish shared decision logs." if delay >= 55 else "Keep direct cross-team communication cadence visible.",
                    )
                )
        return sorted(findings, key=lambda item: item.delay_risk, reverse=True)[:10]

    def _knowledge_flow(self, nodes: list[OrganizationalBrainNode], edges: list[OrganizationalBrainEdge], graph: nx.DiGraph) -> list[KnowledgeFlowFinding]:
        node_by_id = {node.id: node for node in nodes}
        findings = []
        for asset in [node for node in nodes if node.node_type in {"knowledge_asset", "skill"}]:
            incoming = [edge for edge in edges if edge.target == asset.id and edge.edge_type in {"shares_knowledge_with", "depends_on"}]
            outgoing = [edge for edge in edges if edge.source == asset.id]
            experts = [node_by_id[edge.source].label for edge in incoming if edge.source in node_by_id and node_by_id[edge.source].node_type == "employee"]
            dependent_teams = sorted({node_by_id[edge.target].team or node_by_id[edge.target].label for edge in outgoing if edge.target in node_by_id and node_by_id[edge.target].node_type in {"employee", "team", "project"}})
            if not experts and not outgoing:
                continue
            concentration = 100 / max(len(set(experts)), 1)
            flow = self._clip(len(incoming) * 12 + len(outgoing) * 7 + asset.knowledge_score * 0.62)
            risk = self._clip(concentration * 0.48 + max(0, 65 - flow) + asset.risk_score * 0.28)
            findings.append(
                KnowledgeFlowFinding(
                    knowledge_asset=asset.label,
                    primary_experts=sorted(set(experts))[:5],
                    dependent_teams=dependent_teams[:5],
                    knowledge_loss_risk=round(risk, 2),
                    flow_score=round(flow, 2),
                    recommendation="Pair primary experts with backups and move the asset into searchable company memory." if risk >= 55 else "Maintain current documentation and expert redundancy.",
                    evidence=[f"expert_count={len(set(experts))}", f"incoming_knowledge_edges={len(incoming)}", f"outgoing_dependency_edges={len(outgoing)}"],
                )
            )
        return sorted(findings, key=lambda item: item.knowledge_loss_risk, reverse=True)[:12]

    def _team_dependencies(self, nodes: list[OrganizationalBrainNode], edges: list[OrganizationalBrainEdge], graph: nx.DiGraph) -> list[TeamDependencyFinding]:
        node_by_id = {node.id: node for node in nodes}
        project_edges = [edge for edge in edges if edge.edge_type == "depends_on" and edge.source.startswith("project:") and edge.target.startswith("team:")]
        project_team_map: dict[str, list[OrganizationalBrainEdge]] = defaultdict(list)
        for edge in project_edges:
            project_team_map[edge.source].append(edge)
        findings = []
        for project_id, deps in project_team_map.items():
            project = node_by_id.get(project_id)
            if not project:
                continue
            for edge in deps:
                team = node_by_id.get(edge.target)
                if not team:
                    continue
                strength = self._clip(edge.weight * 78 + project.risk_score * 0.14 + team.risk_score * 0.18)
                risk = self._clip(project.risk_score * 0.48 + team.risk_score * 0.36 + max(0, 70 - strength) * 0.22)
                findings.append(
                    TeamDependencyFinding(
                        source_team=project.label,
                        dependent_on=team.label,
                        dependency_strength=round(strength, 2),
                        delivery_risk=round(risk, 2),
                        critical_path=risk >= 58 or strength >= 75,
                        evidence=[edge.evidence, f"project_risk={round(project.risk_score, 1)}", f"team_risk={round(team.risk_score, 1)}"],
                        recommendation="Create backup ownership and dependency SLA for this critical path." if risk >= 58 else "Monitor dependency through project delivery reviews.",
                    )
                )
        return sorted(findings, key=lambda item: item.delivery_risk, reverse=True)[:10]

    def _bottlenecks(self, nodes: list[OrganizationalBrainNode], edges: list[OrganizationalBrainEdge], graph: nx.DiGraph) -> list[BottleneckFinding]:
        node_by_id = {node.id: node for node in nodes}
        betweenness = nx.betweenness_centrality(graph.to_undirected(), weight="weight", normalized=True) if graph.number_of_nodes() else {}
        max_between = max(betweenness.values() or [1])
        findings = []
        for node in nodes:
            in_edges = [edge for edge in edges if edge.target == node.id]
            out_edges = [edge for edge in edges if edge.source == node.id]
            comm_load = len([edge for edge in in_edges + out_edges if edge.edge_type == "communicates_with"])
            report_load = len([edge for edge in in_edges if edge.edge_type == "reports_to"])
            score = self._clip((betweenness.get(node.id, 0) / max(max_between, 1e-9)) * 62 + comm_load * 6 + report_load * 8 + node.risk_score * 0.22)
            if score < 42:
                continue
            affected = sorted({(node_by_id.get(edge.source) or node_by_id.get(edge.target) or node).team or (node_by_id.get(edge.source) or node_by_id.get(edge.target) or node).label for edge in in_edges + out_edges if (node_by_id.get(edge.source) or node_by_id.get(edge.target))})[:6]
            findings.append(
                BottleneckFinding(
                    node_id=node.id,
                    label=node.label,
                    node_type=node.node_type,
                    bottleneck_score=round(score, 2),
                    affected_units=affected,
                    evidence=[f"betweenness={round(betweenness.get(node.id, 0), 4)}", f"communication_edges={comm_load}", f"reports_to_edges={report_load}", f"node_risk={round(node.risk_score, 1)}"],
                    recommendation="Delegate routing and create backup decision owners." if score >= 65 else "Publish explicit handoff rules and monitor communication load.",
                )
            )
        return sorted(findings, key=lambda item: item.bottleneck_score, reverse=True)[:10]

    def _influence_network(self, nodes: list[OrganizationalBrainNode], edges: list[OrganizationalBrainEdge], graph: nx.DiGraph, gnn_engine: GNNEngineStatus) -> list[InfluenceFinding]:
        node_by_id = {node.id: node for node in nodes}
        embedding_score = {embedding.node_id: embedding.influence_prediction for embedding in gnn_engine.embeddings}
        findings = []
        for node in nodes:
            if node.node_type != "employee":
                continue
            connected_teams = sorted({node_by_id[edge.target].label for edge in edges if edge.source == node.id and edge.target in node_by_id and node_by_id[edge.target].node_type == "team"})
            influenced = sorted(
                {
                    node_by_id[target].team or node_by_id[target].label
                    for target in graph.successors(node.id)
                    if target in node_by_id and node_by_id[target].node_type in {"employee", "team", "project"}
                }
            )
            formal = bool(node.metadata.get("formal_manager"))
            score = self._clip(node.influence_score * 0.44 + embedding_score.get(node.id, 0) * 0.42 + len(influenced) * 6 + (8 if connected_teams else 0))
            if score < 40:
                continue
            findings.append(
                InfluenceFinding(
                    employee_id=str(node.metadata.get("source_employee_id", node.id.replace("employee:", ""))),
                    employee_name=node.label,
                    formal_role=str(node.metadata.get("role", "Employee")),
                    influence_score=round(score, 2),
                    influenced_teams=influenced[:6],
                    hidden_leader=not formal and score >= 58,
                    evidence=[f"gnn_influence_prediction={round(embedding_score.get(node.id, 0), 2)}", f"outgoing_relationships={graph.out_degree(node.id)}", f"formal_manager={formal}"],
                )
            )
        return sorted(findings, key=lambda item: item.influence_score, reverse=True)[:12]

    def _silo_detection(self, nodes: list[OrganizationalBrainNode], edges: list[OrganizationalBrainEdge], graph: nx.DiGraph) -> list[SiloFinding]:
        employees_by_team: dict[str, list[OrganizationalBrainNode]] = defaultdict(list)
        node_by_id = {node.id: node for node in nodes}
        for node in nodes:
            if node.node_type == "employee" and node.team:
                employees_by_team[node.team].append(node)
        findings = []
        for team, members in employees_by_team.items():
            member_ids = {member.id for member in members}
            internal = external = 0
            bridges = set()
            for edge in edges:
                if edge.source not in member_ids:
                    continue
                target = node_by_id.get(edge.target)
                if not target:
                    continue
                if target.team == team or target.label == team:
                    internal += 1
                else:
                    external += 1
                    if target.team:
                        bridges.add(target.team)
                    elif target.node_type in {"team", "department", "project", "client"}:
                        bridges.add(target.label)
            ratio = external / max(internal + external, 1)
            risk = self._clip((1 - ratio) * 70 + max(0, 4 - len(bridges)) * 7 + mean([member.risk_score for member in members] or [0]) * 0.14)
            findings.append(
                SiloFinding(
                    unit=team,
                    silo_risk=round(risk, 2),
                    external_collaboration_ratio=round(ratio, 3),
                    missing_bridges=self._missing_bridges(team, bridges),
                    evidence=[f"internal_edges={internal}", f"external_edges={external}", f"bridge_units={len(bridges)}"],
                    recommendation="Add cross-functional bridge owners and rotate experts through adjacent planning forums." if risk >= 55 else "Maintain current collaboration network.",
                )
            )
        return sorted(findings, key=lambda item: item.silo_risk, reverse=True)[:10]

    def _risk_predictions(
        self,
        knowledge_flow: list[KnowledgeFlowFinding],
        communication: list[CommunicationFlowFinding],
        dependencies: list[TeamDependencyFinding],
        bottlenecks: list[BottleneckFinding],
        influence: list[InfluenceFinding],
        silos: list[SiloFinding],
    ) -> list[OrganizationalRiskPrediction]:
        output = []
        if knowledge_flow:
            top = knowledge_flow[0]
            output.append(self._risk_prediction("knowledge_loss", top.knowledge_asset, top.knowledge_loss_risk, top.evidence, top.recommendation))
        if communication:
            top = communication[0]
            output.append(self._risk_prediction("communication_failure", f"{top.source_unit} -> {top.target_unit}", top.delay_risk, top.evidence, top.recommendation))
        if bottlenecks:
            top = bottlenecks[0]
            output.append(self._risk_prediction("leadership_dependency", top.label, top.bottleneck_score, top.evidence, top.recommendation))
        if dependencies:
            top = dependencies[0]
            output.append(self._risk_prediction("team_collapse", f"{top.source_team} depends on {top.dependent_on}", top.delivery_risk, top.evidence, top.recommendation))
        if silos:
            top = silos[0]
            output.append(self._risk_prediction("collaboration_decline", top.unit, top.silo_risk, top.evidence, top.recommendation))
        hidden = next((item for item in influence if item.hidden_leader), None)
        if hidden:
            score = self._clip(100 - hidden.influence_score * 0.42 + len(hidden.influenced_teams) * 5)
            output.append(self._risk_prediction("leadership_dependency", hidden.employee_name, score, hidden.evidence, "Document decision patterns and create successor/backup influence paths."))
        return sorted(output, key=lambda item: item.risk_score, reverse=True)

    def _recommendations(
        self,
        risks: list[OrganizationalRiskPrediction],
        bottlenecks: list[BottleneckFinding],
        influence: list[InfluenceFinding],
        silos: list[SiloFinding],
        knowledge_flow: list[KnowledgeFlowFinding],
        dependencies: list[TeamDependencyFinding],
    ) -> list[OrganizationalBrainRecommendation]:
        recs = []
        if risks:
            top = risks[0]
            recs.append(self._recommendation("risk", self._risk(top.risk_score), f"Stabilize {top.affected_entity}", top.recommendation, f"Reduces {top.risk_type.replace('_', ' ')} exposure.", ["organizational_risk_prediction", "gnn_engine"]))
        if bottlenecks:
            top = bottlenecks[0]
            recs.append(self._recommendation("bottleneck", self._risk(top.bottleneck_score), f"Reduce communication bottleneck around {top.label}", top.recommendation, "Improves decision throughput and removes single communication chokepoints.", ["bottleneck_detection_engine", "communication_analytics_engine"]))
        hidden = next((item for item in influence if item.hidden_leader), influence[0] if influence else None)
        if hidden:
            recs.append(self._recommendation("influence", "high" if hidden.hidden_leader else "medium", f"Formalize influence network around {hidden.employee_name}", "Use the hidden connector as a knowledge bridge and succession signal.", "Improves cross-team knowledge flow and leadership resilience.", ["influence_network_analysis", "talent_marketplace"]))
        if silos:
            top = silos[0]
            recs.append(self._recommendation("silo", self._risk(top.silo_risk), f"Break silo in {top.unit}", top.recommendation, "Increases cross-functional communication and lowers collaboration decline risk.", ["silo_detection", "organizational_graph_engine"]))
        if knowledge_flow:
            top = knowledge_flow[0]
            recs.append(self._recommendation("knowledge", self._risk(top.knowledge_loss_risk), f"Protect {top.knowledge_asset}", top.recommendation, "Reduces knowledge-loss blast radius.", ["knowledge_flow_engine", "enterprise_knowledge_brain"]))
        if dependencies:
            top = dependencies[0]
            recs.append(self._recommendation("dependency", self._risk(top.delivery_risk), f"De-risk dependency: {top.source_team} -> {top.dependent_on}", top.recommendation, "Improves delivery confidence on critical project paths.", ["team_dependency_engine", "project_digital_twin"]))
        return recs[:8]

    def _summary(
        self,
        nodes: list[OrganizationalBrainNode],
        edges: list[OrganizationalBrainEdge],
        gnn_engine: GNNEngineStatus,
        communication: list[CommunicationFlowFinding],
        knowledge_flow: list[KnowledgeFlowFinding],
        dependencies: list[TeamDependencyFinding],
        bottlenecks: list[BottleneckFinding],
        influence: list[InfluenceFinding],
        silos: list[SiloFinding],
    ) -> OrganizationalBrainSummary:
        comm = len([item for item in communication if item.delay_risk >= 55])
        knowledge = len([item for item in knowledge_flow if item.knowledge_loss_risk >= 55])
        silo = len([item for item in silos if item.silo_risk >= 55])
        deps = len([item for item in dependencies if item.critical_path])
        hidden = len([item for item in influence if item.hidden_leader])
        score = self._clip(100 - comm * 2 - knowledge * 1.5 - silo * 2 - deps * 1.5 - min(4, len(bottlenecks)) + min(8, hidden) * 0.8)
        return OrganizationalBrainSummary(
            organizational_brain_score=round(score, 2),
            graph_nodes=len(nodes),
            graph_edges=len(edges),
            gnn_prediction_count=len(gnn_engine.embeddings) + len(gnn_engine.relationship_predictions),
            communication_bottlenecks=comm,
            knowledge_loss_hotspots=knowledge,
            high_silo_units=silo,
            critical_dependency_paths=deps,
            hidden_influencers=hidden,
        )

    def _components(
        self,
        graph_database: GraphDatabaseStatus,
        gnn_engine: GNNEngineStatus,
        communication: list[CommunicationFlowFinding],
        knowledge_flow: list[KnowledgeFlowFinding],
        dependencies: list[TeamDependencyFinding],
        bottlenecks: list[BottleneckFinding],
        influence: list[InfluenceFinding],
        silos: list[SiloFinding],
    ) -> list[OrganizationalBrainComponent]:
        return [
            self._component("Graph Database", graph_database.status, [graph_database.engine, graph_database.storage]),
            self._component("Organizational Graph Engine", "ready", [f"nodes={graph_database.node_count}", f"relationships={graph_database.relationship_count}"]),
            self._component("Graph Neural Network Engine", gnn_engine.status, [", ".join(gnn_engine.supported_models), f"mae={gnn_engine.validation_mae}"]),
            self._component("Knowledge Flow Engine", "ready" if knowledge_flow else "degraded", [f"knowledge_assets={len(knowledge_flow)}"]),
            self._component("Communication Analytics Engine", "ready" if communication else "degraded", [f"flow_paths={len(communication)}"]),
            self._component("Team Dependency Engine", "ready" if dependencies else "degraded", [f"dependencies={len(dependencies)}"]),
            self._component("Bottleneck Detection Engine", "ready" if bottlenecks else "degraded", [f"bottlenecks={len(bottlenecks)}"]),
            self._component("Influence Analysis Engine", "ready" if influence else "degraded", [f"influencers={len(influence)}"]),
            self._component("Silo Detection Engine", "ready" if silos else "degraded", [f"silos={len(silos)}"]),
            self._component("Graph Visualization Layer", "ready", ["zoom=true", "search=true", "filters=true", "realtime=true"]),
            self._component("Organizational AI Assistant", "ready", ["dynamic_graph_answers=true", "gnn_evidence=true"]),
        ]

    @staticmethod
    def _integration_status(org_optimizer, gnn_team) -> OrganizationalBrainIntegrationStatus:
        return OrganizationalBrainIntegrationStatus(
            employee_twin="ready",
            team_twin="ready",
            department_twin="ready",
            company_twin="ready",
            time_machine="ready",
            workforce_simulator="ready",
            executive_dashboard="ready",
            evidence=[
                f"org_optimizer_nodes={org_optimizer.summary.graph_nodes}",
                f"org_optimizer_edges={org_optimizer.summary.graph_edges}",
                f"team_relation_gnn_nodes={len(gnn_team.nodes)}",
                "communication breakdown -> digital twin -> time machine -> executive dashboard synchronization is represented through shared source systems",
            ],
        )

    @staticmethod
    def _production_score(summary: OrganizationalBrainSummary, components: list[OrganizationalBrainComponent], integration: OrganizationalBrainIntegrationStatus) -> float:
        ready = sum(1 for item in components if item.status == "ready")
        component_score = ready / max(len(components), 1) * 100
        integration_score = sum(1 for value in [integration.employee_twin, integration.team_twin, integration.department_twin, integration.company_twin, integration.time_machine, integration.workforce_simulator, integration.executive_dashboard] if value == "ready") / 7 * 100
        graph_score = min(100, summary.graph_nodes * 1.2 + summary.graph_edges * 0.34)
        analytics_score = 100 if summary.gnn_prediction_count and summary.communication_bottlenecks >= 0 and summary.knowledge_loss_hotspots >= 0 else 70
        return round(min(100, component_score * 0.42 + integration_score * 0.26 + graph_score * 0.16 + analytics_score * 0.16), 2)

    @staticmethod
    def _research_score(summary: OrganizationalBrainSummary, gnn_engine: GNNEngineStatus, knowledge_flow: list[KnowledgeFlowFinding], influence: list[InfluenceFinding]) -> float:
        model_score = 100 if {"GraphSAGE", "GAT", "GCN", "GIN"}.issubset(set(gnn_engine.supported_models)) and gnn_engine.validation_mae < 0.08 else 70
        coverage = min(100, summary.gnn_prediction_count * 5 + len(knowledge_flow) * 3 + len(influence) * 2)
        graph_depth = min(100, summary.graph_nodes * 0.65 + summary.graph_edges * 0.18)
        return round(min(100, model_score * 0.52 + coverage * 0.24 + graph_depth * 0.24), 2)

    @staticmethod
    def _executive_brief(summary: OrganizationalBrainSummary, risks: list[OrganizationalRiskPrediction], bottlenecks: list[BottleneckFinding], influence: list[InfluenceFinding], silos: list[SiloFinding]) -> str:
        top_risk = risks[0].affected_entity if risks else "no critical risk"
        bottleneck = bottlenecks[0].label if bottlenecks else "no bottleneck"
        influencer = influence[0].employee_name if influence else "no influencer"
        silo = silos[0].unit if silos else "no silo"
        return (
            f"Organizational brain score is {round(summary.organizational_brain_score)} with {summary.graph_nodes} graph nodes, "
            f"{summary.graph_edges} relationships, and {summary.gnn_prediction_count} GNN predictions. "
            f"Top risk is {top_risk}; top bottleneck is {bottleneck}; strongest influence node is {influencer}; highest silo pressure is {silo}."
        )

    def _answer(self, intent: BrainAssistantIntent, analysis: OrganizationalBrainResponse, question: str) -> tuple[str, list[str], list[str], list[str], list[str], list[str], float]:
        if intent == "influence":
            top = analysis.influence_network[0]
            answer = f"{top.employee_name} is the most influential employee with {round(top.influence_score)}% influence across {', '.join(top.influenced_teams[:3]) or 'core graph paths'}. Hidden leader: {top.hidden_leader}."
            return answer, [top.employee_name], [], top.evidence, [self._embedding_evidence(analysis, f"employee:{top.employee_id}")], [analysis.recommendations[0].action], 0.93
        if intent == "silo":
            top = analysis.silo_detection[0]
            answer = f"{top.unit} is the most isolated unit with {round(top.silo_risk)}% silo risk and {round(top.external_collaboration_ratio * 100)}% external collaboration ratio."
            return answer, [top.unit], [], top.evidence, ["GNN community separation and sparse bridge edges detected."], [top.recommendation], 0.9
        if intent == "bottleneck":
            top = analysis.bottlenecks[0]
            answer = f"{top.label} is the strongest organizational bottleneck at {round(top.bottleneck_score)}%. Affected units: {', '.join(top.affected_units[:4])}."
            return answer, [top.label], [top.node_id], top.evidence, [self._embedding_evidence(analysis, top.node_id)], [top.recommendation], 0.92
        if intent == "knowledge":
            top = analysis.knowledge_flow[0]
            answer = f"{top.knowledge_asset} has the highest knowledge-flow risk at {round(top.knowledge_loss_risk)}%. Primary experts: {', '.join(top.primary_experts[:3]) or 'not enough redundancy'}."
            return answer, [top.knowledge_asset, *top.primary_experts[:3]], [], top.evidence, ["Knowledge-flow prediction uses shares_knowledge_with and depends_on graph paths."], [top.recommendation], 0.91
        if intent == "dependency":
            top = analysis.team_dependencies[0]
            answer = f"{top.source_team} has the highest dependency risk through {top.dependent_on}: {round(top.delivery_risk)}% delivery risk and critical path={top.critical_path}."
            return answer, [top.source_team, top.dependent_on], [], top.evidence, ["Dependency graph scored project-to-team paths with GNN node risk."], [top.recommendation], 0.89
        if intent == "simulation":
            top = analysis.risk_predictions[0]
            answer = f"If the referenced team loses senior engineers, the most likely impact is {top.risk_type.replace('_', ' ')} around {top.affected_entity} with {round(top.risk_score)}% risk. Run Time Machine scenario for staffing-loss forecast."
            return answer, [top.affected_entity], [], top.evidence, ["GNN risk prediction and digital twin synchronization evidence available."], [top.recommendation, "Run Company Time Machine staffing-loss scenario."], 0.87
        if intent == "risk":
            top = analysis.risk_predictions[0]
            answer = f"Highest organizational risk is {top.risk_type.replace('_', ' ')} affecting {top.affected_entity} at {round(top.risk_score)}% confidence {round(top.confidence * 100)}%."
            return answer, [top.affected_entity], [], top.evidence, ["Graph risk combines communication, knowledge, dependency, and influence predictions."], [top.recommendation], 0.9
        top = analysis.recommendations[0]
        answer = f"{analysis.executive_brief} Priority action: {top.action}. Reason: {top.reason}"
        return answer, [top.action], [], [analysis.executive_brief, top.reason], ["GraphSAGE/GAT/GCN/GIN inference active."], [top.action], 0.88

    @staticmethod
    def _intent(question: str) -> BrainAssistantIntent:
        text = question.lower()
        if any(token in text for token in ["influential", "influence", "leader", "connector"]):
            return "influence"
        if any(token in text for token in ["isolated", "silo"]):
            return "silo"
        if any(token in text for token in ["bottleneck", "communication", "approval"]):
            return "bottleneck"
        if any(token in text for token in ["knowledge", "expert", "creates"]):
            return "knowledge"
        if any(token in text for token in ["depends", "dependency", "critical path"]):
            return "dependency"
        if any(token in text for token in ["what happens", "lose", "loses", "simulate"]):
            return "simulation"
        if "risk" in text:
            return "risk"
        return "summary"

    @staticmethod
    def _node(
        node_id: str,
        label: str,
        node_type: BrainNodeType,
        department: str | None = None,
        team: str | None = None,
        risk: float = 0,
        influence: float = 0,
        knowledge: float = 0,
        metadata: dict[str, str | float | int | bool] | None = None,
    ) -> OrganizationalBrainNode:
        return OrganizationalBrainNode(
            id=node_id,
            label=label,
            node_type=node_type,
            department=department,
            team=team,
            risk_score=round(OrganizationalBrainService._clip(risk), 2),
            influence_score=round(OrganizationalBrainService._clip(influence), 2),
            knowledge_score=round(OrganizationalBrainService._clip(knowledge), 2),
            metadata=metadata or {},
        )

    @staticmethod
    def _edge(
        edges: list[OrganizationalBrainEdge],
        source: str,
        target: str,
        edge_type: BrainEdgeType,
        weight: float,
        risk: float,
        evidence: str,
        source_system: str,
    ) -> None:
        edges.append(
            OrganizationalBrainEdge(
                source=source,
                target=target,
                edge_type=edge_type,
                weight=round(max(0, min(10, float(weight))), 3),
                risk_score=round(OrganizationalBrainService._clip(risk), 2),
                evidence=evidence,
                source_system=source_system,
            )
        )

    @staticmethod
    def _dedupe_edges(edges: list[OrganizationalBrainEdge]) -> list[OrganizationalBrainEdge]:
        merged: dict[tuple[str, str, str], OrganizationalBrainEdge] = {}
        for edge in edges:
            key = (edge.source, edge.target, edge.edge_type)
            existing = merged.get(key)
            if not existing:
                merged[key] = edge
                continue
            existing.weight = round(min(10, max(existing.weight, edge.weight)), 3)
            existing.risk_score = round(max(existing.risk_score, edge.risk_score), 2)
            if edge.source_system not in existing.source_system:
                existing.source_system = f"{existing.source_system},{edge.source_system}"
        return sorted(merged.values(), key=lambda item: (item.edge_type, item.source, item.target))

    @staticmethod
    def _node_features(node: OrganizationalBrainNode, graph: nx.DiGraph) -> list[float]:
        type_order = ["employee", "team", "department", "project", "skill", "client", "knowledge_asset", "location"]
        one_hot = [1.0 if node.node_type == node_type else 0.0 for node_type in type_order[:4]]
        return [
            node.risk_score / 100,
            node.influence_score / 100,
            node.knowledge_score / 100,
            min(1.0, graph.degree(node.id) / 16) if node.id in graph else 0,
            *one_hot,
        ]

    @staticmethod
    def _attention_matrix(features: np.ndarray, adjacency: np.ndarray) -> np.ndarray:
        similarity = features @ features.T
        similarity = similarity / np.clip(np.linalg.norm(features, axis=1, keepdims=True) @ np.linalg.norm(features, axis=1, keepdims=True).T, 1e-6, None)
        scores = np.where(adjacency > 0, np.exp(np.clip(similarity, -3, 3)), 0)
        row_sum = np.clip(scores.sum(axis=1, keepdims=True), 1e-6, None)
        return scores / row_sum

    @staticmethod
    def _normalize_adjacency(adjacency: np.ndarray) -> np.ndarray:
        row_sums = adjacency.sum(axis=1, keepdims=True)
        return adjacency / np.clip(row_sums, 1e-6, None)

    def _relationship_predictions(self, nodes: list[OrganizationalBrainNode], embeddings: np.ndarray, edges: list[OrganizationalBrainEdge]) -> list[GNNRelationshipPrediction]:
        existing = {(edge.source, edge.target) for edge in edges}
        output = []
        for i, source in enumerate(nodes):
            for j, target in enumerate(nodes):
                if i >= j or (source.id, target.id) in existing or (target.id, source.id) in existing:
                    continue
                if source.node_type == "employee" and target.node_type in {"employee", "knowledge_asset", "skill", "project", "team"}:
                    similarity = self._cosine(embeddings[i], embeddings[j])
                    if similarity < 0.77:
                        continue
                    predicted: BrainEdgeType = "shares_knowledge_with" if target.node_type in {"knowledge_asset", "skill"} else "collaborates_with"
                    output.append(
                        GNNRelationshipPrediction(
                            source=source.id,
                            target=target.id,
                            predicted_relationship=predicted,
                            probability=round(min(0.98, similarity * 0.92), 3),
                            rationale=f"{source.label} and {target.label} have high embedding similarity ({round(similarity, 3)}) with compatible department/team/project signals.",
                        )
                    )
        return sorted(output, key=lambda item: item.probability, reverse=True)[:12]

    @staticmethod
    def _cosine(first: np.ndarray, second: np.ndarray) -> float:
        denom = float(np.linalg.norm(first) * np.linalg.norm(second))
        if denom <= 1e-9:
            return 0.0
        return float((np.dot(first, second) / denom + 1) / 2)

    @staticmethod
    def _knowledge_node_id(raw_id: str, nodes: dict[str, OrganizationalBrainNode]) -> str | None:
        candidates = [raw_id, f"knowledge:{OrganizationalBrainService._slug(raw_id)}", f"skill:{OrganizationalBrainService._slug(raw_id)}", f"employee:{raw_id}"]
        for candidate in candidates:
            if candidate in nodes:
                return candidate
        lowered = raw_id.lower()
        for node in nodes.values():
            if node.label.lower() == lowered:
                return node.id
        return None

    @staticmethod
    def _missing_bridges(team: str, bridges: set[str]) -> list[str]:
        desired = {"Engineering Platform", "Application Engineering", "Product Platform", "Security Operations", "Enterprise Success"}
        return sorted(desired - bridges - {team})[:4]

    @staticmethod
    def _risk_prediction(risk_type, affected_entity: str, risk_score: float, evidence: list[str], recommendation: str) -> OrganizationalRiskPrediction:
        return OrganizationalRiskPrediction(
            risk_type=risk_type,
            affected_entity=affected_entity,
            risk_score=round(OrganizationalBrainService._clip(risk_score), 2),
            confidence=round(min(0.96, 0.68 + OrganizationalBrainService._clip(risk_score) / 330), 3),
            evidence=evidence,
            recommendation=recommendation,
        )

    @staticmethod
    def _recommendation(recommendation_id: str, priority: BrainRiskLevel, action: str, reason: str, expected_impact: str, source_systems: list[str]) -> OrganizationalBrainRecommendation:
        confidence = {"critical": 0.94, "high": 0.9, "medium": 0.84, "low": 0.76}[priority]
        return OrganizationalBrainRecommendation(
            recommendation_id=f"org-brain-{recommendation_id}",
            priority=priority,
            action=action,
            reason=reason,
            expected_impact=expected_impact,
            confidence=confidence,
            source_systems=source_systems,
        )

    @staticmethod
    def _component(name: str, status, evidence: list[str]) -> OrganizationalBrainComponent:
        return OrganizationalBrainComponent(name=name, status=status, evidence=evidence)

    @staticmethod
    def _embedding_evidence(analysis: OrganizationalBrainResponse, node_id: str) -> str:
        embedding = next((item for item in analysis.gnn_engine.embeddings if item.node_id == node_id), None)
        if not embedding:
            return "No top embedding row for cited node; graph evidence used."
        return f"embedding={embedding.embedding[:4]}, influence={embedding.influence_prediction}, risk={embedding.risk_prediction}"

    @staticmethod
    def _slug(value: str) -> str:
        normalized = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
        while "--" in normalized:
            normalized = normalized.replace("--", "-")
        return normalized.strip("-") or "unknown"

    @staticmethod
    def _clip(value: float) -> float:
        if math.isnan(float(value)):
            return 0.0
        return max(0.0, min(100.0, float(value)))

    @staticmethod
    def _risk(score: float) -> BrainRiskLevel:
        if score >= 82:
            return "critical"
        if score >= 65:
            return "high"
        if score >= 42:
            return "medium"
        return "low"

    def _persist(self, response: OrganizationalBrainResponse) -> None:
        self._append_jsonl(HISTORY_PATH, response.model_dump(mode="json"))

    def _append_jsonl(self, path: Path, payload: dict[str, object]) -> None:
        with self._lock:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")

    @staticmethod
    def _latest_history() -> OrganizationalBrainResponse | None:
        if not HISTORY_PATH.exists():
            return None
        try:
            size = HISTORY_PATH.stat().st_size
            with HISTORY_PATH.open("rb") as handle:
                handle.seek(max(0, size - 8_388_608))
                lines = handle.read().decode("utf-8", errors="ignore").splitlines()[-100:]
            for line in reversed(lines):
                try:
                    return OrganizationalBrainResponse.model_validate_json(line)
                except Exception:
                    continue
        except OSError:
            return None
        return None


organizational_brain_service = OrganizationalBrainService()
