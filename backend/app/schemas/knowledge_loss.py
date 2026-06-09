from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


KnowledgePriority = Literal["low", "medium", "high", "critical"]
KnowledgeSourceType = Literal["chat", "documentation", "meeting", "git", "jira", "slack", "support", "code", "sop", "design"]
KnowledgeNodeType = Literal["employee", "skill", "system", "workflow", "document", "team"]
KnowledgeDocumentType = Literal["sop", "deployment_guide", "troubleshooting_manual", "architecture_summary", "onboarding_guide"]
KnowledgeRecommendationCategory = Literal["documentation", "session", "cross_training", "mentorship", "backup_owner", "onboarding", "executive"]


class KnowledgeSourceSignal(BaseModel):
    source_id: str
    title: str
    source_type: KnowledgeSourceType = "documentation"
    employee_id: str
    employee_name: str
    department: str = "Engineering"
    team: str = "Platform"
    role: str = "Engineer"
    content: str = Field(min_length=12, max_length=5000)
    systems: list[str] = Field(default_factory=list, max_length=16)
    skills: list[str] = Field(default_factory=list, max_length=24)
    contribution_count: int = Field(default=4, ge=0, le=1000)
    incident_resolutions: int = Field(default=1, ge=0, le=500)
    docs_authored: int = Field(default=1, ge=0, le=500)
    commit_count: int = Field(default=6, ge=0, le=5000)
    meeting_mentions: int = Field(default=2, ge=0, le=500)
    attrition_risk: float = Field(default=0.24, ge=0, le=1)
    seniority: float = Field(default=0.65, ge=0, le=1)
    documentation_quality: float = Field(default=0.62, ge=0, le=1)
    last_updated_days: int = Field(default=14, ge=0, le=730)
    business_criticality: float = Field(default=0.62, ge=0, le=1)
    redundancy_count: int = Field(default=1, ge=0, le=20)
    handoff_readiness: float = Field(default=0.48, ge=0, le=1)
    onboarding_relevance: float = Field(default=0.54, ge=0, le=1)


class KnowledgeLossRequest(BaseModel):
    cycle_name: str = "Realtime Knowledge Loss Prevention Review"
    horizon_days: int = Field(default=60, ge=14, le=180)
    target_role: str = "Backend Engineer"
    sources: list[KnowledgeSourceSignal] = Field(default_factory=list, max_length=80)
    realtime: bool = False


class ExpertiseProfile(BaseModel):
    employee_id: str
    employee_name: str
    department: str
    team: str
    role: str
    top_expertise: list[str]
    owned_systems: list[str]
    expertise_score: float = Field(ge=0, le=100)
    knowledge_criticality: float = Field(ge=0, le=100)
    ownership_concentration: float = Field(ge=0, le=100)
    documentation_coverage: float = Field(ge=0, le=100)
    attrition_risk: float = Field(ge=0, le=100)
    knowledge_loss_probability: float = Field(ge=0, le=100)
    operational_disruption_risk: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    evidence: list[str] = Field(default_factory=list)
    transfer_actions: list[str] = Field(default_factory=list)


class KnowledgeGraphNode(BaseModel):
    node_id: str
    label: str
    node_type: KnowledgeNodeType
    risk_score: float = Field(ge=0, le=100)
    size: float = Field(ge=1, le=100)
    metadata: dict[str, str | float | int] = Field(default_factory=dict)


class KnowledgeGraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    strength: float = Field(ge=0, le=100)
    risk: float = Field(ge=0, le=100)
    evidence: str


class GeneratedKnowledgeDocument(BaseModel):
    document_id: str
    title: str
    document_type: KnowledgeDocumentType
    owner: str
    systems: list[str]
    content: str
    coverage_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    source_count: int = Field(ge=1)


class KnowledgeRiskForecastPoint(BaseModel):
    employee_name: str
    day: int = Field(ge=1)
    knowledge_loss_probability: float = Field(ge=0, le=100)
    operational_disruption_risk: float = Field(ge=0, le=100)
    transfer_completion_probability: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)


class OrganizationalMemoryHeatmapPoint(BaseModel):
    department: str
    system: str
    expertise_concentration: float = Field(ge=0, le=100)
    documentation_coverage: float = Field(ge=0, le=100)
    redundancy_score: float = Field(ge=0, le=100)
    knowledge_loss_risk: float = Field(ge=0, le=100)
    priority: KnowledgePriority


class OnboardingRoadmap(BaseModel):
    role: str
    focus_area: str
    steps: list[str]
    estimated_days_saved: float = Field(ge=0, le=120)
    confidence: float = Field(ge=0, le=1)


class KnowledgeTransferRecommendation(BaseModel):
    title: str
    category: KnowledgeRecommendationCategory
    priority: KnowledgePriority
    action: str
    expected_impact: str
    affected_employees: list[str] = Field(default_factory=list)
    target_systems: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class KnowledgeRiskAlert(BaseModel):
    title: str
    severity: KnowledgePriority
    probability: float = Field(ge=0, le=100)
    impact: str
    recommendation: str


class KnowledgeLossSummary(BaseModel):
    sources_analyzed: int
    experts_identified: int
    graph_nodes: int
    graph_edges: int
    high_risk_dependencies: int
    generated_documents: int
    average_documentation_coverage: float = Field(ge=0, le=100)
    knowledge_loss_risk: float = Field(ge=0, le=100)
    top_risk_owner: str
    stream_sequence: int = 1


class KnowledgeLossResponse(BaseModel):
    model: str
    generated_at: datetime
    cycle_name: str
    horizon_days: int
    target_role: str
    expertise_profiles: list[ExpertiseProfile]
    graph_nodes: list[KnowledgeGraphNode]
    graph_edges: list[KnowledgeGraphEdge]
    generated_documents: list[GeneratedKnowledgeDocument]
    forecasts: list[KnowledgeRiskForecastPoint]
    memory_heatmap: list[OrganizationalMemoryHeatmapPoint]
    onboarding_roadmaps: list[OnboardingRoadmap]
    recommendations: list[KnowledgeTransferRecommendation]
    alerts: list[KnowledgeRiskAlert]
    executive_insights: list[str]
    summary: KnowledgeLossSummary
    source_systems: list[str]
    storage: str
    graph_store: str
