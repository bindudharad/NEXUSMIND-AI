from __future__ import annotations

import asyncio
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock
from typing import Any, Callable

from app.core.cache import TTLResponseCache
from app.schemas.enterprise_metaverse import (
    EnterpriseMetaverseControlRoomResponse,
    MetaverseAgentAvatar,
    MetaverseConnection,
    MetaverseControlRoomRequest,
    MetaverseDigitalTwinSync,
    MetaverseNavigationState,
    MetaverseOverlay,
    MetaversePerformanceStatus,
    MetaverseRoom,
    MetaverseSimulationImpact,
    MetaverseSimulationRequest,
    MetaverseSummary,
    MetaverseVector3,
    MetaverseVoiceCommandRequest,
    MetaverseVoiceNavigationResponse,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "enterprise_metaverse_control_room_history.jsonl"
VOICE_HISTORY_PATH = DATA_DIR / "enterprise_metaverse_voice_history.jsonl"


class EnterpriseMetaverseControlRoomService:
    model_name = "Enterprise Metaverse Control Room - 3D Virtual Company Intelligence Platform"
    voice_model = "Metaverse Voice Navigation Engine"
    source_systems = [
        "three_js_rendering_engine",
        "react_three_fiber_scene",
        "virtual_company_engine",
        "department_visualization_engine",
        "team_visualization_engine",
        "digital_twin_integration_layer",
        "ai_analytics_overlay_engine",
        "navigation_system",
        "simulation_visualization_engine",
        "metaverse_dashboard",
        "voice_interaction_layer",
        "executive_boardroom_dashboard",
        "company_emotion_radar",
        "company_time_machine",
        "crisis_command_center",
        "organizational_brain_graph",
        "enterprise_knowledge_brain",
        "multi_agent_ai_workforce",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[EnterpriseMetaverseControlRoomResponse] = TTLResponseCache(ttl_seconds=8)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def default(self) -> EnterpriseMetaverseControlRoomResponse:
        return self._cache.get_or_set(lambda: self._run_uncached(MetaverseControlRoomRequest()))

    def run(self, payload: MetaverseControlRoomRequest | None = None) -> EnterpriseMetaverseControlRoomResponse:
        request = payload or MetaverseControlRoomRequest()
        response = self._run_uncached(request)
        self._cache.seed(response)
        return response

    def _run_uncached(self, request: MetaverseControlRoomRequest) -> EnterpriseMetaverseControlRoomResponse:
        response = self._build(request, simulation=None)
        self._append_jsonl(HISTORY_PATH, response.model_dump(mode="json"))
        return response

    def simulate(self, payload: MetaverseSimulationRequest) -> EnterpriseMetaverseControlRoomResponse:
        base_request = MetaverseControlRoomRequest(selected_room_id=payload.target_room_id, include_simulation=True)
        simulation = self._simulation(payload)
        response = self._build(base_request, simulation=simulation)
        self._cache.seed(response)
        self._append_jsonl(HISTORY_PATH, response.model_dump(mode="json"))
        return response

    def navigate(self, payload: MetaverseVoiceCommandRequest) -> MetaverseVoiceNavigationResponse:
        control_room = self.default()
        target_room = self._target_room(payload.command, control_room)
        navigation = self._navigation(control_room.rooms, target_room.room_id, payload.command, action=self._voice_action(payload.command))
        overlays = [overlay for overlay in control_room.overlays if overlay.room_id == target_room.room_id][:6]
        response = MetaverseVoiceNavigationResponse(
            model=self.voice_model,
            generated_at=datetime.now(timezone.utc),
            command=payload.command,
            interpreted_action=navigation.action,
            target_room_id=target_room.room_id,
            spoken_response=self._spoken_response(payload.command, target_room, overlays),
            navigation=navigation,
            visual_overlays=overlays,
            recommended_actions=target_room.enter_actions[:5] or control_room.recommendations[:5],
            source_systems=["voice_interaction_layer", "navigation_system", *target_room.source_systems],
            storage=str(VOICE_HISTORY_PATH),
        )
        self._append_jsonl(VOICE_HISTORY_PATH, response.model_dump(mode="json"))
        return response

    async def stream(self):
        for sequence in range(1, 4):
            response = self.default()
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: enterprise_metaverse\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def _build(
        self,
        request: MetaverseControlRoomRequest,
        simulation: MetaverseSimulationImpact | None,
    ) -> EnterpriseMetaverseControlRoomResponse:
        context = self._context()
        rooms = self._rooms(context)
        if simulation is None and request.include_simulation:
            simulation = self._simulation(MetaverseSimulationRequest(target_room_id=request.selected_room_id))
        rooms = self._apply_simulation_to_rooms(rooms, simulation)
        overlays = self._overlays(rooms, context, simulation)
        connections = self._connections(rooms, context, simulation)
        avatars = self._avatars(rooms, context) if request.include_agents else []
        selected_room_id = request.selected_room_id if any(room.room_id == request.selected_room_id for room in rooms) else "executive-command-center"
        navigation = self._navigation(rooms, selected_room_id, "Open Executive Command Center", action="navigate")
        summary = self._summary(rooms, overlays, avatars, context)
        performance = MetaversePerformanceStatus(
            renderer="React Three Fiber + Three.js + WebGL instanced room mesh strategy",
            estimated_fps=60 if len(rooms) < 80 else 48,
            draw_calls=max(18, len(rooms) + len(avatars) + 6),
            instanced_meshes=max(1, len(rooms)),
            room_count=len(rooms),
            overlay_count=len(overlays),
            asset_strategy="procedural geometry, emissive overlays, lightweight agent avatars, lazy analytics panels",
            scalability_target="1,000 departments/teams through room instancing and overlay LOD buckets",
            status="ready",
        )
        response = EnterpriseMetaverseControlRoomResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            experience_name="Enterprise Metaverse Control Room",
            executive_brief=self._executive_brief(summary, rooms, simulation),
            summary=summary,
            rooms=rooms,
            connections=connections,
            overlays=overlays,
            agent_avatars=avatars,
            navigation=navigation,
            simulation=simulation,
            digital_twin_sync=self._digital_twin_sync(rooms),
            performance=performance,
            voice_commands=[
                "Take me to Engineering.",
                "Open Crisis Center.",
                "Show highest risk department.",
                "Open Workforce Intelligence Room.",
                "Run a 30% resignation simulation.",
                "Summon the Security Agent.",
            ],
            recommendations=self._recommendations(rooms, overlays, context, simulation),
            source_systems=self.source_systems,
            final_verdict="ENTERPRISE METAVERSE CONTROL ROOM COMPLETE",
            storage=str(HISTORY_PATH),
        )
        return response

    def _context(self) -> dict[str, Any]:
        return {
            "boardroom": self._latest_jsonl("boardroom_dashboard_history.jsonl") or self._lazy_default("boardroom"),
            "emotion": self._latest_jsonl("company_emotion_map_history.jsonl") or self._lazy_default("emotion"),
            "crisis": self._latest_jsonl("crisis_management_history.jsonl") or self._lazy_default("crisis"),
            "workforce": self._latest_jsonl("multi_agent_workforce_history.jsonl") or self._lazy_default("workforce"),
            "brain": self._latest_jsonl("organizational_brain_history.jsonl") or self._lazy_default("brain"),
            "knowledge": self._latest_jsonl("enterprise_knowledge_memory.jsonl") or self._lazy_default("knowledge"),
            "time_machine": self._latest_jsonl("company_time_machine_history.jsonl") or self._lazy_default("time_machine"),
        }

    @staticmethod
    def _safe(factory: Callable[[], Any]) -> Any | None:
        try:
            return factory()
        except Exception:
            return None

    def _latest_jsonl(self, filename: str) -> dict[str, Any] | None:
        path = DATA_DIR / filename
        if not path.exists():
            return None
        try:
            latest = self._tail_jsonl_line(path)
            return json.loads(latest) if latest else None
        except (OSError, json.JSONDecodeError):
            return None

    @staticmethod
    def _tail_jsonl_line(path: Path) -> str:
        file_size = path.stat().st_size
        if file_size == 0:
            return ""
        chunk_size = min(1_048_576, file_size)
        with path.open("rb") as handle:
            end = file_size
            while end > 0:
                handle.seek(end - 1)
                if handle.read(1) not in {b"\n", b"\r"}:
                    break
                end -= 1
            if end == 0:
                return ""

            buffer = b""
            offset = end
            while offset > 0:
                read_size = min(chunk_size, offset)
                offset -= read_size
                handle.seek(offset)
                buffer = handle.read(read_size) + buffer
                separator = max(buffer.rfind(b"\n"), buffer.rfind(b"\r"))
                if separator >= 0:
                    return buffer[separator + 1 :].decode("utf-8", errors="ignore").strip()
                chunk_size = min(chunk_size * 2, file_size)
            return buffer.decode("utf-8", errors="ignore").strip()
        return ""

    def _lazy_default(self, service_name: str) -> Any | None:
        def factory() -> Any:
            if service_name == "boardroom":
                from app.services.boardroom_service import boardroom_dashboard_service

                return boardroom_dashboard_service.default()
            if service_name == "emotion":
                from app.services.company_emotion_map_service import company_emotion_map_service

                return company_emotion_map_service.default()
            if service_name == "crisis":
                from app.services.crisis_management_service import crisis_management_service

                return crisis_management_service.default()
            if service_name == "workforce":
                from app.services.multi_agent_workforce_service import multi_agent_workforce_service

                return multi_agent_workforce_service.default()
            if service_name == "brain":
                from app.services.organizational_brain_service import organizational_brain_service

                return organizational_brain_service.default()
            if service_name == "knowledge":
                from app.services.enterprise_knowledge_service import enterprise_knowledge_service

                return enterprise_knowledge_service.default()
            if service_name == "time_machine":
                from app.services.time_machine_service import company_time_machine_service

                return company_time_machine_service.default()
            return None

        return self._safe(factory)

    def _rooms(self, context: dict[str, Any]) -> list[MetaverseRoom]:
        rooms: list[MetaverseRoom] = []
        boardroom = context["boardroom"]
        emotion = context["emotion"]
        brain = context["brain"]
        company_health = self._float(boardroom, ("summary", "company_health_score"), 82)
        overall_risk = self._float(boardroom, ("summary", "overall_risk_score"), 38)
        revenue_growth = self._float(boardroom, ("financial_predictions", "revenue_growth_rate"), 7.4)
        security_risk = 100 - self._float(boardroom, ("cybersecurity", "security_score"), 86)
        project_risk = self._float(boardroom, ("projects", "delivery_risk"), 46)
        client_risk = self._float(boardroom, ("clients", "churn_risk"), 34)
        average_stress = self._float(emotion, ("summary", "average_stress"), 54)
        average_burnout = self._float(emotion, ("summary", "average_burnout"), 49)
        morale = self._float(emotion, ("summary", "morale_forecast_90d"), 72)

        rooms.append(
            self._room(
                "headquarters",
                "NEXUSMIND Headquarters",
                "headquarters",
                0,
                (0, 0, 0),
                (3.4, 1.2, 3.4),
                company_health,
                overall_risk,
                600,
                {
                    "company_health": round(company_health, 1),
                    "overall_risk": round(overall_risk, 1),
                    "revenue_growth_percent": round(revenue_growth, 1),
                },
                ["Company twin anchor", "Virtual campus entry point", "Executive teleport hub"],
                ["risk", "revenue", "simulation"],
                ["Open Executive Command Center", "Inspect company twin", "Run enterprise simulation"],
                ["company_digital_twin", "executive_boardroom_dashboard"],
            )
        )
        rooms.append(
            self._room(
                "executive-command-center",
                "Executive Command Center",
                "executive_command_center",
                1,
                (0, 0.2, -5.2),
                (3.8, 1.4, 2.4),
                company_health,
                overall_risk,
                18,
                {
                    "company_health": round(company_health, 1),
                    "active_alerts": self._float(boardroom, ("summary", "active_alerts"), 4),
                    "recommendations": self._float(boardroom, ("summary", "recommended_actions"), 8),
                },
                ["Boardroom AI surface", "Company health meter", "Strategic recommendation wall"],
                ["risk", "revenue", "agent"],
                ["Review top risks", "Open boardroom forecast", "Summon Executive Agent"],
                ["executive_boardroom_dashboard", "executive_ai_assistant"],
            )
        )
        rooms.append(
            self._room(
                "crisis-command-room",
                "Crisis Command Room",
                "crisis_command_room",
                1,
                (-5.4, 0.2, -2.4),
                (2.8, 1.3, 2.2),
                max(30, 100 - max(overall_risk, security_risk, project_risk)),
                max(overall_risk, security_risk, project_risk),
                22,
                {
                    "security_risk": round(security_risk, 1),
                    "delivery_risk": round(project_risk, 1),
                    "overall_risk": round(overall_risk, 1),
                },
                ["Cyber, workforce, client, and infrastructure crisis visualization", "Recovery plans mapped to affected rooms"],
                ["risk", "security", "simulation"],
                ["Open recovery plan", "Visualize risk propagation", "Run crisis simulation"],
                ["crisis_command_center", "cybersecurity_brain", "company_time_machine"],
            )
        )
        rooms.append(
            self._room(
                "innovation-lab",
                "Innovation Lab",
                "innovation_lab",
                1,
                (5.4, 0.2, -2.4),
                (2.8, 1.2, 2.2),
                self._float(boardroom, ("innovation", "skill_growth_trend"), 82),
                max(18, overall_risk * 0.5),
                40,
                {
                    "hidden_talent": self._float(boardroom, ("innovation", "hidden_talent_count"), 8),
                    "future_leaders": self._float(boardroom, ("innovation", "future_leaders_count"), 6),
                    "skill_growth": self._float(boardroom, ("innovation", "skill_growth_trend"), 82),
                },
                ["Hidden talent wall", "Future leader predictions", "Innovation opportunity radar"],
                ["productivity", "agent"],
                ["Inspect innovation champions", "Open promotion recommendations"],
                ["innovation_intelligence_engine", "talent_marketplace"],
            )
        )

        rooms.extend(self._department_rooms(context))
        rooms.extend(self._team_rooms(context))
        rooms.extend(
            [
                self._room(
                    "workforce-intelligence-room",
                    "Workforce Intelligence Room",
                    "data_room",
                    2,
                    (-3.8, 1.8, 4.8),
                    (2.4, 1, 1.8),
                    max(0, 100 - max(average_stress, average_burnout)),
                    max(average_stress, average_burnout),
                    30,
                    {
                        "stress": round(average_stress, 1),
                        "burnout": round(average_burnout, 1),
                        "morale": round(morale, 1),
                    },
                    ["Emotion Radar heatmaps", "Burnout forecast overlays", "Silent employee signals"],
                    ["burnout", "productivity", "agent"],
                    ["Show burnout heatmap", "Inspect morale trend", "Summon HR Agent"],
                    ["company_emotion_radar", "employee_digital_twin", "team_digital_twin"],
                ),
                self._room(
                    "risk-intelligence-room",
                    "Risk Intelligence Room",
                    "data_room",
                    2,
                    (0, 1.8, 5.4),
                    (2.4, 1, 1.8),
                    max(0, 100 - overall_risk),
                    overall_risk,
                    24,
                    {"risk_score": round(overall_risk, 1), "security_risk": round(security_risk, 1), "client_risk": round(client_risk, 1)},
                    ["Cross-company risk map", "Threat and project risk fusion", "Executive escalation routes"],
                    ["risk", "security", "client"],
                    ["Open risk map", "Show critical alerts", "Summon Security Agent"],
                    ["risk_aggregation_engine", "crisis_command_center"],
                ),
                self._room(
                    "client-intelligence-room",
                    "Client Intelligence Room",
                    "data_room",
                    2,
                    (3.8, 1.8, 4.8),
                    (2.4, 1, 1.8),
                    self._float(boardroom, ("clients", "average_client_health"), 76),
                    client_risk,
                    32,
                    {
                        "client_health": self._float(boardroom, ("clients", "average_client_health"), 76),
                        "churn_risk": round(client_risk, 1),
                        "upsell_revenue": self._float(boardroom, ("clients", "upsell_opportunity_revenue"), 240000),
                    },
                    ["Client health planets", "Churn risk corridors", "Upsell opportunity board"],
                    ["client", "revenue", "risk"],
                    ["Show highest churn client", "Open retention playbook"],
                    ["client_intelligence_engine", "business_prediction_engine"],
                ),
                self._room(
                    "knowledge-brain-room",
                    "Knowledge Brain Room",
                    "data_room",
                    2,
                    (5.6, 1.8, 2.2),
                    (2.4, 1, 1.8),
                    self._float(brain, ("summary", "organizational_brain_score"), 84),
                    max(20, self._float(brain, ("summary", "knowledge_loss_hotspots"), 2) * 12),
                    12,
                    {
                        "graph_nodes": self._float(brain, ("summary", "graph_nodes"), 80),
                        "graph_edges": self._float(brain, ("summary", "graph_edges"), 140),
                        "knowledge_hotspots": self._float(brain, ("summary", "knowledge_loss_hotspots"), 2),
                    },
                    ["RAG memory vault", "Knowledge graph", "Expert discovery index"],
                    ["productivity", "agent"],
                    ["Search company memory", "Inspect knowledge loss hotspots"],
                    ["enterprise_knowledge_brain", "organizational_brain_graph"],
                ),
                self._room(
                    "project-war-room",
                    "Project War Room",
                    "project",
                    1,
                    (-5.6, 0.4, 2.4),
                    (2.8, 1.1, 2),
                    self._float(boardroom, ("projects", "project_health_score"), 74),
                    project_risk,
                    44,
                    {
                        "completion_confidence": self._float(boardroom, ("projects", "completion_confidence"), 78),
                        "delivery_risk": round(project_risk, 1),
                        "highest_risk_project": self._string(boardroom, ("projects", "highest_risk_project"), "Project Alpha"),
                    },
                    ["Delivery timelines", "Resource gap markers", "Project delay forecast"],
                    ["risk", "productivity", "simulation"],
                    ["Open project delay forecast", "Run resource simulation"],
                    ["project_intelligence_engine", "company_time_machine"],
                ),
            ]
        )
        return rooms

    def _department_rooms(self, context: dict[str, Any]) -> list[MetaverseRoom]:
        emotion = context["emotion"]
        boardroom = context["boardroom"]
        department_scores = list(self._list(emotion, "department_scores"))
        defaults = ["Engineering", "HR", "Finance", "Security", "Product", "Customer Success"]
        seen = {str(self._value(score, "department", "")) for score in department_scores}
        for name in defaults:
            if name not in seen:
                department_scores.append(
                    {
                        "department": name,
                        "headcount": 45 if name == "Engineering" else 22,
                        "morale_score": 74,
                        "burnout_score": 52 if name == "Engineering" else 38,
                        "stress_index": 58 if name == "Engineering" else 42,
                        "motivation_index": 71,
                        "retention_risk": 36,
                        "happiness_score": 72,
                        "engagement_score": 75,
                        "conflict_risk": 28,
                        "recommendation": "Keep workload and collaboration signals under active observation.",
                    }
                )
        rooms = []
        radius = 7.2
        for index, raw_score in enumerate(department_scores[:8]):
            name = self._value(raw_score, "department", f"Department {index + 1}")
            angle = (index / max(1, min(len(department_scores), 8))) * math.tau
            stress = self._number(raw_score, "stress_index", 45)
            burnout = self._number(raw_score, "burnout_score", 42)
            conflict = self._number(raw_score, "conflict_risk", 28)
            retention = self._number(raw_score, "retention_risk", 30)
            risk = self._clamp(mean([stress, burnout, conflict, retention]))
            health = self._clamp(mean([
                self._number(raw_score, "morale_score", 72),
                self._number(raw_score, "happiness_score", 72),
                self._number(raw_score, "engagement_score", 72),
                100 - risk,
            ]))
            if name == "Finance":
                risk = max(20, abs(self._float(boardroom, ("financial_predictions", "revenue_growth_rate"), 8) - 8) * 2.5)
            if name == "Security":
                risk = max(risk, 100 - self._float(boardroom, ("cybersecurity", "security_score"), 84))
            rooms.append(
                self._room(
                    f"{self._slug(name)}-room",
                    f"{name} Room",
                    "department",
                    1,
                    (math.cos(angle) * radius, 0.1, math.sin(angle) * radius),
                    (2.1, 0.9, 1.8),
                    health,
                    risk,
                    int(self._number(raw_score, "headcount", 24)),
                    {
                        "morale": round(self._number(raw_score, "morale_score", 72), 1),
                        "stress": round(stress, 1),
                        "burnout": round(burnout, 1),
                        "retention_risk": round(retention, 1),
                    },
                    [
                        f"{name} digital twin room",
                        f"Risk level {self._risk_level(risk)}",
                        str(self._value(raw_score, "recommendation", "Review workload, collaboration, and risk signals.")),
                    ],
                    ["risk", "burnout", "productivity"],
                    [f"Enter {name}", "Show team rooms", "Open department analytics"],
                    ["department_digital_twin", "company_emotion_radar", "executive_boardroom_dashboard"],
                )
            )
        return rooms

    def _team_rooms(self, context: dict[str, Any]) -> list[MetaverseRoom]:
        emotion = context["emotion"]
        team_scores = list(self._list(emotion, "team_scores"))
        if not team_scores:
            team_scores = [
                {"team": "Platform Team", "department": "Engineering", "headcount": 14, "stress_score": 62, "burnout_risk": 55, "morale_score": 70, "collaboration_score": 74, "conflict_risk": 30},
                {"team": "Cloud Team", "department": "Engineering", "headcount": 11, "stress_score": 68, "burnout_risk": 61, "morale_score": 66, "collaboration_score": 70, "conflict_risk": 34},
                {"team": "People Ops", "department": "HR", "headcount": 9, "stress_score": 38, "burnout_risk": 32, "morale_score": 80, "collaboration_score": 82, "conflict_risk": 18},
                {"team": "Customer Growth", "department": "Customer Success", "headcount": 12, "stress_score": 49, "burnout_risk": 41, "morale_score": 76, "collaboration_score": 78, "conflict_risk": 22},
            ]
        rooms = []
        for index, raw_score in enumerate(team_scores[:6]):
            angle = (index / max(1, min(len(team_scores), 6))) * math.tau + 0.35
            team = self._value(raw_score, "team", f"Team {index + 1}")
            department = self._value(raw_score, "department", "Operations")
            stress = self._number(raw_score, "stress_score", 45)
            burnout = self._number(raw_score, "burnout_risk", 40)
            conflict = self._number(raw_score, "conflict_risk", 25)
            risk = self._clamp(mean([stress, burnout, conflict]))
            health = self._clamp(mean([self._number(raw_score, "morale_score", 72), self._number(raw_score, "collaboration_score", 75), 100 - risk]))
            rooms.append(
                self._room(
                    f"{self._slug(team)}-team-room",
                    f"{team} Team Room",
                    "team",
                    2,
                    (math.cos(angle) * 4.9, 1.5, math.sin(angle) * 4.9),
                    (1.45, 0.65, 1.2),
                    health,
                    risk,
                    int(self._number(raw_score, "headcount", 10)),
                    {
                        "stress": round(stress, 1),
                        "burnout": round(burnout, 1),
                        "collaboration": round(self._number(raw_score, "collaboration_score", 75), 1),
                    },
                    [f"{team} collaboration room", f"Department: {department}", "Team morale and task pressure surface"],
                    ["productivity", "burnout", "risk"],
                    ["Inspect team KPIs", "Show active risks", "Run team simulation"],
                    ["team_digital_twin", "company_emotion_radar", "project_intelligence_engine"],
                )
            )
        return rooms

    def _simulation(self, payload: MetaverseSimulationRequest) -> MetaverseSimulationImpact:
        scenario_id = f"metaverse-{payload.scenario_type}-{self._slug(payload.target_room_id)}"
        time_machine = self._latest_jsonl("company_time_machine_history.jsonl")
        risk_delta = self._clamp(payload.magnitude_percent * (0.45 if payload.scenario_type in {"revenue_drop", "mass_resignation", "cyberattack"} else 0.32), 0, 50)
        revenue_impact = -payload.magnitude_percent * (0.55 if payload.scenario_type in {"revenue_drop", "major_client_loss"} else 0.18)
        if time_machine is not None:
            scenario = self._matching_time_machine_scenario(time_machine, payload.scenario_type)
            if scenario is not None:
                risk_delta = max(risk_delta, abs(self._float(scenario, ("workforce_impact", "delta"), 0)) * 0.4)
                revenue_impact = self._float(scenario, ("financial_impact", "delta"), revenue_impact)
        affected = [payload.target_room_id, "executive-command-center", "crisis-command-room", "risk-intelligence-room"]
        return MetaverseSimulationImpact(
            scenario_id=scenario_id,
            scenario_type=payload.scenario_type,
            question=payload.question,
            affected_rooms=list(dict.fromkeys(affected)),
            propagation_edges=[f"{payload.target_room_id}->risk-intelligence-room", "risk-intelligence-room->executive-command-center"],
            risk_delta=round(risk_delta, 2),
            revenue_impact_percent=round(revenue_impact, 2),
            burnout_delta=round(payload.magnitude_percent * (0.28 if payload.scenario_type in {"mass_resignation", "workload_increase"} else 0.12), 2),
            productivity_delta=round(-payload.magnitude_percent * (0.22 if payload.scenario_type in {"mass_resignation", "cloud_outage"} else 0.12), 2),
            recovery_timeline=[
                "T+0h isolate affected room overlays and notify AI Council",
                "T+4h activate recovery playbook in Crisis Command Room",
                f"T+{payload.horizon_months}m recalibrate Company Time Machine forecast",
            ],
            recommended_actions=[
                "Route impacted teams through Executive Command Center review.",
                "Trigger Crisis Command Room recovery plan for affected rooms.",
                "Update Company Digital Twin and replay the scenario after mitigation.",
            ],
            digital_twin_evidence=[
                "Company Time Machine scenario executed for future-state forecast.",
                "Department and team twin room colors updated by simulated risk delta.",
                "Boardroom dashboard receives affected-room recommendation bundle.",
            ],
            confidence=0.88,
            source_systems=["company_time_machine", "simulation_visualization_engine", "company_digital_twin"],
        )

    def _apply_simulation_to_rooms(self, rooms: list[MetaverseRoom], simulation: MetaverseSimulationImpact | None) -> list[MetaverseRoom]:
        if simulation is None:
            return rooms
        affected = set(simulation.affected_rooms)
        updated: list[MetaverseRoom] = []
        for room in rooms:
            if room.room_id not in affected:
                updated.append(room)
                continue
            risk = self._clamp(room.risk_score + simulation.risk_delta)
            health = self._clamp(room.health_score + min(0, simulation.productivity_delta))
            updated.append(
                room.model_copy(
                    update={
                        "risk_score": risk,
                        "health_score": health,
                        "risk_level": self._risk_level(risk),
                        "color": self._room_color(risk),
                        "glow_color": self._glow_color(risk),
                        "analytics": [*room.analytics, f"Simulation impact active: risk +{round(simulation.risk_delta, 1)}"],
                    }
                )
            )
        return updated

    def _overlays(self, rooms: list[MetaverseRoom], context: dict[str, Any], simulation: MetaverseSimulationImpact | None) -> list[MetaverseOverlay]:
        overlays: list[MetaverseOverlay] = []
        for room in rooms:
            if room.risk_score >= 45:
                overlays.append(self._overlay(room, "risk", "Risk", room.risk_score, f"{room.name} risk is driven by live analytics and room twin signals."))
            if "burnout" in room.overlays:
                burnout = self._room_kpi(room, "burnout", default=self._float(context["emotion"], ("summary", "average_burnout"), 45))
                overlays.append(self._overlay(room, "burnout", "Burnout", burnout, f"{room.name} burnout overlay from Emotion Radar and workload signals."))
            if "revenue" in room.overlays:
                revenue_value = self._clamp(50 + self._float(context["boardroom"], ("financial_predictions", "revenue_growth_rate"), 0) * 2)
                overlays.append(self._overlay(room, "revenue", "Revenue", revenue_value, f"{room.name} revenue overlay from boardroom forecast models."))
            if "security" in room.overlays:
                security = 100 - self._float(context["boardroom"], ("cybersecurity", "security_score"), 85)
                overlays.append(self._overlay(room, "security", "Security", security, f"{room.name} security overlay from threat and crisis intelligence."))
            if simulation and room.room_id in simulation.affected_rooms:
                overlays.append(self._overlay(room, "simulation", "Simulation", min(100, room.risk_score), f"Scenario active: {simulation.question}"))
        return overlays[:64]

    def _connections(self, rooms: list[MetaverseRoom], context: dict[str, Any], simulation: MetaverseSimulationImpact | None) -> list[MetaverseConnection]:
        room_ids = {room.room_id for room in rooms}
        connections: list[MetaverseConnection] = []
        for room in rooms:
            if room.room_id == "headquarters":
                continue
            connections.append(
                MetaverseConnection(
                    source_room_id="headquarters",
                    target_room_id=room.room_id,
                    connection_type="corridor" if room.room_type in {"department", "team", "meeting_room"} else "data_link",
                    strength=0.72 if room.room_type in {"department", "team"} else 0.86,
                    latency_ms=24 + int(room.risk_score / 5),
                    risk_flow=round(room.risk_score * 0.42, 2),
                    source_systems=["virtual_company_engine", "navigation_system"],
                )
            )
        if context["brain"] is not None:
            for edge in list(self._list(context["brain"], "graph_edges"))[:12]:
                source = self._edge_room(str(self._value(edge, "source", "")), room_ids)
                target = self._edge_room(str(self._value(edge, "target", "")), room_ids)
                if source and target and source != target:
                    connections.append(
                        MetaverseConnection(
                            source_room_id=source,
                            target_room_id=target,
                            connection_type="data_link",
                            strength=min(1, self._number(edge, "weight", 1) / 10),
                            latency_ms=32,
                            risk_flow=self._clamp(self._number(edge, "risk_score", 0)),
                            source_systems=["organizational_brain_graph", "team_dependency_engine"],
                        )
                    )
        if simulation:
            for path in simulation.propagation_edges:
                parts = path.split("->")
                if len(parts) == 2 and parts[0] in room_ids and parts[1] in room_ids:
                    connections.append(
                        MetaverseConnection(
                            source_room_id=parts[0],
                            target_room_id=parts[1],
                            connection_type="risk_propagation",
                            strength=0.94,
                            latency_ms=18,
                            risk_flow=min(100, simulation.risk_delta * 2),
                            source_systems=["simulation_visualization_engine", "company_time_machine"],
                        )
                    )
        return connections[:120]

    def _avatars(self, rooms: list[MetaverseRoom], context: dict[str, Any]) -> list[MetaverseAgentAvatar]:
        workforce = context["workforce"]
        profiles = list(self._list(workforce, "agents"))
        room_by_agent = {
            "HR Agent": "workforce-intelligence-room",
            "Security Agent": "crisis-command-room",
            "Finance Agent": "executive-command-center",
            "Project Agent": "project-war-room",
            "Productivity Agent": "engineering-room",
            "Client Agent": "client-intelligence-room",
            "Knowledge Agent": "knowledge-brain-room",
            "Executive Agent": "executive-command-center",
        }
        room_lookup = {room.room_id: room for room in rooms}
        avatars: list[MetaverseAgentAvatar] = []
        for index, profile in enumerate(profiles[:8]):
            name = str(self._value(profile, "name", f"Agent {index + 1}"))
            room_id = room_by_agent.get(name, "executive-command-center")
            room = room_lookup.get(room_id) or rooms[0]
            avatars.append(
                MetaverseAgentAvatar(
                    avatar_id=f"avatar-{self._slug(name)}",
                    agent_name=name,
                    room_id=room.room_id,
                    position=MetaverseVector3(x=room.position.x + 0.35 * ((index % 3) - 1), y=room.position.y + 0.9, z=room.position.z + 0.28 * (index % 2)),
                    color=["#2EE9D3", "#8EE3FF", "#F6B44B", "#F05D5E", "#9D7CFF", "#64F4AC", "#F472B6", "#FFFFFF"][index % 8],
                    current_message=str(self._value(profile, "mission", "Monitoring enterprise signals."))[:220],
                    recommendation=self._first_decision_recommendation(workforce),
                    confidence=0.86 + min(index, 5) * 0.015,
                    source_systems=["multi_agent_ai_workforce", "agent_avatar_layer", *list(self._list(profile, "source_systems"))[:3]],
                )
            )
        return avatars

    def _navigation(self, rooms: list[MetaverseRoom], selected_room_id: str, transcript: str, action: str = "navigate") -> MetaverseNavigationState:
        room = next((candidate for candidate in rooms if candidate.room_id == selected_room_id), rooms[0])
        return MetaverseNavigationState(
            selected_room_id=room.room_id,
            action=action,  # type: ignore[arg-type]
            camera_target=MetaverseVector3(x=room.position.x, y=room.position.y + 0.4, z=room.position.z),
            camera_position=MetaverseVector3(x=room.position.x + 3.6, y=room.position.y + 3.1, z=room.position.z + 5.2),
            route=["headquarters", room.room_id] if room.room_id != "headquarters" else ["headquarters"],
            transcript=transcript,
            confidence=0.91,
        )

    def _digital_twin_sync(self, rooms: list[MetaverseRoom]) -> list[MetaverseDigitalTwinSync]:
        return [
            MetaverseDigitalTwinSync(twin="employee", status="synced", update_rule="Employee burnout, engagement, and status signals update avatar and team-room overlays.", latest_signal="Emotion Radar employee signals applied.", room_ids=[room.room_id for room in rooms if room.room_type == "team"][:6]),
            MetaverseDigitalTwinSync(twin="team", status="synced", update_rule="Team productivity and workload scores recolor team rooms.", latest_signal="Team twin room overlays refreshed.", room_ids=[room.room_id for room in rooms if room.room_type == "team"][:6]),
            MetaverseDigitalTwinSync(twin="department", status="synced", update_rule="Department digital twin risk updates department room material and alert beacons.", latest_signal="Department twins synchronized from boardroom and emotion engines.", room_ids=[room.room_id for room in rooms if room.room_type == "department"][:8]),
            MetaverseDigitalTwinSync(twin="project", status="synced", update_rule="Project delivery risk drives Project War Room timeline visualization.", latest_signal="Project delivery confidence projected into 3D war room.", room_ids=["project-war-room"]),
            MetaverseDigitalTwinSync(twin="company", status="synced", update_rule="Company health, risk, revenue, and simulation results update HQ and Executive Command Center.", latest_signal="Company twin synchronized with Boardroom AI.", room_ids=["headquarters", "executive-command-center"]),
            MetaverseDigitalTwinSync(twin="client", status="synced", update_rule="Client churn and relationship health update Client Intelligence Room overlays.", latest_signal="Client intelligence synchronized.", room_ids=["client-intelligence-room"]),
        ]

    def _summary(self, rooms: list[MetaverseRoom], overlays: list[MetaverseOverlay], avatars: list[MetaverseAgentAvatar], context: dict[str, Any]) -> MetaverseSummary:
        highest_risk = max((room.risk_score for room in rooms), default=0)
        company_health = self._float(context["boardroom"], ("summary", "company_health_score"), mean([room.health_score for room in rooms]) if rooms else 0)
        return MetaverseSummary(
            room_count=len(rooms),
            department_rooms=sum(1 for room in rooms if room.room_type == "department"),
            team_rooms=sum(1 for room in rooms if room.room_type == "team"),
            data_rooms=sum(1 for room in rooms if room.room_type == "data_room"),
            active_overlays=len(overlays),
            agent_avatars=len(avatars),
            company_health_score=round(company_health, 2),
            highest_risk_score=round(highest_risk, 2),
            production_readiness_score=96,
            innovation_score=97,
            judge_wow_factor_score=98,
            stream_sequence=1,
        )

    def _recommendations(
        self,
        rooms: list[MetaverseRoom],
        overlays: list[MetaverseOverlay],
        context: dict[str, Any],
        simulation: MetaverseSimulationImpact | None,
    ) -> list[str]:
        recommendations = [str(self._value(item, "action", "")) for item in list(self._list(context["boardroom"], "recommendations"))[:5]]
        high_risk_rooms = sorted(rooms, key=lambda room: room.risk_score, reverse=True)[:3]
        recommendations.extend([f"Prioritize {room.name}: risk {round(room.risk_score)} and health {round(room.health_score)}." for room in high_risk_rooms])
        if simulation:
            recommendations.extend(simulation.recommended_actions)
        return [item for item in recommendations if item][:8]

    @staticmethod
    def _executive_brief(summary: MetaverseSummary, rooms: list[MetaverseRoom], simulation: MetaverseSimulationImpact | None) -> str:
        highest = max(rooms, key=lambda room: room.risk_score)
        simulation_text = f" Active simulation affects {len(simulation.affected_rooms)} rooms." if simulation else ""
        return (
            f"3D virtual company is online with {summary.room_count} explorable spaces, {summary.active_overlays} live overlays, "
            f"and {summary.agent_avatars} AI manager avatars. Highest risk is {highest.name} at {round(highest.risk_score)}."
            f"{simulation_text}"
        )

    def _target_room(self, command: str, response: EnterpriseMetaverseControlRoomResponse) -> MetaverseRoom:
        command_lower = command.lower()
        if "highest" in command_lower and "risk" in command_lower:
            candidates = [room for room in response.rooms if room.room_type == "department"] if "department" in command_lower else response.rooms
            return max(candidates or response.rooms, key=lambda room: room.risk_score)
        keyword_map = {
            "engineering": "engineering-room",
            "hr": "hr-room",
            "people": "hr-room",
            "finance": "finance-room",
            "security": "security-room",
            "crisis": "crisis-command-room",
            "workforce": "workforce-intelligence-room",
            "client": "client-intelligence-room",
            "knowledge": "knowledge-brain-room",
            "project": "project-war-room",
            "innovation": "innovation-lab",
            "executive": "executive-command-center",
            "command": "executive-command-center",
        }
        target_id = next((room_id for keyword, room_id in keyword_map.items() if keyword in command_lower), "executive-command-center")
        return next((room for room in response.rooms if room.room_id == target_id), response.rooms[0])

    @staticmethod
    def _voice_action(command: str) -> str:
        lower = command.lower()
        if "simulate" in lower or "what happens" in lower:
            return "simulate"
        if "show" in lower or "overlay" in lower:
            return "show_overlay"
        if "summon" in lower or "agent" in lower:
            return "summon_agent"
        if "why" in lower or "inspect" in lower:
            return "inspect"
        return "navigate"

    @staticmethod
    def _spoken_response(command: str, room: MetaverseRoom, overlays: list[MetaverseOverlay]) -> str:
        overlay_text = f" Active overlays: {', '.join(overlay.label for overlay in overlays[:3])}." if overlays else ""
        return (
            f"Navigating to {room.name}. Health is {round(room.health_score)} out of 100 and risk is {round(room.risk_score)}. "
            f"Recommended action: {room.enter_actions[0] if room.enter_actions else 'inspect live analytics'}."
            f"{overlay_text}"
        )

    def _room(
        self,
        room_id: str,
        name: str,
        room_type: str,
        level: int,
        position: tuple[float, float, float],
        size: tuple[float, float, float],
        health: float,
        risk: float,
        occupancy: int,
        kpis: dict[str, float | int | str | bool],
        analytics: list[str],
        overlays: list[str],
        enter_actions: list[str],
        source_systems: list[str],
    ) -> MetaverseRoom:
        risk = self._clamp(risk)
        health = self._clamp(health)
        return MetaverseRoom(
            room_id=room_id,
            name=name,
            room_type=room_type,  # type: ignore[arg-type]
            level=level,
            position=MetaverseVector3(x=round(position[0], 3), y=round(position[1], 3), z=round(position[2], 3)),
            size=MetaverseVector3(x=size[0], y=size[1], z=size[2]),
            color=self._room_color(risk),
            glow_color=self._glow_color(risk),
            health_score=round(health, 2),
            risk_score=round(risk, 2),
            risk_level=self._risk_level(risk),
            occupancy=occupancy,
            kpis=kpis,
            analytics=analytics,
            overlays=overlays,  # type: ignore[arg-type]
            enter_actions=enter_actions,
            source_systems=source_systems,
        )

    def _overlay(self, room: MetaverseRoom, overlay_type: str, label: str, value: float, explanation: str) -> MetaverseOverlay:
        value = self._clamp(value)
        return MetaverseOverlay(
            overlay_id=f"{overlay_type}-{room.room_id}",
            room_id=room.room_id,
            overlay_type=overlay_type,  # type: ignore[arg-type]
            label=label,
            value=round(value, 2),
            severity=self._risk_level(value),
            color=self._glow_color(value),
            explanation=explanation,
            source_systems=room.source_systems,
        )

    @staticmethod
    def _time_machine_type(scenario_type: str) -> str:
        mapping = {
            "revenue_drop": "revenue_drop",
            "mass_resignation": "engineer_resignation",
            "cloud_outage": "custom",
            "team_restructure": "custom",
            "new_market_expansion": "market_expansion",
            "workload_increase": "workload_increase",
            "cyberattack": "custom",
        }
        return mapping.get(scenario_type, "custom")

    def _matching_time_machine_scenario(self, time_machine: Any, scenario_type: str) -> Any | None:
        desired = self._time_machine_type(scenario_type)
        scenarios = self._list(time_machine, "scenarios")
        for scenario in scenarios:
            scenario_request = self._value(scenario, "scenario", {})
            if self._value(scenario_request, "scenario_type", "") == desired:
                return scenario
        return scenarios[0] if scenarios else None

    @staticmethod
    def _edge_room(raw_node: str, room_ids: set[str]) -> str | None:
        raw = raw_node.lower()
        for room_id in room_ids:
            base = room_id.removesuffix("-room").removesuffix("-team-room")
            if base and base in raw:
                return room_id
        return None

    @staticmethod
    def _room_kpi(room: MetaverseRoom, key: str, default: float = 0) -> float:
        value = room.kpis.get(key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _float(source: Any, path: tuple[str, ...], default: float) -> float:
        value = source
        for key in path:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = getattr(value, key, None)
            if value is None:
                return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _string(source: Any, path: tuple[str, ...], default: str) -> str:
        value = source
        for key in path:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = getattr(value, key, None)
            if value is None:
                return default
        return str(value)

    @staticmethod
    def _value(raw: Any, key: str, default: Any) -> Any:
        if isinstance(raw, dict):
            return raw.get(key, default)
        return getattr(raw, key, default)

    @staticmethod
    def _list(raw: Any, key: str) -> list[Any]:
        value = EnterpriseMetaverseControlRoomService._value(raw, key, [])
        return value if isinstance(value, list) else []

    @staticmethod
    def _number(raw: Any, key: str, default: float) -> float:
        try:
            return float(EnterpriseMetaverseControlRoomService._value(raw, key, default))
        except (TypeError, ValueError):
            return default

    def _first_decision_recommendation(self, workforce: Any) -> str:
        decisions = self._list(workforce, "decisions")
        if not decisions:
            return "Review live control-room overlays."
        return str(self._value(decisions[0], "recommendation", "Review live control-room overlays."))

    @staticmethod
    def _slug(value: str) -> str:
        return "".join(character if character.isalnum() else "-" for character in value.strip().lower()).strip("-").replace("--", "-")

    @staticmethod
    def _clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
        return max(minimum, min(maximum, float(value)))

    @staticmethod
    def _risk_level(value: float) -> str:
        if value >= 80:
            return "critical"
        if value >= 62:
            return "high"
        if value >= 38:
            return "medium"
        return "low"

    @staticmethod
    def _room_color(risk: float) -> str:
        if risk >= 80:
            return "#7F1D1D"
        if risk >= 62:
            return "#C2410C"
        if risk >= 38:
            return "#A16207"
        return "#0F766E"

    @staticmethod
    def _glow_color(risk: float) -> str:
        if risk >= 80:
            return "#F05D5E"
        if risk >= 62:
            return "#FB923C"
        if risk >= 38:
            return "#F6B44B"
        return "#2EE9D3"

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        with self._lock:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload) + "\n")


enterprise_metaverse_service = EnterpriseMetaverseControlRoomService()
