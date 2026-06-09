from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


BrainNodeType = Literal["employee", "team", "department", "project", "skill", "client", "knowledge_asset", "location"]
BrainEdgeType = Literal[
    "reports_to",
    "works_with",
    "communicates_with",
    "collaborates_with",
    "depends_on",
    "mentors",
    "shares_knowledge_with",
]
BrainRiskLevel = Literal["low", "medium", "high", "critical"]
BrainAssistantIntent = Literal[
    "influence",
    "silo",
    "bottleneck",
    "knowledge",
    "dependency",
    "simulation",
    "risk",
    "summary",
]
BrainComponentStatus = Literal["ready", "degraded", "missing"]


class OrganizationalBrainRequest(BaseModel):
    cycle_name: str = "Realtime AI Organizational Brain Review"
    horizon_months: int = Field(default=12, ge=3, le=36)
    include_marketplace: bool = True
    include_knowledge_brain: bool = True
    include_client_graph: bool = True
    refresh: bool = True


class OrganizationalBrainAssistantRequest(BaseModel):
    question: str = Field(default="Who is the most influential employee?", min_length=2, max_length=700)
    session_id: str = "organizational-brain"
    horizon_months: int = Field(default=12, ge=3, le=36)


class OrganizationalBrainNode(BaseModel):
    id: str
    label: str
    node_type: BrainNodeType
    department: str | None = None
    team: str | None = None
    risk_score: float = Field(default=0, ge=0, le=100)
    influence_score: float = Field(default=0, ge=0, le=100)
    knowledge_score: float = Field(default=0, ge=0, le=100)
    x: float = Field(default=0, ge=0, le=1000)
    y: float = Field(default=0, ge=0, le=1000)
    metadata: dict[str, str | float | int | bool] = Field(default_factory=dict)


class OrganizationalBrainEdge(BaseModel):
    source: str
    target: str
    edge_type: BrainEdgeType
    weight: float = Field(default=1, ge=0, le=10)
    risk_score: float = Field(default=0, ge=0, le=100)
    evidence: str
    source_system: str


class GraphDatabaseStatus(BaseModel):
    engine: str
    status: BrainComponentStatus
    configured_external_database: str
    node_count: int = Field(ge=0)
    relationship_count: int = Field(ge=0)
    indexed_fields: list[str]
    query_latency_ms: float = Field(ge=0)
    storage: str
    export_format: str


class GNNNodeEmbedding(BaseModel):
    node_id: str
    label: str
    node_type: BrainNodeType
    embedding: list[float]
    influence_prediction: float = Field(ge=0, le=100)
    knowledge_flow_prediction: float = Field(ge=0, le=100)
    risk_prediction: float = Field(ge=0, le=100)
    nearest_neighbors: list[str]


class GNNRelationshipPrediction(BaseModel):
    source: str
    target: str
    predicted_relationship: BrainEdgeType
    probability: float = Field(ge=0, le=1)
    rationale: str


class GNNEngineStatus(BaseModel):
    status: BrainComponentStatus
    supported_models: list[Literal["GraphSAGE", "GAT", "GCN", "GIN"]]
    training_status: str
    node_embedding_dimensions: int = Field(ge=1)
    training_nodes: int = Field(ge=0)
    training_edges: int = Field(ge=0)
    validation_mae: float = Field(ge=0, le=1)
    inference_latency_ms: float = Field(ge=0)
    embeddings: list[GNNNodeEmbedding]
    relationship_predictions: list[GNNRelationshipPrediction]
    source_systems: list[str]


class CommunicationFlowFinding(BaseModel):
    source_unit: str
    target_unit: str
    communication_score: float = Field(ge=0, le=100)
    bottleneck_node: str
    delay_risk: float = Field(ge=0, le=100)
    evidence: list[str]
    recommendation: str


class KnowledgeFlowFinding(BaseModel):
    knowledge_asset: str
    primary_experts: list[str]
    dependent_teams: list[str]
    knowledge_loss_risk: float = Field(ge=0, le=100)
    flow_score: float = Field(ge=0, le=100)
    recommendation: str
    evidence: list[str]


class TeamDependencyFinding(BaseModel):
    source_team: str
    dependent_on: str
    dependency_strength: float = Field(ge=0, le=100)
    delivery_risk: float = Field(ge=0, le=100)
    critical_path: bool
    evidence: list[str]
    recommendation: str


