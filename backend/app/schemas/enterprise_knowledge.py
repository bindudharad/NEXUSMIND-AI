from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


KnowledgeBrainSourceType = Literal[
    "text",
    "pdf",
    "docx",
    "pptx",
    "xlsx",
    "csv",
    "wiki",
    "sop",
    "incident",
    "meeting",
    "project_report",
    "technical_doc",
]


class EnterpriseKnowledgeDocumentInput(BaseModel):
    document_id: str | None = None
    title: str = Field(min_length=2)
    source_type: KnowledgeBrainSourceType = "text"
    file_name: str | None = None
    content: str | None = None
    content_base64: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnterpriseKnowledgeIngestRequest(BaseModel):
    documents: list[EnterpriseKnowledgeDocumentInput] = Field(default_factory=list, min_length=1)
    tenant_id: str = "nexusmind-demo"
    source_system: str = "manual_upload"
    persist: bool = True


class EnterpriseKnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=2)
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict[str, Any] = Field(default_factory=dict)
    include_graph_evidence: bool = True

    @model_validator(mode="before")
    @classmethod
    def normalize_result_limit(cls, data: Any) -> Any:
        if isinstance(data, dict):
            requested_limit = data.get("top_k") or data.get("topK") or data.get("limit")
            if requested_limit is not None:
                data = {**data, "top_k": requested_limit}
        return data


class EnterpriseKnowledgeAskRequest(BaseModel):
    question: str = Field(min_length=2)
    top_k: int = Field(default=6, ge=1, le=20)
    include_graph_evidence: bool = True
    session_id: str = "default"

    @model_validator(mode="before")
    @classmethod
    def normalize_result_limit(cls, data: Any) -> Any:
        if isinstance(data, dict):
            requested_limit = data.get("top_k") or data.get("topK") or data.get("limit")
            if requested_limit is not None:
                data = {**data, "top_k": requested_limit}
        return data


class EnterpriseKnowledgeEntitySet(BaseModel):
    people: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    incidents: list[str] = Field(default_factory=list)
    solutions: list[str] = Field(default_factory=list)
    systems: list[str] = Field(default_factory=list)


class EnterpriseKnowledgeDocumentRecord(BaseModel):
    document_id: str
    title: str
    source_type: str
    file_name: str
    parser: str
    chunks: int
    extracted_entities: EnterpriseKnowledgeEntitySet
    experts: list[str] = Field(default_factory=list)
    systems: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class EnterpriseKnowledgeCitation(BaseModel):
    citation_id: str
    document_id: str
    title: str
    chunk_id: str
    snippet: str
    score: float = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnterpriseKnowledgeMatchedChunk(BaseModel):
    chunk_id: str
    text: str
    score: float = Field(ge=0)
    entities: EnterpriseKnowledgeEntitySet
    experts: list[str] = Field(default_factory=list)
    systems: list[str] = Field(default_factory=list)
    citation_id: str


class EnterpriseKnowledgeSearchResult(BaseModel):
    document_id: str
    title: str
    source_type: str
    score: float = Field(ge=0)
    matched_chunks: list[EnterpriseKnowledgeMatchedChunk]
    extracted_entities: EnterpriseKnowledgeEntitySet
    experts: list[str] = Field(default_factory=list)
    systems: list[str] = Field(default_factory=list)
    citations: list[EnterpriseKnowledgeCitation]
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnterpriseKnowledgeExpertRanking(BaseModel):
    employee_id: str
    employee_name: str
    department: str
    team: str
    skill: str
    score: float = Field(ge=0, le=100)
    evidence: list[str] = Field(default_factory=list)
    documents: list[str] = Field(default_factory=list)
    systems: list[str] = Field(default_factory=list)


class EnterpriseKnowledgeGraphNode(BaseModel):
    id: str
    label: str
    type: str
    score: float = Field(default=0, ge=0, le=100)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnterpriseKnowledgeGraphEdge(BaseModel):
    source: str
    target: str
    type: str
    weight: float = Field(default=1, ge=0)
    evidence: str


class EnterpriseKnowledgeRecommendation(BaseModel):
    title: str
    priority: Literal["critical", "high", "medium", "low"]
    action: str
    rationale: str
    expected_impact: float = Field(ge=0, le=100)


class EnterpriseKnowledgeInsight(BaseModel):
    title: str
    category: str
    detail: str
    score: float = Field(ge=0, le=100)
    evidence: list[str] = Field(default_factory=list)


class EnterpriseKnowledgeTimelineEvent(BaseModel):
    event_id: str
    occurred_at: datetime
    event_type: str
    title: str
    summary: str
    people: list[str] = Field(default_factory=list)
    systems: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class EnterpriseKnowledgeSecurityControl(BaseModel):
    control: str
    status: Literal["ready", "enforced", "simulated", "watch"]
    detail: str
    evidence: list[str] = Field(default_factory=list)


