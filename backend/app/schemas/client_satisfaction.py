from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ClientRiskPriority = Literal["low", "medium", "high", "critical"]
ClientAccountTier = Literal["standard", "strategic", "enterprise", "global"]
ClientRecommendationCategory = Literal[
    "communication",
    "delivery",
    "quality",
    "churn",
    "escalation",
    "renewal",
    "executive",
    "payment",
    "project",
    "engagement",
    "opportunity",
]
ClientEngagementTrend = Literal["declining", "stable", "improving"]
ClientAssistantIntent = Literal["churn", "payment", "project", "sentiment", "opportunity", "risk", "recommendation", "summary"]


class ClientAccountSignal(BaseModel):
    client_id: str
    client_name: str
    industry: str = "Technology"
    account_tier: ClientAccountTier = "enterprise"
    project_name: str
    contract_value: float = Field(default=750000, ge=0, le=250000000)
    renewal_days: int = Field(default=120, ge=1, le=730)
    delivery_delay_days: float = Field(default=2, ge=0, le=180)
    missed_milestones: int = Field(default=0, ge=0, le=80)
    sla_breach_count: int = Field(default=0, ge=0, le=120)
    bug_frequency: float = Field(default=0.16, ge=0, le=1)
    production_incidents: int = Field(default=0, ge=0, le=80)
    qa_pass_rate: float = Field(default=0.86, ge=0, le=1)
    rework_ratio: float = Field(default=0.12, ge=0, le=1)
    issue_resolution_hours: float = Field(default=18, ge=0, le=720)
    escalation_count: int = Field(default=0, ge=0, le=100)
    communication_sentiment: float = Field(default=0.24, ge=-1, le=1)
    interaction_frequency: float = Field(default=0.72, ge=0, le=1)
    feedback_score: float = Field(default=0.78, ge=0, le=1)
    nps_delta: float = Field(default=0, ge=-100, le=100)
    delivery_consistency: float = Field(default=0.78, ge=0, le=1)
    relationship_tenure_months: int = Field(default=18, ge=0, le=240)
    executive_sponsor_engagement: float = Field(default=0.7, ge=0, le=1)
    open_critical_issues: int = Field(default=0, ge=0, le=80)
    average_payment_delay_days: float = Field(default=4, ge=0, le=180)
    overdue_invoice_amount: float = Field(default=0, ge=0, le=100_000_000)
    invoice_dispute_count: int = Field(default=0, ge=0, le=50)
    payment_terms_days: int = Field(default=30, ge=1, le=180)
    meeting_attendance_rate: float = Field(default=0.78, ge=0, le=1)
    email_response_hours: float = Field(default=18, ge=0, le=720)
    platform_usage_score: float = Field(default=0.7, ge=0, le=1)
    feature_adoption_score: float = Field(default=0.64, ge=0, le=1)
    support_ticket_count: int = Field(default=4, ge=0, le=300)
    upsell_signal_score: float = Field(default=0.42, ge=0, le=1)
    expansion_budget_signal: float = Field(default=0.38, ge=0, le=1)
    stakeholder_change_count: int = Field(default=0, ge=0, le=50)
    meeting_transcripts: list[str] = Field(default_factory=list, max_length=12)
    email_threads: list[str] = Field(default_factory=list, max_length=12)


class ClientSatisfactionRequest(BaseModel):
    cycle_name: str = "Realtime Client Satisfaction Review"
    horizon_days: int = Field(default=45, ge=7, le=180)
    clients: list[ClientAccountSignal] = Field(default_factory=list, max_length=32)
    realtime: bool = False


class ClientForecastPoint(BaseModel):
    day: int = Field(ge=1)
    client_health_score: float = Field(ge=0, le=100)
    churn_risk: float = Field(ge=0, le=100)
    escalation_probability: float = Field(ge=0, le=100)
    delivery_confidence: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)


class ClientSatisfactionPrediction(BaseModel):
    client_id: str
    client_name: str
    industry: str
    account_tier: ClientAccountTier
    project_name: str
    client_health_score: float = Field(ge=0, le=100)
    satisfaction_score: float = Field(ge=0, le=100)
    dissatisfaction_probability: float = Field(ge=0, le=100)
    churn_risk: float = Field(ge=0, le=100)
    escalation_probability: float = Field(ge=0, le=100)
    relationship_stability: float = Field(ge=0, le=100)
    communication_health: float = Field(ge=0, le=100)
    delivery_health: float = Field(ge=0, le=100)
    quality_risk: float = Field(ge=0, le=100)
    trust_decline: float = Field(ge=0, le=100)
    renewal_risk: float = Field(ge=0, le=100)
    renewal_probability: float = Field(ge=0, le=100)
    payment_delay_risk: float = Field(ge=0, le=100)
    predicted_payment_delay_days: float = Field(ge=0, le=365)
    invoice_collection_risk: float = Field(ge=0, le=100)
    project_failure_risk: float = Field(ge=0, le=100)
    budget_overrun_risk: float = Field(ge=0, le=100)
    client_dissatisfaction_risk: float = Field(ge=0, le=100)
    engagement_score: float = Field(ge=0, le=100)
    engagement_trend: ClientEngagementTrend
    upsell_opportunity_score: float = Field(ge=0, le=100)
    upsell_revenue_potential: float = Field(ge=0, le=250000000)
    intervention_priority_score: float = Field(ge=0, le=100)
    revenue_at_risk: float = Field(ge=0, le=250000000)
    sentiment_label: str
    confidence: float = Field(ge=0, le=1)
    risk_drivers: list[str] = Field(default_factory=list)
    recovery_actions: list[str] = Field(default_factory=list)
    forecast: list[ClientForecastPoint]