class BottleneckFinding(BaseModel):
    node_id: str
    label: str
    node_type: BrainNodeType
    bottleneck_score: float = Field(ge=0, le=100)
    affected_units: list[str]
    evidence: list[str]
    recommendation: str


class InfluenceFinding(BaseModel):
    employee_id: str
    employee_name: str
    formal_role: str
    influence_score: float = Field(ge=0, le=100)
    influenced_teams: list[str]
    hidden_leader: bool
    evidence: list[str]


class SiloFinding(BaseModel):
    unit: str
    silo_risk: float = Field(ge=0, le=100)
    external_collaboration_ratio: float = Field(ge=0, le=1)
    missing_bridges: list[str]
    evidence: list[str]
    recommendation: str


class OrganizationalRiskPrediction(BaseModel):
    risk_type: Literal["knowledge_loss", "communication_failure", "leadership_dependency", "team_collapse", "collaboration_decline"]
    affected_entity: str
    risk_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    evidence: list[str]
    recommendation: str


class OrganizationalBrainRecommendation(BaseModel):
    recommendation_id: str
    priority: BrainRiskLevel
    action: str
    reason: str
    expected_impact: str
    confidence: float = Field(ge=0, le=1)
    source_systems: list[str]


class OrganizationalBrainIntegrationStatus(BaseModel):
    employee_twin: BrainComponentStatus
    team_twin: BrainComponentStatus
    department_twin: BrainComponentStatus
    company_twin: BrainComponentStatus
    time_machine: BrainComponentStatus
    workforce_simulator: BrainComponentStatus
    executive_dashboard: BrainComponentStatus
    evidence: list[str]


class OrganizationalBrainComponent(BaseModel):
    name: str
    status: BrainComponentStatus
    evidence: list[str]


class OrganizationalBrainSummary(BaseModel):
    organizational_brain_score: float = Field(ge=0, le=100)
    graph_nodes: int = Field(ge=0)
    graph_edges: int = Field(ge=0)
    gnn_prediction_count: int = Field(ge=0)
    communication_bottlenecks: int = Field(ge=0)
    knowledge_loss_hotspots: int = Field(ge=0)
    high_silo_units: int = Field(ge=0)
    critical_dependency_paths: int = Field(ge=0)
    hidden_influencers: int = Field(ge=0)
    stream_sequence: int = 1


class GraphVisualizationLayer(BaseModel):
    layout_algorithm: str
    supports_zoom: bool
    supports_search: bool
    supports_filters: bool
    realtime_updates: bool
    nodes: list[OrganizationalBrainNode]
    edges: list[OrganizationalBrainEdge]


class OrganizationalBrainResponse(BaseModel):
    model: str
    generated_at: datetime
    cycle_name: str
    summary: OrganizationalBrainSummary
    graph_database: GraphDatabaseStatus
    graph_nodes: list[OrganizationalBrainNode]
    graph_edges: list[OrganizationalBrainEdge]
    gnn_engine: GNNEngineStatus
    communication_flow: list[CommunicationFlowFinding]
    knowledge_flow: list[KnowledgeFlowFinding]
    team_dependencies: list[TeamDependencyFinding]
    bottlenecks: list[BottleneckFinding]
    influence_network: list[InfluenceFinding]
    silo_detection: list[SiloFinding]
    risk_predictions: list[OrganizationalRiskPrediction]
    recommendations: list[OrganizationalBrainRecommendation]
    graph_visualization: GraphVisualizationLayer
    integration_status: OrganizationalBrainIntegrationStatus
    components: list[OrganizationalBrainComponent]
    executive_brief: str
    supported_questions: list[str]
    source_systems: list[str]
    production_readiness_score: float = Field(ge=0, le=100)
    research_innovation_score: float = Field(ge=0, le=100)
    final_verdict: str
    storage: str


class OrganizationalBrainAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: BrainAssistantIntent
    answer: str
    confidence: float = Field(ge=0, le=1)
    cited_nodes: list[str]
    cited_edges: list[str]
    recommended_actions: list[str]
    graph_evidence: list[str]
    gnn_evidence: list[str]
    source_systems: list[str]
    storage: str