class EnterpriseKnowledgeIntegrationSignal(BaseModel):
    system: str
    status: Literal["synced", "ready", "projected", "watch"]
    update: str
    evidence: list[str] = Field(default_factory=list)


class EnterpriseKnowledgeAgentContribution(BaseModel):
    agent: str
    role: str
    finding: str
    recommendation: str
    confidence: float = Field(ge=0, le=1)
    source_systems: list[str] = Field(default_factory=list)


class EnterpriseKnowledgeStatusReport(BaseModel):
    knowledge_ingestion_status: str
    document_intelligence_status: str
    vector_database_status: str
    knowledge_graph_status: str
    rag_status: str
    expertise_discovery_status: str
    lessons_learned_status: str
    knowledge_assistant_status: str
    dashboard_status: str
    security_status: str
    digital_twin_integration_status: str
    multi_agent_integration_status: str
    missing_components: list[str] = Field(default_factory=list)
    fixed_components: list[str] = Field(default_factory=list)
    errors_found: list[str] = Field(default_factory=list)
    errors_fixed: list[str] = Field(default_factory=list)
    performance_metrics: dict[str, Any] = Field(default_factory=dict)
    production_readiness_score: float = Field(ge=0, le=100)
    innovation_score: float = Field(ge=0, le=100)
    business_value_score: float = Field(ge=0, le=100)
    final_verdict: str


class EnterpriseKnowledgeSummary(BaseModel):
    knowledge_health_score: float = Field(ge=0, le=100)
    documents_indexed: int
    chunks_indexed: int
    experts_detected: int
    graph_nodes: int
    graph_edges: int
    incidents_detected: int
    solutions_detected: int
    sop_gaps: int
    qdrant_status: str
    neo4j_status: str


class EnterpriseKnowledgeDefaultResponse(BaseModel):
    model: str
    generated_at: datetime
    summary: EnterpriseKnowledgeSummary
    documents: list[EnterpriseKnowledgeDocumentRecord]
    top_experts: list[EnterpriseKnowledgeExpertRanking]
    graph_nodes: list[EnterpriseKnowledgeGraphNode]
    graph_edges: list[EnterpriseKnowledgeGraphEdge]
    technology_map: list[EnterpriseKnowledgeInsight]
    valuable_documents: list[EnterpriseKnowledgeInsight]
    incident_memory: list[EnterpriseKnowledgeInsight]
    lessons_learned: list[EnterpriseKnowledgeInsight]
    organizational_memory_timeline: list[EnterpriseKnowledgeTimelineEvent]
    sop_gaps: list[EnterpriseKnowledgeInsight]
    recommendations: list[EnterpriseKnowledgeRecommendation]
    security_controls: list[EnterpriseKnowledgeSecurityControl]
    digital_twin_sync: list[EnterpriseKnowledgeIntegrationSignal]
    agent_council: list[EnterpriseKnowledgeAgentContribution]
    status_report: EnterpriseKnowledgeStatusReport
    source_systems: list[str]
    storage: dict[str, str]
    final_verdict: str


class EnterpriseKnowledgeIngestResponse(BaseModel):
    model: str
    generated_at: datetime
    ingested_documents: list[EnterpriseKnowledgeDocumentRecord]
    summary: EnterpriseKnowledgeSummary
    graph_nodes: list[EnterpriseKnowledgeGraphNode]
    graph_edges: list[EnterpriseKnowledgeGraphEdge]
    recommendations: list[EnterpriseKnowledgeRecommendation]
    source_systems: list[str]
    storage: dict[str, str]


class EnterpriseKnowledgeSearchResponse(BaseModel):
    model: str
    generated_at: datetime
    query: str
    results: list[EnterpriseKnowledgeSearchResult]
    citations: list[EnterpriseKnowledgeCitation]
    graph_evidence: list[EnterpriseKnowledgeGraphEdge]
    source_systems: list[str]
    vector_database: str
    storage: dict[str, str]


class EnterpriseKnowledgeAskResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    answer: str
    confidence: float = Field(ge=0, le=1)
    citations: list[EnterpriseKnowledgeCitation]
    retrieved_chunks: list[EnterpriseKnowledgeMatchedChunk]
    graph_evidence: list[EnterpriseKnowledgeGraphEdge]
    source_systems: list[str]
    recommended_follow_up_actions: list[str]
    storage: dict[str, str]
    final_verdict: str


class EnterpriseKnowledgeGraphResponse(BaseModel):
    model: str
    generated_at: datetime
    nodes: list[EnterpriseKnowledgeGraphNode]
    edges: list[EnterpriseKnowledgeGraphEdge]
    source_systems: list[str]
    storage: dict[str, str]


class EnterpriseKnowledgeExpertsResponse(BaseModel):
    model: str
    generated_at: datetime
    skill: str | None
    experts: list[EnterpriseKnowledgeExpertRanking]
    source_systems: list[str]
    storage: dict[str, str]
