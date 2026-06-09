from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


AnomalySeverity = Literal["critical", "high", "medium", "low"]


class BehaviorEvent(BaseModel):
    employee_id: str
    employee_name: str
    department: str
    role: str
    timestamp: datetime
    login_count: int = Field(ge=0, le=80)
    failed_logins: int = Field(ge=0, le=80)
    off_hours_logins: int = Field(ge=0, le=60)
    inactive_hours: float = Field(ge=0, le=24)
    productivity_score: float = Field(ge=0, le=1)
    overtime_hours: float = Field(ge=0, le=40)
    messages_sent: int = Field(ge=0, le=400)
    negative_sentiment_ratio: float = Field(ge=0, le=1)
    toxic_message_count: int = Field(ge=0, le=100)
    data_download_mb: float = Field(ge=0, le=100000)
    privileged_actions: int = Field(ge=0, le=200)
    project_commits: int = Field(ge=0, le=120)
    meeting_hours: float = Field(ge=0, le=24)
    stress_score: float = Field(ge=0, le=1)
    access_scope_changes: int = Field(ge=0, le=100)
    device_change_count: int = Field(default=0, ge=0, le=50)
    unusual_location_count: int = Field(default=0, ge=0, le=50)
    impossible_travel_events: int = Field(default=0, ge=0, le=20)
    browser_fingerprint_changes: int = Field(default=0, ge=0, le=50)
    sensitive_file_accesses: int = Field(default=0, ge=0, le=10000)
    external_transfer_mb: float = Field(default=0, ge=0, le=100000)
    cloud_upload_mb: float = Field(default=0, ge=0, le=100000)
    usb_write_mb: float = Field(default=0, ge=0, le=100000)
    policy_violation_count: int = Field(default=0, ge=0, le=500)
    admin_role_changes: int = Field(default=0, ge=0, le=100)
    privileged_session_minutes: float = Field(default=0, ge=0, le=1440)
    baseline_deviation: float = Field(default=0, ge=0, le=1)


class AnomalyDetectionRequest(BaseModel):
    events: list[BehaviorEvent] = Field(default_factory=list)
    sensitivity: float = Field(default=0.6, ge=0, le=1)


class AnomalyAlert(BaseModel):
    alert_id: str
    employee_id: str
    employee_name: str
    department: str
    anomaly_type: str
    severity: AnomalySeverity
    anomaly_score: float = Field(ge=0, le=100)
    insider_threat_score: float = Field(ge=0, le=100)
    access_anomaly_score: float = Field(ge=0, le=100)
    data_leakage_probability: float = Field(ge=0, le=100)
    privilege_misuse_score: float = Field(ge=0, le=100)
    fraud_likelihood: float = Field(ge=0, le=100)
    burnout_anomaly_score: float = Field(ge=0, le=100)
    productivity_anomaly_score: float = Field(ge=0, le=100)
    behavioral_drift_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    evidence: list[str]
    affected_assets: list[str]
    recommendation: str
    mitigation_actions: list[str]
    source_model: str


class AnomalySummary(BaseModel):
    critical_alerts: int
    high_alerts: int
    insider_threats: int
    burnout_anomalies: int
    productivity_anomalies: int
    data_leakage_alerts: int = 0
    access_anomaly_alerts: int = 0
    privilege_misuse_alerts: int = 0
    average_insider_score: float = Field(default=0, ge=0, le=100)
    average_data_leakage_probability: float = Field(default=0, ge=0, le=100)


class UserRiskHeatmapPoint(BaseModel):
    department: str
    employee_count: int = Field(ge=0)
    highest_risk_employee: str
    average_threat_score: float = Field(ge=0, le=100)
    average_data_leakage_probability: float = Field(ge=0, le=100)
    average_access_anomaly_score: float = Field(ge=0, le=100)
    critical_alerts: int = Field(ge=0)


class SecurityRecommendation(BaseModel):
    title: str
    priority: AnomalySeverity
    action: str
    rationale: str
    expected_impact: str
    confidence: float = Field(ge=0, le=1)


class AnomalyDetectionResponse(BaseModel):
    model: str
    generated_at: datetime
    events_analyzed: int
    anomaly_rate: float = Field(ge=0, le=1)
    adaptive_threshold: float = Field(ge=0, le=100)
    alerts: list[AnomalyAlert]
    user_risk_heatmap: list[UserRiskHeatmapPoint] = Field(default_factory=list)
    security_recommendations: list[SecurityRecommendation] = Field(default_factory=list)
    executive_insights: list[str] = Field(default_factory=list)
    summary: AnomalySummary
    source_systems: list[str] = Field(default_factory=list)
    stream_sequence: int = 1
    storage: str


class AnomalyFeedbackRequest(BaseModel):
    alert_id: str
    confirmed: bool
    severity_adjustment: int = Field(default=0, ge=-2, le=2)
    notes: str = ""


class AnomalyFeedbackResponse(BaseModel):
    alert_id: str
    learning_signal: float = Field(ge=0, le=1)
    message: str
    storage: str
