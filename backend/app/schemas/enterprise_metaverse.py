from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


MetaverseRoomType = Literal[
    "headquarters",
    "department",
    "team",
    "project",
    "meeting_room",
    "data_room",
    "executive_command_center",
    "crisis_command_room",
    "innovation_lab",
]
MetaverseOverlayType = Literal["risk", "productivity", "burnout", "revenue", "security", "client", "simulation", "agent"]
MetaverseRiskLevel = Literal["low", "medium", "high", "critical"]
MetaverseSimulationType = Literal[
    "revenue_drop",
    "mass_resignation",
    "cloud_outage",
    "team_restructure",
    "new_market_expansion",
    "workload_increase",
    "cyberattack",
]
MetaverseNavigationAction = Literal["navigate", "inspect", "simulate", "show_overlay", "summon_agent"]


class MetaverseVector3(BaseModel):
    x: float
    y: float
    z: float


class MetaverseRoom(BaseModel):
    room_id: str
    name: str
    room_type: MetaverseRoomType
    level: int = Field(ge=0, le=20)
    position: MetaverseVector3
    size: MetaverseVector3
    color: str
    glow_color: str
    health_score: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    risk_level: MetaverseRiskLevel
    occupancy: int = Field(ge=0)
    kpis: dict[str, float | int | str | bool]
    analytics: list[str]
    overlays: list[MetaverseOverlayType]
    enter_actions: list[str]
    source_systems: list[str]


class MetaverseConnection(BaseModel):
    source_room_id: str
    target_room_id: str
    connection_type: Literal["corridor", "elevator", "data_link", "risk_propagation", "agent_route"]
    strength: float = Field(ge=0, le=1)
    latency_ms: int = Field(ge=0)
    risk_flow: float = Field(ge=0, le=100)
    source_systems: list[str]


class MetaverseOverlay(BaseModel):
    overlay_id: str
    room_id: str
    overlay_type: MetaverseOverlayType
    label: str
    value: float = Field(ge=0, le=100)
    severity: MetaverseRiskLevel
    color: str
    explanation: str
    source_systems: list[str]


class MetaverseAgentAvatar(BaseModel):
    avatar_id: str
    agent_name: str
    room_id: str
    position: MetaverseVector3
    color: str
    current_message: str
    recommendation: str
    confidence: float = Field(ge=0, le=1)
    source_systems: list[str]


class MetaverseSimulationRequest(BaseModel):
    scenario_type: MetaverseSimulationType = "mass_resignation"
    question: str = Field(default="What happens if 30% of Engineering resigns?", min_length=2, max_length=700)
    target_room_id: str = Field(default="engineering-room", max_length=120)
    magnitude_percent: float = Field(default=30, ge=1, le=100)
    horizon_months: int = Field(default=6, ge=1, le=36)


class MetaverseSimulationImpact(BaseModel):
    scenario_id: str
    scenario_type: MetaverseSimulationType
    question: str
    affected_rooms: list[str]
    propagation_edges: list[str]
    risk_delta: float
    revenue_impact_percent: float
    burnout_delta: float
    productivity_delta: float
    recovery_timeline: list[str]
    recommended_actions: list[str]
    digital_twin_evidence: list[str]
    confidence: float = Field(ge=0, le=1)
    source_systems: list[str]


class MetaverseVoiceCommandRequest(BaseModel):
    command: str = Field(default="Show highest risk department.", min_length=2, max_length=500)
    session_id: str = Field(default="enterprise-metaverse-control-room", max_length=120)


class MetaverseNavigationState(BaseModel):
    selected_room_id: str
    action: MetaverseNavigationAction
    camera_target: MetaverseVector3
    camera_position: MetaverseVector3
    route: list[str]
    transcript: str
    confidence: float = Field(ge=0, le=1)


class MetaverseVoiceNavigationResponse(BaseModel):
    model: str
    generated_at: datetime
    command: str
    interpreted_action: MetaverseNavigationAction
    target_room_id: str
    spoken_response: str
    navigation: MetaverseNavigationState
    visual_overlays: list[MetaverseOverlay]
    recommended_actions: list[str]
    source_systems: list[str]
    storage: str


class MetaverseDigitalTwinSync(BaseModel):
    twin: Literal["employee", "team", "department", "project", "company", "client"]
    status: Literal["synced", "degraded", "missing"]
    update_rule: str
    latest_signal: str
    room_ids: list[str]


class MetaversePerformanceStatus(BaseModel):
    renderer: str
    estimated_fps: int = Field(ge=1, le=240)
    draw_calls: int = Field(ge=0)
    instanced_meshes: int = Field(ge=0)
    room_count: int = Field(ge=0)
    overlay_count: int = Field(ge=0)
    asset_strategy: str
    scalability_target: str
    status: Literal["ready", "degraded", "missing"]


class MetaverseSummary(BaseModel):
    room_count: int = Field(ge=0)
    department_rooms: int = Field(ge=0)
    team_rooms: int = Field(ge=0)
    data_rooms: int = Field(ge=0)
    active_overlays: int = Field(ge=0)
    agent_avatars: int = Field(ge=0)
    company_health_score: float = Field(ge=0, le=100)
    highest_risk_score: float = Field(ge=0, le=100)
    production_readiness_score: float = Field(ge=0, le=100)
    innovation_score: float = Field(ge=0, le=100)
    judge_wow_factor_score: float = Field(ge=0, le=100)
    stream_sequence: int = 1


class MetaverseControlRoomRequest(BaseModel):
    selected_room_id: str = Field(default="executive-command-center", max_length=120)
    include_agents: bool = True
    include_simulation: bool = True
    realtime: bool = True


class EnterpriseMetaverseControlRoomResponse(BaseModel):
    model: str
    generated_at: datetime
    experience_name: str
    executive_brief: str
    summary: MetaverseSummary
    rooms: list[MetaverseRoom]
    connections: list[MetaverseConnection]
    overlays: list[MetaverseOverlay]
    agent_avatars: list[MetaverseAgentAvatar]
    navigation: MetaverseNavigationState
    simulation: MetaverseSimulationImpact | None
    digital_twin_sync: list[MetaverseDigitalTwinSync]
    performance: MetaversePerformanceStatus
    voice_commands: list[str]
    recommendations: list[str]
    source_systems: list[str]
    final_verdict: str = "ENTERPRISE METAVERSE CONTROL ROOM COMPLETE"
    storage: str