class ClientHealthHeatmapPoint(BaseModel):
    client_name: str
    metric: str
    score: float = Field(ge=0, le=100)
    priority: ClientRiskPriority


class CommunicationSentimentPoint(BaseModel):
    client_name: str
    label: str
    sentiment_score: float = Field(ge=-1, le=1)
    negativity_risk: float = Field(ge=0, le=100)
    trust_risk: float = Field(ge=0, le=100)


class DeliveryRiskPoint(BaseModel):
    client_name: str
    delay_risk: float = Field(ge=0, le=100)
    sla_risk: float = Field(ge=0, le=100)
    quality_risk: float = Field(ge=0, le=100)
    issue_resolution_risk: float = Field(ge=0, le=100)


class ClientPaymentRiskPoint(BaseModel):
    client_name: str
    payment_delay_risk: float = Field(ge=0, le=100)
    predicted_delay_days: float = Field(ge=0, le=365)
    collection_risk: float = Field(ge=0, le=100)
    overdue_invoice_amount: float = Field(ge=0, le=100_000_000)
    priority: ClientRiskPriority


class ClientProjectRiskPoint(BaseModel):
    client_name: str
    project_name: str
    project_failure_risk: float = Field(ge=0, le=100)
    delay_risk: float = Field(ge=0, le=100)
    budget_overrun_risk: float = Field(ge=0, le=100)
    dissatisfaction_risk: float = Field(ge=0, le=100)
    primary_cause: str
    priority: ClientRiskPriority


class ClientEngagementAnalyticsPoint(BaseModel):
    client_name: str
    engagement_score: float = Field(ge=0, le=100)
    trend: ClientEngagementTrend
    meeting_participation: float = Field(ge=0, le=100)
    email_responsiveness: float = Field(ge=0, le=100)
    platform_usage: float = Field(ge=0, le=100)
    feature_adoption: float = Field(ge=0, le=100)
    support_pressure: float = Field(ge=0, le=100)


class ClientOpportunityInsight(BaseModel):
    client_name: str
    opportunity: str
    probability: float = Field(ge=0, le=100)
    potential_revenue: float = Field(ge=0, le=250000000)
    rationale: str
    recommended_action: str
    priority: ClientRiskPriority


class ClientRecoveryRecommendation(BaseModel):
    title: str
    category: ClientRecommendationCategory
    priority: ClientRiskPriority
    action: str
    expected_impact: str
    confidence: float = Field(ge=0, le=1)
    affected_clients: list[str] = Field(default_factory=list)


class ClientSatisfactionAlert(BaseModel):
    title: str
    severity: ClientRiskPriority
    probability: float = Field(ge=0, le=100)
    impact: str
    recommendation: str


class ClientSatisfactionSummary(BaseModel):
    clients_analyzed: int
    average_client_health_score: float = Field(ge=0, le=100)
    average_churn_risk: float = Field(ge=0, le=100)
    average_escalation_probability: float = Field(ge=0, le=100)
    high_risk_clients: int
    revenue_at_risk: float = Field(ge=0, le=250000000)
    payment_risk_accounts: int
    project_risk_accounts: int
    opportunity_revenue: float = Field(ge=0, le=250000000)
    highest_risk_client: str
    best_upsell_client: str
    stream_sequence: int = 1


class ClientSatisfactionResponse(BaseModel):
    model: str
    generated_at: datetime
    cycle_name: str
    horizon_days: int
    predictions: list[ClientSatisfactionPrediction]
    heatmap: list[ClientHealthHeatmapPoint]
    communication_sentiment: list[CommunicationSentimentPoint]
    delivery_risks: list[DeliveryRiskPoint]
    payment_risks: list[ClientPaymentRiskPoint]
    project_risks: list[ClientProjectRiskPoint]
    engagement_analytics: list[ClientEngagementAnalyticsPoint]
    opportunity_pipeline: list[ClientOpportunityInsight]
    recommendations: list[ClientRecoveryRecommendation]
    alerts: list[ClientSatisfactionAlert]
    executive_insights: list[str]
    supported_questions: list[str]
    summary: ClientSatisfactionSummary
    source_systems: list[str]
    storage: str


class ClientAssistantRequest(BaseModel):
    question: str = Field(default="Show highest-risk accounts.", min_length=2, max_length=500)


class ClientAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: ClientAssistantIntent
    answer: str
    confidence: float = Field(ge=0, le=1)
    cited_clients: list[str] = Field(default_factory=list)
    cited_evidence: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    source_systems: list[str]
    storage: str
