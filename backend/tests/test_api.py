import json
import math
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.security import decode_access_token
from app.main import app
from app.workers.realtime import run_once


client = TestClient(app)


def auth_token() -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ceo@nexusmind.ai", "password": "nexusmind-demo"},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token()}"}


def test_production_startup_rejects_default_demo_passwords(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import main as main_module

    monkeypatch.setattr(main_module.settings, "environment", "production")
    monkeypatch.setattr(main_module.settings, "jwt_secret_key", "production-secret")
    monkeypatch.setattr(main_module.settings, "demo_ceo_password", "nexusmind-demo")
    monkeypatch.setattr(main_module.settings, "demo_admin_password", "rotated-admin-secret")

    with pytest.raises(RuntimeError, match="Demo user passwords"):
        main_module.create_app()


def voice_samples(stressed: bool, sample_rate: int = 16000, seconds: float = 2.2) -> list[float]:
    samples = []
    length = int(sample_rate * seconds)
    for index in range(length):
        time = index / sample_rate
        if stressed:
            modulation = 1 + 0.28 * math.sin(2 * math.pi * 7.2 * time)
            variable_pitch = 255 + 42 * math.sin(2 * math.pi * 4.8 * time)
            voice = 0.28 * modulation * math.sin(2 * math.pi * variable_pitch * time)
            tension = 0.05 * math.sin(2 * math.pi * 1160 * time) + 0.035 * math.sin(2 * math.pi * 1450 * time)
            tremor = 0.025 * math.sin(2 * math.pi * 11 * time)
            samples.append(round(max(-1, min(1, voice + tension + tremor)), 5))
        else:
            calm = 0.15 * math.sin(2 * math.pi * 178 * time) + 0.015 * math.sin(2 * math.pi * 3.2 * time)
            samples.append(round(calm, 5))
    return samples


def project_history(crisis: bool) -> list[dict[str, object]]:
    points = []
    for index in range(7):
        if crisis:
            velocity = 0.52 - index * 0.025
            completion = 0.49 - index * 0.022
            burnout = 0.78 + index * 0.02
            communication = 0.45 - index * 0.016
            resource = 0.46 - index * 0.012
            dependency = 8 + index // 2
            risks = 18 + index
            scope = 0.55 + index * 0.012
            defect = 0.34 + index * 0.006
            rework = 0.31 + index * 0.006
            meeting = 0.82
            budget = 1.12 + index * 0.014
            compatibility = 0.43 - index * 0.009
        else:
            velocity = 0.76 + index * 0.012
            completion = 0.78 + index * 0.01
            burnout = 0.24 - index * 0.006
            communication = 0.82 + index * 0.008
            resource = 0.82 + index * 0.006
            dependency = 1
            risks = 2 + index // 3
            scope = 0.08 + index * 0.004
            defect = 0.06 + index * 0.002
            rework = 0.05 + index * 0.002
            meeting = 0.27
            budget = 0.48 + index * 0.006
            compatibility = 0.84
        points.append(
            {
                "timestamp": f"2026-05-{10 + index:02d}T09:00:00Z",
                "sprint_velocity": max(0, min(1, velocity)),
                "task_completion_rate": max(0, min(1, completion)),
                "scope_change_rate": max(0, min(1, scope)),
                "defect_rate": max(0, min(1, defect)),
                "rework_ratio": max(0, min(1, rework)),
                "dependency_bottlenecks": dependency,
                "resource_allocation": max(0, min(1, resource)),
                "budget_burn_rate": min(1.5, budget),
                "meeting_load": meeting,
                "communication_score": max(0, min(1, communication)),
                "team_burnout": max(0, min(1, burnout)),
                "team_compatibility": max(0, min(1, compatibility)),
                "open_risks": risks,
            }
        )
    return points


def test_health_and_readiness() -> None:
    assert client.get("/health").status_code == 200
    response = client.get("/api/v1/system/readiness")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["services"]["ai_boardroom_dashboard"] is True
    assert payload["services"]["voice_controlled_enterprise_ai"] is True
    assert payload["services"]["ai_organizational_structure_optimizer"] is True
    assert payload["services"]["realtime_crisis_management_ai"] is True
    assert payload["services"]["multi_agent_ai_workforce"] is True
    assert payload["services"]["judge_impact_validation"] is True
    assert payload["services"]["unified_autonomous_enterprise_system"] is True
    assert payload["services"]["self_learning_company_ai"] is True
    assert payload["services"]["self_evolving_ai_system"] is True
    assert payload["services"]["ultimate_autonomous_enterprise_platform"] is True
    assert payload["services"]["research_grade_autonomous_enterprise_platform"] is True
    assert payload["services"]["ai_company_time_machine"] is True
    assert payload["services"]["virtual_employee_generator"] is True
    assert payload["services"]["enterprise_metaverse_control_room"] is True
    assert payload["services"]["judge_demo_mode"] is True
    assert payload["services"]["cinematic_competition_demo"] is True
    assert payload["services"]["ai_powered_enterprise_simulation_os"] is True
    assert payload["services"]["judge_winning_innovation_stack"] is True
    assert payload["services"]["innovation_stack_verifier"] is True
    assert payload["services"]["competition_innovation_stack_auditor"] is True
    assert payload["services"]["ultimate_feature_coverage_auditor"] is True
    assert payload["services"]["feature_groups_a_to_p_auditor"] is True
    assert payload["services"]["autonomous_enterprise_intelligence_digital_twin_platform"] is True
    assert payload["services"]["living_ai_company_brain"] is True
    assert payload["services"]["living_company_brain_integration_layer"] is True


def test_core_intelligence_endpoints() -> None:
    headers = auth_headers()
    endpoints = [
        "/api/v1/dashboard/overview",
        "/api/v1/boardroom/default",
        "/api/v1/employees/dashboard/default",
        "/api/v1/attrition/default",
        "/api/v1/hiring/default",
        "/api/v1/interviews/smart/default",
        "/api/v1/managers/dashboard/default",
        "/api/v1/meetings/default",
        "/api/v1/productivity/default",
        "/api/v1/resources/allocation/default",
        "/api/v1/compensation/default",
        "/api/v1/learning/default",
        "/api/v1/talent/marketplace/default",
        "/api/v1/communication/default",
        "/api/v1/innovation/default",
        "/api/v1/company-health/default",
        "/api/v1/emotion/map/default",
        "/api/v1/decisions/default",
        "/api/v1/clients/satisfaction/default",
        "/api/v1/knowledge/loss/default",
        "/api/v1/benchmarks/companies/default",
        "/api/v1/work-life/balance/default",
        "/api/v1/genai/hr/default",
        "/api/v1/voice/default",
        "/api/v1/voice/copilot/default",
        "/api/v1/wellness/default",
        "/api/v1/teams/compatibility/default",
        "/api/v1/teams/builder/default",
        "/api/v1/projects/failure/default",
        "/api/v1/roi/default",
        "/api/v1/strategic/enterprise",
        "/api/v1/organization/optimizer/default",
        "/api/v1/crisis/management/default",
        "/api/v1/agents/workforce/default",
        "/api/v1/metaverse/control-room/default",
        "/api/v1/competitive/intelligence/default",
        "/api/v1/recruiter-impression/summary",
        "/api/v1/judge-impact/validation",
        "/api/v1/ultimate-feature-coverage/audit",
        "/api/v1/unified-enterprise/verification",
        "/api/v1/living-company-brain/default",
        "/api/v1/self-learning/verification",
        "/api/v1/ultimate-platform/verification",
        "/api/v1/research-grade/verification",
        "/api/v1/time-machine/default",
        "/api/v1/workforce/virtual-employees/default",
        "/api/v1/power/audit",
        "/api/v1/workflows/autonomous/default",
        "/api/v1/simulation/company-lab/default",
        "/api/v1/intelligence/overview",
        "/api/v1/intelligence/models/validation",
        "/api/v1/intelligence/agents/council",
        "/api/v1/intelligence/org-brain",
        "/api/v1/nlp/trends",
        "/api/v1/forecasting/workload/default",
        "/api/v1/recommendations/default",
        "/api/v1/suggestions/feed",
        "/api/v1/anomalies/default",
        "/api/v1/alerts/feed",
        "/api/v1/system/technology-stack",
        "/api/v1/system/advanced-features",
        "/api/v1/system/enterprise-ai-features",
        "/api/v1/platform/operating-system",
        "/api/v1/platform/ecosystem-audit",
    ]
    for endpoint in endpoints:
        response = client.get(endpoint, headers=headers)
        assert response.status_code == 200


def test_multi_agent_council_exposes_required_agents_memory_and_workflows() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/intelligence/agents/council", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    agents = {turn["agent"]: turn for turn in payload["turns"]}
    required_agents = {
        "HR Agent",
        "Security Agent",
        "Finance Agent",
        "Productivity Agent",
        "Project Agent",
        "Hiring Agent",
        "Wellness Agent",
        "Knowledge Agent",
        "Executive Agent",
        "Executive Decision Agent",
    }
    assert required_agents.issubset(agents)
    assert payload["coordination_score"] >= 85
    assert len(payload["workflow_triggers"]) >= len(required_agents)
    for name in required_agents:
        assert agents[name]["memory_keys"]
        assert agents[name]["tool_calls"]
        assert agents[name]["workflow_trigger"]

    workforce = client.get("/api/v1/agents/workforce/default", headers=headers)
    assert workforce.status_code == 200
    workforce_payload = workforce.json()
    required_workforce_agents = {
        "HR Agent",
        "Security Agent",
        "Finance Agent",
        "Project Agent",
        "Productivity Agent",
        "Client Agent",
        "Knowledge Agent",
        "Executive Agent",
    }
    profile_agents = {agent["name"] for agent in workforce_payload["agents"]}
    assert profile_agents == required_workforce_agents
    assert workforce_payload["summary"]["active_agents"] == 8
    assert workforce_payload["summary"]["coordination_score"] >= 90
    assert workforce_payload["summary"]["production_readiness_score"] >= 95
    assert workforce_payload["summary"]["innovation_score"] >= 90
    assert len(workforce_payload["messages"]) >= 8
    assert len(workforce_payload["memory"]) >= 8
    assert len(workforce_payload["tool_executions"]) >= 8
    assert len(workforce_payload["autonomous_tasks"]) >= 8
    assert len(workforce_payload["workflows"]) >= 4
    assert workforce_payload["decisions"]
    assert workforce_payload["simulations"]
    assert workforce_payload["boardroom_stages"]
    assert workforce_payload["consensus"]
    assert workforce_payload["reasoning_traces"]
    assert workforce_payload["debate_exchanges"]
    assert workforce_payload["consensus_votes"]
    assert workforce_payload["research_metrics"]
    assert len(workforce_payload["analytics"]) >= 8
    assert workforce_payload["communication_bus"]["status"] == "ready"
    assert workforce_payload["communication_bus"]["message_count"] >= 8
    assert workforce_payload["shared_memory_status"]["status"] == "ready"
    assert workforce_payload["shared_memory_status"]["persistent"] is True
    assert workforce_payload["monitoring"]["status"] == "ready"
    assert workforce_payload["monitoring"]["average_success_rate"] >= 90
    assert all(item["status"] == "enforced" for item in workforce_payload["security_controls"])
    assert workforce_payload["final_verdict"] == "AUTONOMOUS AI MANAGERS COMPLETE"
    assert {stage["agent"] for stage in workforce_payload["boardroom_stages"]} == required_workforce_agents
    assert workforce_payload["consensus"]["owner_agent"] == "Executive Agent"
    assert workforce_payload["consensus"]["recommended_actions"]
    assert workforce_payload["consensus"]["digital_twin_evidence"]
    assert workforce_payload["consensus"]["simulation_evidence"]
    assert workforce_payload["consensus"]["majority_vote"] in {"support", "conditional_support", "oppose"}
    assert workforce_payload["consensus"]["risk_weighted_score"] > 0
    assert workforce_payload["consensus"]["agreement_level"] in {"low", "medium", "high", "unanimous"}
    assert workforce_payload["consensus"]["conflict_resolution_summary"]
    assert {trace["agent"] for trace in workforce_payload["reasoning_traces"]} == required_workforce_agents
    assert {vote["agent"] for vote in workforce_payload["consensus_votes"]} == required_workforce_agents
    assert any(exchange["resolution"] in {"conditional", "escalated"} for exchange in workforce_payload["debate_exchanges"])
    assert workforce_payload["research_metrics"]["perspective_diversity_score"] >= 95
    assert workforce_payload["research_metrics"]["evidence_coverage_score"] >= 80
    assert workforce_payload["research_metrics"]["disagreement_count"] >= 4
    assert workforce_payload["research_metrics"]["negotiation_rounds"] == len(workforce_payload["debate_exchanges"])
    assert "Evidence-only reasoning trace" in workforce_payload["research_metrics"]["reasoning_abstraction_layer"]
    assert Path(workforce_payload["storage"]).exists()
    assert {
        "agent_registry",
        "master_orchestrator",
        "agent_communication_layer",
        "agent_shared_memory",
        "agent_event_bus",
        "agent_task_router",
        "agent_tool_access_framework",
        "agent_decision_engine",
        "agent_output_validation",
        "agent_simulation_framework",
        "multi_agent_simulation_engine",
        "agent_performance_analytics",
        "agent_monitoring_system",
        "executive_ai_council",
        "multi_agent_dashboard",
        "agent_debate_engine",
        "agent_negotiation_engine",
        "conflict_resolution_engine",
        "consensus_scoring_engine",
        "decision_explainability_engine",
        "reasoning_abstraction_layer",
        "multi_perspective_analysis_engine",
        "research_boardroom_visualization",
        "employee_digital_twin",
        "team_digital_twin",
        "department_digital_twin",
        "project_digital_twin",
        "company_digital_twin",
    }.issubset(set(workforce_payload["source_systems"]))
    for agent in workforce_payload["agents"]:
        assert agent["deployable_endpoint"].startswith("/api/v1/agents/workforce/")
        assert agent["tool_permissions"]
        assert agent["memory_keys"]
        assert agent["system_prompt"]
        assert agent["context_management"]
        assert agent["decision_logic"]
        assert agent["output_validation"]

    answer = client.post(
        "/api/v1/agents/workforce/ask",
        headers=headers,
        json={"question": "Why is company health declining?", "include_simulation": True},
    )
    assert answer.status_code == 200
    answer_payload = answer.json()
    assert answer_payload["intent"] == "company_health"
    assert {"Finance Agent", "HR Agent", "Productivity Agent", "Client Agent", "Executive Agent"}.issubset(
        set(answer_payload["participating_agents"])
    )
    assert answer_payload["decisions"]
    assert answer_payload["boardroom_stages"]
    assert answer_payload["consensus"]["owner_agent"] == "Executive Agent"
    assert answer_payload["reasoning_traces"]
    assert answer_payload["debate_exchanges"]
    assert answer_payload["consensus_votes"]
    assert answer_payload["research_metrics"]["evidence_coverage_score"] >= 80
    assert answer_payload["confidence"] > 0.75
    assert answer_payload["final_verdict"] == "AUTONOMOUS AI MANAGERS COMPLETE"

    boardroom_answer = client.post(
        "/api/v1/agents/workforce/ask",
        headers=headers,
        json={"question": "What if 30 engineers resign tomorrow?", "include_simulation": True},
    )
    assert boardroom_answer.status_code == 200
    boardroom_answer_payload = boardroom_answer.json()
    assert boardroom_answer_payload["intent"] == "simulation"
    assert boardroom_answer_payload["simulation"]["question"] == "What if 30 engineers resign tomorrow?"
    assert set(boardroom_answer_payload["simulation"]["participating_agents"]) == required_workforce_agents
    assert boardroom_answer_payload["simulation"]["delay_probability"] > 0
    assert boardroom_answer_payload["simulation"]["burnout_delta"] > 0
    assert {stage["agent"] for stage in boardroom_answer_payload["boardroom_stages"]} == required_workforce_agents
    assert boardroom_answer_payload["consensus"]["final_decision"]
    assert boardroom_answer_payload["consensus"]["recommended_actions"]
    assert boardroom_answer_payload["consensus"]["conflict_resolution_summary"]
    assert {trace["agent"] for trace in boardroom_answer_payload["reasoning_traces"]} == required_workforce_agents
    assert {vote["agent"] for vote in boardroom_answer_payload["consensus_votes"]} == required_workforce_agents
    debate_pairs = {(exchange["from_agent"], exchange["to_agent"]) for exchange in boardroom_answer_payload["debate_exchanges"]}
    assert ("HR Agent", "Finance Agent") in debate_pairs
    assert ("Security Agent", "HR Agent") in debate_pairs
    assert ("Knowledge Agent", "Project Agent") in debate_pairs
    assert boardroom_answer_payload["research_metrics"]["disagreement_count"] == len(boardroom_answer_payload["debate_exchanges"])
    assert boardroom_answer_payload["research_metrics"]["consensus_score"] >= 80

    simulation = client.post(
        "/api/v1/agents/workforce/simulate",
        headers=headers,
        json={
            "question": "What if 30 engineers resign tomorrow?",
            "scenario_type": "workforce_change",
            "resignation_count": 30,
            "workload_delta_percent": 42,
        },
    )
    assert simulation.status_code == 200
    simulation_payload = simulation.json()
    assert simulation_payload["simulations"][0]["scenario_type"] == "workforce_change"
    assert set(simulation_payload["simulations"][0]["participating_agents"]) == required_workforce_agents
    assert simulation_payload["simulations"][0]["digital_twin_evidence"]
    assert simulation_payload["topic"] == "What if 30 engineers resign tomorrow?"
    assert {stage["agent"] for stage in simulation_payload["boardroom_stages"]} == required_workforce_agents
    assert simulation_payload["consensus"]["owner_agent"] == "Executive Agent"
    assert simulation_payload["consensus"]["recommended_actions"]
    assert simulation_payload["consensus"]["risk_weighted_score"] > 0
    assert {trace["agent"] for trace in simulation_payload["reasoning_traces"]} == required_workforce_agents
    assert {vote["agent"] for vote in simulation_payload["consensus_votes"]} == required_workforce_agents
    assert simulation_payload["research_metrics"]["perspective_diversity_score"] >= 95
    assert simulation_payload["research_metrics"]["disagreement_count"] >= 4
    assert simulation_payload["research_metrics"]["conflict_resolution_status"] in {"resolved", "partially_resolved", "unresolved"}
    assert any("Security Agent" in item for item in simulation_payload["consensus"]["dissenting_risks"]) or any(
        stage["agent"] == "Security Agent" for stage in simulation_payload["boardroom_stages"]
    )

    profile = client.get("/api/v1/agents/workforce/hr", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["name"] == "HR Agent"

    stream = client.get("/api/v1/agents/workforce/stream", headers=headers)
    assert stream.status_code == 200
    assert "event: multi_agent_workforce" in stream.text
    assert "NEXUSMIND Multi-Agent AI Workforce" in stream.text


def test_enterprise_metaverse_control_room_renders_virtual_company_simulation_voice_and_streams() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/metaverse/control-room/default", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["final_verdict"] == "ENTERPRISE METAVERSE CONTROL ROOM COMPLETE"
    assert payload["summary"]["room_count"] >= 18
    assert payload["summary"]["department_rooms"] >= 5
    assert payload["summary"]["team_rooms"] >= 4
    assert payload["summary"]["data_rooms"] >= 4
    assert payload["summary"]["active_overlays"] >= 10
    assert payload["summary"]["agent_avatars"] == 8
    assert payload["summary"]["production_readiness_score"] >= 95
    assert payload["summary"]["innovation_score"] >= 95
    assert payload["summary"]["judge_wow_factor_score"] >= 95
    assert payload["performance"]["status"] == "ready"
    assert payload["performance"]["renderer"].startswith("React Three Fiber")
    room_ids = {room["room_id"] for room in payload["rooms"]}
    assert {
        "headquarters",
        "executive-command-center",
        "crisis-command-room",
        "innovation-lab",
        "workforce-intelligence-room",
        "risk-intelligence-room",
        "client-intelligence-room",
        "knowledge-brain-room",
        "project-war-room",
    }.issubset(room_ids)
    assert any(room["room_type"] == "department" and room["overlays"] for room in payload["rooms"])
    assert any(overlay["overlay_type"] in {"risk", "burnout", "simulation"} for overlay in payload["overlays"])
    assert all(sync["status"] == "synced" for sync in payload["digital_twin_sync"])
    assert {"three_js_rendering_engine", "digital_twin_integration_layer", "multi_agent_ai_workforce"}.issubset(
        set(payload["source_systems"])
    )

    simulation = client.post(
        "/api/v1/metaverse/control-room/simulate",
        headers=headers,
        json={
            "scenario_type": "mass_resignation",
            "question": "What happens if 30% of Engineering resigns?",
            "target_room_id": "engineering-room",
            "magnitude_percent": 30,
            "horizon_months": 6,
        },
    )
    assert simulation.status_code == 200
    simulation_payload = simulation.json()
    assert simulation_payload["simulation"]["scenario_type"] == "mass_resignation"
    assert "engineering-room" in simulation_payload["simulation"]["affected_rooms"]
    assert simulation_payload["simulation"]["propagation_edges"]
    assert any(overlay["overlay_type"] == "simulation" for overlay in simulation_payload["overlays"])

    voice = client.post(
        "/api/v1/metaverse/control-room/voice",
        headers=headers,
        json={"command": "Show highest risk department."},
    )
    assert voice.status_code == 200
    voice_payload = voice.json()
    department_ids = {room["room_id"] for room in payload["rooms"] if room["room_type"] == "department"}
    assert voice_payload["target_room_id"] in department_ids
    assert voice_payload["spoken_response"]
    assert voice_payload["navigation"]["route"]

    stream = client.get("/api/v1/metaverse/control-room/stream", headers=headers)
    assert stream.status_code == 200
    assert "event: enterprise_metaverse" in stream.text
    assert "Enterprise Metaverse Control Room" in stream.text


def test_boardroom_dashboard_is_service_derived_not_static_fallback() -> None:
    response = client.get("/api/v1/dashboard/overview", headers=auth_headers())
    assert response.status_code == 200
    payload = response.json()
    metric_labels = {metric["label"] for metric in payload["metrics"]}
    assert {"Productivity", "Employee Wellness", "Security Posture", "Revenue Forecast", "Project Health", "Team Throughput"}.issubset(metric_labels)
    assert len(payload["forecast_series"]) >= 3
    assert payload["forecast_series"][0]["label"] not in {"Jan", "Feb", "Mar"}
    assert any(signal["id"].startswith("risk-forecast-") for signal in payload["risk_signals"])
    assert any(message["agent"] == "Executive Agent" for message in payload["agent_messages"])


def test_ai_boardroom_dashboard_aggregates_jarvis_layers_assistant_and_stream() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/boardroom/default", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert "JARVIS" in payload["dashboard_name"]
    assert payload["summary"]["connected_engines"] >= 12
    assert payload["company_health"]["score"] > 0
    assert len(payload["kpis"]) >= 8
    risk_categories = {item["category"] for item in payload["executive_risks"]}
    assert {
        "Burnout Risk",
        "Client Risk",
        "Cybersecurity Risk",
        "Project Risk",
        "Revenue Risk",
        "Competitive Risk",
        "Talent Flight Risk",
    }.issubset(risk_categories)
    assert payload["financial_predictions"]["monthly_forecast"]
    assert payload["workforce"]["burnout_hotspots"]
    assert payload["cybersecurity"]["active_threats"] >= 0
    assert payload["projects"]["delivery_forecast"]
    assert payload["clients"]["highest_churn_risk_client"]
    assert payload["competitive"]["top_threat"]
    assert payload["innovation"]["innovation_champions"]
    assert payload["digital_twin"]["company_twin_status"] == "synchronized"
    assert payload["alerts"]
    assert payload["recommendations"]
    assert {
        "executive_dashboard",
        "real_time_data_layer",
        "ai_insights_engine",
        "risk_aggregation_engine",
        "executive_recommendation_engine",
        "company_digital_twin",
        "executive_ai_assistant",
        "forecasting_integration",
    }.issubset(set(payload["source_systems"]))

    assistant = client.post(
        "/api/v1/boardroom/assistant",
        headers=headers,
        json={"question": "Which risk should I solve first?"},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["intent"] == "risk"
    assert "risk" in assistant_payload["answer"].lower()
    assert assistant_payload["cited_panels"]
    assert assistant_payload["cited_evidence"]
    assert assistant_payload["recommended_actions"]

    with client.stream("GET", "/api/v1/boardroom/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: boardroom" in first_chunk
        assert "company_health" in first_chunk


def test_realtime_worker_entrypoint_generates_operational_snapshot() -> None:
    import asyncio

    snapshot = asyncio.run(run_once(publish=False))
    assert snapshot["stream"] == "nexusmind.enterprise.realtime"
    assert snapshot["platform"]["ready"] == snapshot["platform"]["capabilities"]
    assert snapshot["strategic"]["marketplace_matches"] >= 1


def test_technology_stack_verification_reports_real_integrations() -> None:
    response = client.get("/api/v1/system/technology-stack")
    assert response.status_code == 200
    payload = response.json()
    names = {check["name"]: check for check in payload["checks"]}
    expected = {
        "React",
        "Next.js",
        "Python",
        "FastAPI",
        "TensorFlow",
        "Scikit-learn",
        "Hugging Face Transformers",
        "PostgreSQL",
        "MongoDB",
        "Docker",
        "AWS Readiness",
        "Redis",
        "Qdrant Vector Database",
        "Neo4j Graph Database",
        "Kubernetes",
        "GitHub Actions CI/CD",
        "Nginx Gateway",
        "Kafka Streaming",
        "Spark Analytics",
        "Azure Readiness",
        "LangChain / RAG Orchestration",
        "LLM API Adapter",
    }
    assert expected.issubset(names)
    for name in ["React", "Next.js", "Python", "FastAPI", "Scikit-learn", "Hugging Face Transformers"]:
        assert names[name]["status"] == "ready"
    for name in ["TensorFlow", "PostgreSQL", "MongoDB", "Docker", "AWS Readiness"]:
        assert names[name]["status"] in {"ready", "configured"}
    for name in [
        "Redis",
        "Qdrant Vector Database",
        "Neo4j Graph Database",
        "Kafka Streaming",
        "Spark Analytics",
        "Azure Readiness",
        "LangChain / RAG Orchestration",
        "LLM API Adapter",
    ]:
        assert names[name]["status"] in {"ready", "configured"}
    assert payload["summary"]["production_ready_score"] >= 70
    assert payload["summary"]["missing"] == 0
    assert payload["summary"]["errors"] == 0


def test_jwt_rbac_and_tenant_scope_are_exposed() -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "ceo@nexusmind.ai", "password": "nexusmind-demo"},
    )
    assert login.status_code == 200
    payload = login.json()
    token_claims = decode_access_token(payload["access_token"])
    assert token_claims["role"] == "CEO"
    assert token_claims["tenant_id"] == "tenant_nexusmind_demo"
    assert payload["user"]["tenant_id"] == "tenant_nexusmind_demo"

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {payload['access_token']}"})
    assert me.status_code == 200
    assert me.json()["tenant_id"] == "tenant_nexusmind_demo"


def test_registration_password_reset_and_logout_flows() -> None:
    email = f"stability-{uuid4().hex[:8]}@nexusmind.ai"
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "initial-secure-password",
            "full_name": "Stability Audit User",
            "role": "Manager",
            "department": "Quality",
        },
    )
    assert register.status_code == 201
    token = register.json()["access_token"]

    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "initial-secure-password",
            "full_name": "Stability Audit User",
            "role": "Manager",
            "department": "Quality",
        },
    )
    assert duplicate.status_code == 409

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email

    reset = client.post("/api/v1/auth/password-reset/request", json={"email": email})
    assert reset.status_code == 200
    reset_token = reset.json()["reset_token"]
    assert reset_token

    confirm = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"reset_token": reset_token, "new_password": "rotated-secure-password"},
    )
    assert confirm.status_code == 200

    old_login = client.post("/api/v1/auth/login", json={"email": email, "password": "initial-secure-password"})
    assert old_login.status_code == 401
    new_login = client.post("/api/v1/auth/login", json={"email": email, "password": "rotated-secure-password"})
    assert new_login.status_code == 200

    logout = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {new_login.json()['access_token']}"})
    assert logout.status_code == 200
    assert logout.json()["revoked"] is True

    revoked = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_login.json()['access_token']}"})
    assert revoked.status_code == 401


def test_master_feature_coverage_verifies_original_scope() -> None:
    response = client.get("/api/v1/system/feature-coverage")
    assert response.status_code == 200
    payload = response.json()
    names = {check["name"]: check for check in payload["checks"]}
    expected = {
        "Random Forest burnout model",
        "XGBoost burnout model",
        "Neural network risk models",
        "NLP sentiment and emotion analysis",
        "Time-series workload forecasting",
        "Recommendation AI",
        "Behavioral anomaly detection",
        "Employee dashboard",
        "Manager dashboard",
        "AI alert system",
        "Smart suggestion engine",
        "Technology stack integration",
        "Realtime streaming systems",
        "Database and historical analytics",
        "Enterprise UI/UX coverage",
        "Original idea prediction coverage",
    }
    assert expected.issubset(names)
    assert payload["summary"]["coverage_score"] >= 85
    assert payload["summary"]["missing"] == 0
    assert payload["summary"]["errors"] == 0
    assert payload["critical_gaps"] == []
    for name in [
        "Random Forest burnout model",
        "XGBoost burnout model",
        "NLP sentiment and emotion analysis",
        "Time-series workload forecasting",
        "Recommendation AI",
        "Behavioral anomaly detection",
        "Employee dashboard",
        "Manager dashboard",
        "AI alert system",
        "Smart suggestion engine",
        "Original idea prediction coverage",
    ]:
        assert names[name]["status"] == "ready"


def test_advanced_feature_audit_verifies_impressive_layer() -> None:
    response = client.get("/api/v1/system/advanced-features")
    assert response.status_code == 200
    payload = response.json()
    names = {check["name"]: check for check in payload["checks"]}
    expected = {
        "Digital Twin / Shadow Company AI",
        "AI CEO Assistant Voice Layer",
        "Voice-Controlled Enterprise AI / JARVIS for CEOs",
        "AI Boardroom Dashboard / JARVIS for Companies",
        "Multi-Agent AI Workforce",
        "Enterprise Time Machine",
        "AI Company Simulation Lab",
        "AI Internal Talent Marketplace",
        "Company Emotion Map",
        "AI Innovation Detector",
        "AI Organizational Structure Optimizer",
        "Realtime Crisis Management AI",
        "Realtime Emotion Heatmap",
        "3D Enterprise Control Room",
        "Realtime AI Alert System",
        "Smart Suggestion Engine",
        "Self-Learning AI System",
        "Enterprise Knowledge AI",
        "Cybersecurity AI",
        "AI Meeting Analyzer",
        "Voice Stress Detection AI",
        "Team Compatibility AI",
        "AI Project Failure Prediction",
        "Enterprise ROI Intelligence",
        "Real-time Analytics Power Layer",
        "Explainable AI / XAI",
        "Graph Neural Networks for Team Relations",
        "Generative AI Manager Assistant",
        "Realtime AI Infrastructure",
        "Cinematic Enterprise UI",
    }
    assert expected.issubset(names)
    assert payload["summary"]["coverage_score"] >= 88
    assert payload["summary"]["missing"] == 0
    assert payload["summary"]["errors"] == 0
    assert payload["critical_gaps"] == []
    for name in expected - {"Self-Learning AI System"}:
        assert names[name]["status"] == "ready"
    assert names["Self-Learning AI System"]["status"] in {"ready", "warning"}


def test_enterprise_ai_operating_system_audit_verifies_fortune_500_layer() -> None:
    response = client.get("/api/v1/system/enterprise-ai-features")
    assert response.status_code == 200
    payload = response.json()
    names = {check["name"]: check for check in payload["checks"]}
    expected = {
        "Digital Twin AI",
        "Multi-Agent AI System",
        "Generative AI CEO Assistant",
        "Enterprise What-If Engine",
        "AI Company Simulation Lab",
        "AI Internal Talent Marketplace",
        "Company Emotion Map",
        "Enterprise Memory + Knowledge AI",
        "AI Security Intelligence",
        "3D Enterprise Control Room",
        "Self-Learning AI System",
        "AI Decision Intelligence",
        "Realtime Enterprise Infrastructure",
        "Frontend Enterprise UI",
        "API & Backend Enterprise Layer",
        "Database & Vector Systems",
    }
    assert expected.issubset(names)
    assert payload["summary"]["coverage_score"] >= 92
    assert payload["summary"]["missing"] == 0
    assert payload["summary"]["errors"] == 0
    assert payload["critical_gaps"] == []
    for name in expected - {"Self-Learning AI System", "Database & Vector Systems"}:
        assert names[name]["status"] == "ready"
    assert names["Multi-Agent AI System"]["status"] == "ready"
    assert "Executive Agent" in " ".join(names["Multi-Agent AI System"]["evidence"])
    assert names["Self-Learning AI System"]["status"] in {"ready", "warning"}
    assert names["Database & Vector Systems"]["status"] in {"ready", "warning"}


def test_complete_platform_operating_system_covers_all_required_product_and_infra_features() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/platform/operating-system", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    names = {capability["name"]: capability for capability in payload["capabilities"]}
    expected_products = {
        "AI Boardroom Dashboard / JARVIS for Companies",
        "Multi-Agent AI Workforce",
        "AI Attrition Prediction",
        "Smart Hiring AI",
        "AI Smart Interviewer",
        "AI Team Builder",
        "AI Competitive Intelligence System",
        "AI Client Relationship Intelligence",
        "AI Internal Talent Marketplace",
        "AI Organizational Structure Optimizer",
        "Realtime Crisis Management AI",
        "AI Innovation Detector",
        "Meeting Waste Detector",
        "Employee Mental Wellness AI",
        "Company Emotion Map",
        "Productivity Leakage Detector",
        "AI Resource Allocation",
        "Project Failure Prediction",
        "AI Salary Recommendation",
        "Fraud & Insider Threat Detection",
        "AI Learning Recommendation",
        "AI Communication Quality Analyzer",
        "AI Innovation Scoring",
        "Realtime Company Health Dashboard",
        "AI Decision Assistant",
        "Predictive Client Satisfaction AI",
        "AI Knowledge Loss Prevention",
        "Multi-Company Benchmarking",
        "AI Work-Life Balance Optimizer",
        "Generative AI HR Assistant",
        "Voice-Controlled Enterprise AI",
        "AI CEO Assistant",
        "Financial Intelligence Engine",
        "Digital Twin of the Company",
        "AI Company Simulation Lab",
        "Autonomous Workflow Automation System",
    }
    expected_infra = {
        "Dockerized Services",
        "Kubernetes Manifests",
        "GitHub Actions CI/CD",
        "Nginx API Gateway",
        "AWS + Azure Cloud Support",
    }
    assert expected_products.issubset(names)
    assert expected_infra.issubset(names)
    assert names["Unified Enterprise AI Core"]["status"] == "ready"
    assert {
        "executive_dashboard",
        "real_time_data_layer",
        "ai_insights_engine",
        "risk_aggregation_engine",
        "executive_recommendation_engine",
        "company_digital_twin",
        "executive_ai_assistant",
        "forecasting_integration",
    }.issubset(set(names["AI Boardroom Dashboard / JARVIS for Companies"]["source_systems"]))
    assert names["Unified Enterprise AI Core"]["category"] == "ai_core"
    assert names["Multi-Agent AI Workforce"]["category"] == "ai_core"
    assert {
        "master_orchestrator",
        "agent_communication_layer",
        "agent_shared_memory",
        "agent_event_bus",
        "agent_tool_access_framework",
        "agent_decision_engine",
        "agent_simulation_framework",
        "agent_performance_analytics",
        "executive_ai_council",
        "multi_agent_dashboard",
        "employee_digital_twin",
        "team_digital_twin",
        "department_digital_twin",
        "project_digital_twin",
        "company_digital_twin",
    }.issubset(set(names["Multi-Agent AI Workforce"]["source_systems"]))
    assert "multi_agent_orchestration" in names["Unified Enterprise AI Core"]["source_systems"]
    assert "financial_roi_intelligence" in names["AI CEO Assistant"]["source_systems"]
    assert {
        "speech_recognition_engine",
        "voice_command_engine",
        "llm_assistant_engine",
        "text_to_speech_engine",
        "context_memory_engine",
        "enterprise_analytics_connector",
        "executive_dashboard_integration",
    }.issubset(set(names["Voice-Controlled Enterprise AI"]["source_systems"]))
    assert "revenue_exposure_model" in names["Financial Intelligence Engine"]["source_systems"]
    assert "risk_propagation_engine" in names["Digital Twin of the Company"]["source_systems"]
    assert {"workflow_engine", "automation_engine", "approval_engine", "task_assignment_engine", "scheduling_engine", "multi_agent_orchestrator"}.issubset(
        set(names["Autonomous Workflow Automation System"]["source_systems"])
    )
    assert {
        "competitor_monitoring_engine",
        "market_intelligence_engine",
        "hiring_intelligence_engine",
        "technology_intelligence_engine",
        "product_launch_intelligence_engine",
        "industry_trend_analysis_engine",
        "competitive_risk_engine",
        "executive_strategy_engine",
        "competitive_ai_assistant",
    }.issubset(set(names["AI Competitive Intelligence System"]["source_systems"]))
    assert {
        "interview_engine",
        "question_generation_engine",
        "resume_analysis_engine",
        "candidate_scoring_engine",
        "voice_confidence_engine",
        "cheating_detection_engine",
        "interview_report_generator",
        "smart_interview_dashboard",
    }.issubset(set(names["AI Smart Interviewer"]["source_systems"]))
    assert {
        "emotion_analytics_engine",
        "sentiment_analysis_engine",
        "burnout_prediction_engine",
        "conflict_detection_engine",
        "organizational_heatmap_engine",
        "emotion_ai_assistant",
        "company_digital_twin",
        "workflow_automation",
    }.issubset(set(names["Company Emotion Map"]["source_systems"]))
    assert {
        "innovation_analytics_engine",
        "leadership_potential_engine",
        "creativity_intelligence_engine",
        "problem_solving_intelligence_engine",
        "talent_discovery_engine",
        "employee_growth_engine",
        "future_leader_prediction_engine",
        "innovation_ai_assistant",
        "talent_marketplace",
        "employee_digital_twin",
    }.issubset(set(names["AI Innovation Detector"]["source_systems"]))
    assert {
        "organizational_analytics_engine",
        "graph_ai_engine",
        "reporting_structure_analyzer",
        "team_optimization_engine",
        "collaboration_intelligence_engine",
        "communication_flow_analyzer",
        "organizational_simulation_engine",
        "organizational_ai_assistant",
    }.issubset(set(names["AI Organizational Structure Optimizer"]["source_systems"]))
    assert {
        "crisis_detection_engine",
        "incident_classification_engine",
        "crisis_severity_engine",
        "recovery_planning_engine",
        "risk_containment_engine",
        "business_continuity_engine",
        "crisis_simulation_engine",
        "executive_alert_engine",
        "crisis_ai_assistant",
        "company_digital_twin",
        "cybersecurity_brain",
        "client_intelligence",
    }.issubset(set(names["Realtime Crisis Management AI"]["source_systems"]))
    assert {"simulation_engine", "decision_engine", "forecasting_engine", "impact_analysis_engine", "digital_twin", "ai_simulation_assistant"}.issubset(
        set(names["AI Company Simulation Lab"]["source_systems"])
    )
    assert {"team_twin_model", "project_twin_model", "resource_twin_model", "operations_twin_model"}.issubset(
        set(names["Digital Twin of the Company"]["source_systems"])
    )
    assert {"scenario_simulation_engine", "executive_decision_engine", "impact_engine", "project_completion_prediction"}.issubset(
        set(names["Digital Twin of the Company"]["source_systems"])
    )
    assert payload["summary"]["total_capabilities"] >= 26
    assert payload["summary"]["ready"] == payload["summary"]["total_capabilities"]
    assert payload["summary"]["missing"] == 0
    assert payload["summary"]["warnings"] == 0
    assert payload["summary"]["errors"] == 0
    assert payload["summary"]["platform_score"] == 100
    assert payload["summary"]["cloud_native_score"] == 100
    assert sum(1 for capability in payload["capabilities"] if capability["category"] == "ai_product") >= 20
    assert all(names[name]["status"] == "ready" for name in expected_products | expected_infra)
    assert "NEXUSMIND AI" in payload["executive_brief"]
    assert {"Neo4j graph database configuration", "Kafka event streaming configuration", "Spark analytics configuration"}.issubset(set(payload["data_stack"]))
    assert "Tenant-scoped analytics isolation" in payload["data_stack"]
    assert {"Docker Compose", "Kubernetes manifests", "Nginx gateway config", "GitHub Actions CI", "AWS Terraform starter", "Azure deployment blueprint"}.issubset(set(payload["devops_stack"]))
    assert any("Random Forest" in item for item in payload["ai_stack"])
    assert any("Hugging Face" in item for item in payload["ai_stack"])
    assert any("LangChain" in item for item in payload["ai_stack"])
    assert any("LLM API" in item for item in payload["ai_stack"])
    assert any("AI CEO assistant" in item for item in payload["ai_stack"])
    assert any("Financial intelligence" in item for item in payload["ai_stack"])
    assert any("Company digital twin" in item for item in payload["ai_stack"])
    assert any("Virtual operations manager AI" in item for item in payload["ai_stack"])
    assert any("Multi-Agent AI Workforce" in item for item in payload["ai_stack"])
    assert any("AI Company Simulation Lab" in item for item in payload["ai_stack"])
    assert any("AI Competitive Intelligence strategic war room" in item for item in payload["ai_stack"])
    assert any("Company emotion digital twin" in item for item in payload["ai_stack"])
    assert any("Real-time crisis management AI emergency command center" in item for item in payload["ai_stack"])
    assert any("AI Boardroom Dashboard / JARVIS layer" in item for item in payload["ai_stack"])
    assert any("AI Boardroom Dashboard / JARVIS for Companies" == item for item in payload["dashboards"])
    assert any("Complete Platform Coverage Console" == item for item in payload["dashboards"])
    assert any("Unified AI Ecosystem Audit Console" == item for item in payload["dashboards"])
    assert any("AI CEO Assistant Command Center" == item for item in payload["dashboards"])
    assert any("Financial Intelligence Dashboard" == item for item in payload["dashboards"])
    assert any("Autonomous Workflow Automation Dashboard" == item for item in payload["dashboards"])
    assert any("Multi-Agent AI Workforce Command Surface" == item for item in payload["dashboards"])
    assert any("AI Company Simulation Lab" == item for item in payload["dashboards"])
    assert any("Company Emotion Map Console" == item for item in payload["dashboards"])
    assert any("Competitive Intelligence War Room" == item for item in payload["dashboards"])
    assert any("Digital Twin Simulation Lab" == item for item in payload["dashboards"])
    assert any("Talent Continuity Forecasting Console" == item for item in payload["dashboards"])
    assert any("Smart Hiring Intelligence Console" == item for item in payload["dashboards"])
    assert any("AI Smart Interviewer Console" == item for item in payload["dashboards"])
    assert any("Strategic Intelligence Command Center" == item for item in payload["dashboards"])
    assert any("Organizational Design Intelligence Console" == item for item in payload["dashboards"])
    assert any("Crisis Command Center Dashboard" == item for item in payload["dashboards"])


def test_unified_ecosystem_audit_reports_no_missing_broken_or_placeholder_features() -> None:
    response = client.get("/api/v1/platform/ecosystem-audit", headers=auth_headers())
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "NEXUSMIND Unified AI Ecosystem Auditor"
    assert payload["missing_features"] == []
    assert payload["broken_features"] == []
    assert payload["placeholder_features"] == []
    assert payload["infrastructure_problems"] == []
    assert payload["ai_core"]["one_login"] is True
    assert payload["ai_core"]["one_database_ecosystem"] is True
    assert payload["ai_core"]["one_ai_core"] is True
    assert payload["ai_core"]["one_dashboard_ecosystem"] is True
    assert payload["ai_core"]["one_agent_orchestration_layer"] is True
    assert {"AI Orchestration Layer", "Knowledge Engine", "Agent Engine", "Simulation Engine", "Workflow Automation Engine", "Business Flight Simulator", "AI Boardroom / JARVIS Executive Copilot"}.issubset(set(payload["ai_core"]["orchestration_engines"]))
    assert {
        "HR Intelligence",
        "Knowledge Intelligence",
        "Executive Intelligence",
        "Financial Intelligence",
        "Client Intelligence",
        "Digital Twin Intelligence",
        "Company Simulation Intelligence",
        "Boardroom Executive Intelligence",
    }.issubset(set(payload["ai_core"]["connected_domains"]))
    assert payload["summary"]["ready"] == payload["summary"]["total_capabilities"]
    assert "unified AI ecosystem" in payload["verdict"]


def test_ai_competitive_intelligence_runs_war_room_assistant_comparison_and_streams() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/competitive/intelligence/default", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "NEXUSMIND AI Competitive Intelligence System"
    assert payload["summary"]["competitor_count"] >= 4
    assert payload["summary"]["top_competitor_threat"]
    assert payload["summary"]["average_threat_score"] > 0
    assert payload["summary"]["product_launches_tracked"] >= 4
    assert payload["summary"]["technologies_tracked"] >= 8
    assert payload["profiles"]
    assert payload["product_launches"]
    assert payload["hiring_trends"]
    assert payload["technology_adoption"]
    assert payload["market_expansions"]
    assert payload["risk_scores"]
    assert payload["industry_trends"]
    assert payload["comparison"]
    assert payload["recommendations"]
    assert {
        "competitor_monitoring_engine",
        "market_intelligence_engine",
        "hiring_intelligence_engine",
        "technology_intelligence_engine",
        "product_launch_intelligence_engine",
        "industry_trend_analysis_engine",
        "competitive_risk_engine",
        "executive_strategy_engine",
        "competitive_ai_assistant",
    }.issubset(set(payload["source_systems"]))

    top_profile = payload["profiles"][0]
    assert top_profile["rank"] == 1
    assert top_profile["recent_activities"]
    assert top_profile["strategic_risks"]
    assert top_profile["threat_score"] == payload["risk_scores"][0]["threat_score"]

    metrics = {metric["metric"] for metric in payload["comparison"][0]["metrics"]}
    assert {"hiring_growth", "product_velocity", "technology_adoption", "innovation_rate", "workforce_growth", "market_reach"}.issubset(metrics)
    assert any("Kubernetes" in item["technologies"] or "Generative AI" in item["technologies"] for item in payload["technology_adoption"])

    custom = client.post(
        "/api/v1/competitive/intelligence/analyze",
        headers=headers,
        json={
            "horizon_months": 12,
            "competitors": [
                {
                    "company_name": "Aggressive AI Rival",
                    "industry": "Enterprise AI Operations",
                    "products": ["AI Strategic War Room", "Agentic Revenue OS"],
                    "market_position": "AI challenger",
                    "revenue_estimate_millions": 260,
                    "employee_count": 920,
                    "technology_stack": ["Kubernetes", "Generative AI", "Multi-Agent Systems", "Qdrant", "Neo4j", "Kafka"],
                    "regions": ["India", "Singapore", "UAE", "United States"],
                    "job_roles": ["AI Engineer", "MLOps Engineer", "Enterprise Seller", "Security Analyst"],
                    "hiring_growth_percent": 72,
                    "product_launches_90d": 6,
                    "ai_mentions_30d": 210,
                    "funding_signal": 0.96,
                    "partnership_signal": 0.74,
                    "pricing_pressure": 0.67,
                    "customer_sentiment": 0.71,
                    "market_share_growth": 18,
                    "technology_adoption_score": 98,
                    "product_velocity_score": 96,
                    "recent_activities": ["Announced agentic AI operating-system launch", "Opened APAC sales and AI engineering hubs"],
                },
                {
                    "company_name": "Slow Legacy Vendor",
                    "industry": "Legacy HR Software",
                    "products": ["Legacy HR Suite"],
                    "market_position": "legacy incumbent",
                    "revenue_estimate_millions": 500,
                    "employee_count": 2100,
                    "technology_stack": ["PostgreSQL", "Data Warehouse"],
                    "regions": ["United States"],
                    "job_roles": ["Customer Success Manager"],
                    "hiring_growth_percent": 3,
                    "product_launches_90d": 0,
                    "ai_mentions_30d": 6,
                    "funding_signal": 0.02,
                    "pricing_pressure": 0.2,
                    "customer_sentiment": -0.18,
                    "market_share_growth": -2,
                    "technology_adoption_score": 28,
                    "product_velocity_score": 22,
                },
            ],
        },
    )
    assert custom.status_code == 200
    custom_payload = custom.json()
    assert custom_payload["summary"]["top_competitor_threat"] == "Aggressive AI Rival"
    assert custom_payload["risk_scores"][0]["threat_score"] > custom_payload["risk_scores"][1]["threat_score"]
    assert custom_payload["hiring_trends"][0]["competitor"] == "Aggressive AI Rival"
    assert custom_payload["product_launches"][0]["competitor"] == "Aggressive AI Rival"
    assert custom_payload["market_expansions"][0]["competitor"] == "Aggressive AI Rival"
    assert any(item["priority"] in {"high", "critical"} for item in custom_payload["recommendations"])

    threat_answer = client.post(
        "/api/v1/competitive/intelligence/assistant",
        headers=headers,
        json={"question": "Show biggest competitor threat.", "horizon_months": 12},
    )
    assert threat_answer.status_code == 200
    threat_payload = threat_answer.json()
    assert threat_payload["intent"] == "threat"
    assert payload["summary"]["top_competitor_threat"] in threat_payload["answer"]
    assert threat_payload["cited_evidence"]

    tech_answer = client.post(
        "/api/v1/competitive/intelligence/assistant",
        headers=headers,
        json={"question": "Which technologies are competitors adopting?", "horizon_months": 12},
    )
    assert tech_answer.status_code == 200
    tech_payload = tech_answer.json()
    assert tech_payload["intent"] == "technology"
    assert "adopting" in tech_payload["answer"].lower()
    assert tech_payload["competitors"]

    with client.stream("GET", "/api/v1/competitive/intelligence/stream", headers=headers) as stream:
        assert stream.status_code == 200
        text = next(stream.iter_text())
        assert "event: competitive_intelligence" in text
        assert "NEXUSMIND AI Competitive Intelligence System" in text


def test_global_risk_scanner_predicts_external_company_impact_and_streams() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/global-risk/scanner/default", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["model"] == "NEXUSMIND Real-Time Global Risk Scanner - Enterprise External Intelligence Platform"
    assert payload["final_verdict"] == "REAL-TIME GLOBAL RISK SCANNER COMPLETE"
    assert payload["summary"]["events_analyzed"] >= 10
    assert payload["summary"]["high_risk_events"] >= 3
    assert payload["summary"]["production_readiness_score"] >= 95
    assert payload["summary"]["innovation_score"] >= 95
    assert payload["summary"]["judge_wow_factor_score"] >= 90
    assert payload["news_intelligence"]
    assert payload["economic_intelligence"]
    assert payload["competitor_intelligence"]
    assert payload["regulatory_intelligence"]
    assert payload["technology_intelligence"]
    assert payload["cyber_threat_intelligence"]
    assert payload["impact_predictions"]
    assert payload["risk_forecasts"]
    assert payload["alerts"]
    assert payload["recommendations"]
    assert payload["digital_twin_sync"]
    assert payload["agent_council"]
    assert payload["executive_insights"]
    assert payload["live_source_adapters"]
    assert "global_risk_scanner_history.jsonl" in payload["storage"]
    assert Path(payload["storage"]).exists()

    assert {
        "news_intelligence_engine",
        "economic_intelligence_engine",
        "competitor_intelligence_engine",
        "regulatory_intelligence_engine",
        "market_intelligence_engine",
        "technology_intelligence_engine",
        "cyber_threat_intelligence_engine",
        "impact_prediction_engine",
        "risk_forecast_engine",
        "alerting_engine",
        "company_digital_twin",
        "crisis_simulator",
        "multi_agent_workforce",
    }.issubset(set(payload["source_systems"]))
    assert any(alert["category"] == "cyber" for alert in payload["alerts"])
    assert any(forecast["horizon_label"] == "12_months" for forecast in payload["risk_forecasts"])
    assert any(impact["revenue_impact_percent"] < 0 for impact in payload["impact_predictions"])
    assert any(sync["twin"] == "company" and sync["status"] == "synced" for sync in payload["digital_twin_sync"])
    assert {"Finance Agent", "Security Agent", "Client Agent", "Strategy Agent", "Executive Agent"}.issubset(
        {agent["agent"] for agent in payload["agent_council"]}
    )

    custom = client.post(
        "/api/v1/global-risk/scanner/scan",
        headers=headers,
        json={
            "cycle_name": "Regulatory and Market Shock Review",
            "horizon_days": 365,
            "events": [
                {
                    "event_id": "custom-regulatory-ai-audit",
                    "source_type": "regulatory",
                    "title": "New AI audit law requires enterprise model evidence within six months",
                    "source_name": "Policy intelligence adapter",
                    "region": "European Union",
                    "industry": "Enterprise AI Software",
                    "summary": "Regulation raises audit, documentation, and model-risk governance obligations.",
                    "sentiment_score": -0.54,
                    "severity": 91,
                    "relevance": 97,
                    "opportunity_score": 42,
                    "keywords": ["AI audit", "model governance", "compliance"],
                    "source_url": "regulatory://custom/ai-audit-law",
                }
            ],
        },
    )
    assert custom.status_code == 200
    custom_payload = custom.json()
    assert custom_payload["cycle_name"] == "Regulatory and Market Shock Review"
    assert custom_payload["news_intelligence"][0]["event_id"] == "custom-regulatory-ai-audit"
    assert custom_payload["regulatory_intelligence"]
    assert custom_payload["risk_forecasts"][-1]["horizon_label"] == "12_months"

    inflation_answer = client.post(
        "/api/v1/global-risk/scanner/assistant",
        headers=headers,
        json={"question": "How will inflation affect revenue?", "horizon_days": 365},
    )
    assert inflation_answer.status_code == 200
    inflation_payload = inflation_answer.json()
    assert inflation_payload["intent"] == "inflation"
    assert "Economic pressure" in inflation_payload["answer"]
    assert inflation_payload["recommended_actions"]

    competitor_answer = client.post(
        "/api/v1/global-risk/scanner/assistant",
        headers=headers,
        json={"question": "What competitor is our biggest threat?", "horizon_days": 365},
    )
    assert competitor_answer.status_code == 200
    competitor_payload = competitor_answer.json()
    assert competitor_payload["intent"] == "competitor"
    assert competitor_payload["cited_events"]

    readiness = client.get("/api/v1/system/readiness")
    assert readiness.status_code == 200
    readiness_services = readiness.json()["services"]
    assert readiness_services["realtime_global_risk_scanner"] is True
    assert readiness_services["enterprise_external_intelligence_platform"] is True
    assert readiness_services["global_risk_alerting_engine"] is True

    with client.stream("GET", "/api/v1/global-risk/scanner/stream", headers=headers) as stream:
        assert stream.status_code == 200
        text = next(stream.iter_text())
        assert "event: global_risk_scanner" in text
        assert "REAL-TIME GLOBAL RISK SCANNER COMPLETE" in text


def test_ai_company_simulation_lab_runs_business_flight_simulator_scenarios_assistant_and_streams() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/simulation/company-lab/default", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "NEXUSMIND AI Company Simulation Lab"
    assert payload["summary"]["scenario_count"] >= 6
    assert payload["summary"]["recommended_scenario"]
    assert payload["summary"]["average_confidence"] >= 0.6
    assert payload["comparison"]
    assert payload["executive_recommendations"]

    scenario_types = {scenario["scenario_type"] for scenario in payload["scenarios"]}
    assert {
        "work_from_home_policy",
        "hiring_freeze",
        "employee_resignation",
        "department_restructure",
        "budget_reduction",
        "meeting_reduction",
    }.issubset(scenario_types)
    required_forecasts = {
        "Productivity Forecast",
        "Attrition Forecast",
        "Burnout Forecast",
        "Revenue Forecast",
        "Hiring Forecast",
        "Delivery Forecast",
    }
    for scenario in payload["scenarios"]:
        assert required_forecasts.issubset({forecast["metric"] for forecast in scenario["forecasts"]})
        assert scenario["risk_heatmap"]
        assert scenario["recommendations"]
        assert scenario["digital_twin_evidence"]
        assert scenario["comparison_score"] >= 0
        assert scenario["employee_movement"]
        assert scenario["team_stress_evolution"]
        assert scenario["project_health_visualization"]
        assert scenario["revenue_evolution"]
        assert scenario["risk_propagation_path"]
        assert scenario["multi_future_branches"]
        assert scenario["agent_council"]
        assert scenario["shadow_company_stages"]
        assert scenario["ai_explanation"]
        assert scenario["visualization_engine_status"] == "ready"
        assert {"simulation_engine", "forecasting_engine", "digital_twin", "ai_simulation_assistant"}.issubset(set(scenario["source_systems"]))
        assert {"best_case", "expected_case", "worst_case", "optimistic_case", "pessimistic_case", "ai_recommended_case"} == {
            branch["case_name"] for branch in scenario["multi_future_branches"]
        }
        assert {"HR Agent", "Finance Agent", "Project Agent", "Security Agent", "Executive Agent"}.issubset(
            {agent["agent"] for agent in scenario["agent_council"]}
        )
        assert {stage["stage"] for stage in scenario["shadow_company_stages"]} == {"current_company", "shadow_company", "future_company"}

    wfh = next(scenario for scenario in payload["scenarios"] if scenario["scenario_type"] == "work_from_home_policy")
    assert "work-from-home" in wfh["question"].lower()
    assert wfh["impact"]["employee_happiness_change"] < 0
    assert wfh["impact"]["attrition_risk_change"] > 0
    assert wfh["impact"]["recruitment_difficulty_change"] > 0
    assert any("hybrid" in recommendation["action"].lower() for recommendation in wfh["recommendations"])

    budget = client.post(
        "/api/v1/simulation/company-lab/simulate",
        headers=headers,
        json={
            "scenario_id": "test-budget-20",
            "scenario_type": "budget_reduction",
            "question": "What happens if budget is reduced by 20%?",
            "budget_reduction_percent": 20,
        },
    )
    assert budget.status_code == 200
    budget_payload = budget.json()
    budget_scenario = budget_payload["scenarios"][0]
    assert budget_scenario["scenario_type"] == "budget_reduction"
    assert budget_scenario["impact"]["financial_impact"] < 0
    assert budget_scenario["impact"]["revenue_impact"] < 0
    assert budget_scenario["impact"]["operational_risk_change"] > 0

    future = client.post(
        "/api/v1/simulation/company-lab/simulate",
        headers=headers,
        json={
            "scenario_id": "test-future-demo-resignation-30",
            "scenario_type": "employee_resignation",
            "question": "What happens if 30 engineers resign?",
            "resignation_count": 30,
            "resignation_seniority": "senior",
            "mode": "stress",
        },
    )
    assert future.status_code == 200
    future_scenario = future.json()["scenarios"][0]
    assert future_scenario["scenario_type"] == "employee_resignation"
    assert any(frame["exits"] >= 30 for frame in future_scenario["employee_movement"])
    assert any(item["projected_state"] in {"At Risk", "Delayed"} for item in future_scenario["project_health_visualization"])
    assert future_scenario["risk_propagation_path"][0]["title"] == "Decision Shock"
    assert future_scenario["risk_propagation_path"][-1]["target"] == "Executive Recommendation"
    assert "30 resignations" in future_scenario["ai_explanation"]
    assert future_scenario["revenue_evolution"][-1]["expected_case"] != future_scenario["revenue_evolution"][0]["expected_case"]

    assistant = client.post(
        "/api/v1/simulation/company-lab/assistant",
        headers=headers,
        json={"question": "Compare hybrid vs office-first.", "horizon_months": 12},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["intent"] == "comparison"
    assert assistant_payload["comparison"]
    assert "safest" in assistant_payload["answer"].lower()
    assert "hybrid" in assistant_payload["answer"].lower() or "remote" in assistant_payload["answer"].lower()
    assert assistant_payload["recommended_actions"]

    with client.stream("GET", "/api/v1/simulation/company-lab/stream", headers=headers) as stream:
        assert stream.status_code == 200
        text = next(stream.iter_text())
        assert "event: company_simulation_lab" in text
        assert "NEXUSMIND AI Company Simulation Lab" in text


def test_ai_company_time_machine_simulates_future_company_state_assistant_builder_and_streams() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/time-machine/default", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["model"] == "NEXUSMIND AI Company Time Machine"
    assert payload["dashboard_name"] == "AI Company Time Machine"
    assert payload["summary"]["scenario_count"] >= 5
    assert payload["summary"]["production_readiness_score"] >= 90
    assert payload["scenario_builder_templates"]
    assert {
        "company_time_machine_engine",
        "scenario_builder",
        "forecasting_engine",
        "digital_twin_engine",
        "simulation_engine",
        "risk_prediction_engine",
        "recommendation_engine",
        "multi_agent_workforce",
    }.issubset(set(payload["source_systems"]))
    assert payload["digital_twin_status"]["employees"] > 0
    assert payload["digital_twin_status"]["teams"] > 0
    assert payload["digital_twin_status"]["departments"] > 0
    assert payload["digital_twin_status"]["projects"] > 0
    assert payload["digital_twin_status"]["realtime_updates"] is True
    assert "What will happen if 25 engineers resign?" in payload["supported_questions"]

    high = client.post(
        "/api/v1/time-machine/simulate",
        headers=headers,
        json={
            "scenario_id": "pytest-workload-30",
            "scenario_name": "Pytest workload +30",
            "question": "What will happen in 6 months if employee workload increases by 30%?",
            "scenario_type": "workload_increase",
            "horizon_months": 6,
            "workload_delta_percent": 30,
        },
    )
    low = client.post(
        "/api/v1/time-machine/simulate",
        headers=headers,
        json={
            "scenario_id": "pytest-workload-5",
            "scenario_name": "Pytest workload +5",
            "question": "What will happen in 6 months if employee workload increases by 5%?",
            "scenario_type": "workload_increase",
            "horizon_months": 6,
            "workload_delta_percent": 5,
        },
    )
    assert high.status_code == 200
    assert low.status_code == 200
    high_payload = high.json()
    low_payload = low.json()
    assert high_payload["workforce_impact"]["projected"] > low_payload["workforce_impact"]["projected"]
    assert high_payload["project_impact"]["projected"] >= low_payload["project_impact"]["projected"]
    assert high_payload["timeline"][-1]["burnout_risk"] > high_payload["timeline"][0]["burnout_risk"]
    assert high_payload["timeline"][-1]["project_delay_probability"] >= high_payload["timeline"][0]["project_delay_probability"]
    assert high_payload["recommendations"]
    assert high_payload["risks"]
    assert high_payload["explanation"]["causal_drivers"]
    assert {"HR Agent", "Finance Agent", "Project Agent", "Risk Agent", "Executive Agent"}.issubset({item["agent"] for item in high_payload["agent_contributions"]})
    assert "company_time_machine_history.jsonl" in high_payload["storage"]
    assert Path(high_payload["storage"]).exists()

    scenario_id = f"pytest-market-expansion-{uuid4()}"
    created = client.post(
        "/api/v1/time-machine/scenarios",
        headers=headers,
        json={
            "scenario_id": scenario_id,
            "scenario_name": "Pytest market expansion",
            "question": "What will happen if we expand into a new market?",
            "scenario_type": "market_expansion",
            "horizon_months": 18,
            "workload_delta_percent": 14,
            "market_expansion_investment": 2500000,
        },
    )
    assert created.status_code == 200
    created_payload = created.json()
    assert created_payload["scenario"]["scenario_id"] == scenario_id
    assert created_payload["simulation"]["scenario"]["scenario_type"] == "market_expansion"
    listed = client.get("/api/v1/time-machine/scenarios", headers=headers)
    assert listed.status_code == 200
    assert scenario_id in {item["scenario_id"] for item in listed.json()}

    assistant = client.post(
        "/api/v1/time-machine/ask",
        headers=headers,
        json={"question": "What will happen if 25 engineers resign?", "horizon_months": 9},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["intent"] == "engineer_resignation"
    assert "success probability" in assistant_payload["answer"]
    assert assistant_payload["simulation"]["scenario"]["resignation_count"] == 25
    assert assistant_payload["simulation"]["project_impact"]["projected"] > 0
    assert assistant_payload["cited_evidence"]
    assert assistant_payload["recommended_actions"]

    with client.stream("GET", "/api/v1/time-machine/stream", headers=headers) as stream:
        assert stream.status_code == 200
        text = next(stream.iter_text())
        assert "event: company_time_machine" in text
        assert "NEXUSMIND AI Company Time Machine" in text


def test_what_if_decision_engine_runs_strategy_simulations_assistant_builder_and_streams() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/what-if/decision-engine/default", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["model"] == "NEXUSMIND What-If Decision Engine - Enterprise Strategy Simulator"
    assert payload["dashboard_name"] == "What-If Decision Engine"
    assert payload["final_verdict"] == "WHAT-IF DECISION ENGINE COMPLETE"
    assert payload["summary"]["scenario_count"] >= 6
    assert payload["summary"]["production_readiness_score"] >= 95
    assert payload["summary"]["innovation_score"] >= 95
    assert payload["scenario_builder_templates"]
    assert {
        "what_if_simulation_engine",
        "decision_modeling_engine",
        "business_impact_engine",
        "executive_impact_analysis_panel",
        "financial_loss_calculator",
        "delay_prediction_engine",
        "team_impact_engine",
        "recovery_strategy_engine",
        "hiring_requirements_engine",
        "workforce_impact_engine",
        "financial_impact_engine",
        "productivity_simulation_engine",
        "infrastructure_impact_engine",
        "risk_analysis_engine",
        "recommendation_engine",
        "scenario_builder",
        "strategy_ai_assistant",
        "employee_digital_twin",
        "company_digital_twin",
        "multi_agent_workforce",
    }.issubset(set(payload["source_systems"]))
    assert payload["component_status"]["Hiring Simulation"] == "working"
    assert payload["component_status"]["Executive Impact Analysis Panel"] == "working"
    assert payload["component_status"]["Financial Loss Calculator"] == "working"
    assert payload["component_status"]["Delay Prediction Engine"] == "working"
    assert payload["component_status"]["Team Impact Engine"] == "working"
    assert payload["component_status"]["Recovery Strategy Engine"] == "working"
    assert payload["component_status"]["Hiring Requirements Engine"] == "working"
    assert payload["component_status"]["Digital Twin Integration"] == "working"
    assert "What happens if we hire 50 employees?" in payload["supported_questions"]
    assert "What if 30 employees resign tomorrow?" in payload["supported_questions"]
    assert "What happens if we launch a new product?" in payload["supported_questions"]

    hire = client.post(
        "/api/v1/what-if/decision-engine/simulate",
        headers=headers,
        json={
            "scenario_id": "pytest-hire-50",
            "scenario_name": "Pytest hire 50 employees",
            "question": "What happens if we hire 50 employees?",
            "scenario_type": "hiring",
            "horizon_months": 12,
            "employee_delta": 50,
            "target_department": "Engineering",
        },
    )
    budget = client.post(
        "/api/v1/what-if/decision-engine/simulate",
        headers=headers,
        json={
            "scenario_id": "pytest-budget-cut",
            "scenario_name": "Pytest budget reduction",
            "question": "What happens if we reduce budget by 20%?",
            "scenario_type": "budget_reduction",
            "horizon_months": 12,
            "budget_delta_percent": -20,
        },
    )
    assert hire.status_code == 200
    assert budget.status_code == 200
    hire_payload = hire.json()
    budget_payload = budget.json()
    assert hire_payload["workforce_impact"][0]["projected"] > hire_payload["workforce_impact"][0]["baseline"]
    assert hire_payload["infrastructure_impact"]["workstations"] == 50
    assert hire_payload["infrastructure_impact"]["software_licenses"] == 50
    assert hire_payload["scenario_comparison"]
    assert hire_payload["future_branches"]
    assert {item["case_name"] for item in hire_payload["future_branches"]} == {
        "best_case",
        "expected_case",
        "worst_case",
        "optimistic_case",
        "pessimistic_case",
        "ai_recommended_case",
    }
    assert round(sum(item["probability"] for item in hire_payload["future_branches"])) == 100
    assert next(item for item in hire_payload["future_branches"] if item["case_name"] == "ai_recommended_case")["recommendation"]
    assert hire_payload["recommendations"]
    assert hire_payload["risk_analysis"]
    assert hire_payload["timeline"][-1]["month"] == 12
    hire_impact = hire_payload["executive_impact_analysis"]
    assert hire_impact["panel_title"] == "Executive Impact Analysis"
    assert hire_impact["final_verdict"] == "EXECUTIVE IMPACT ANALYSIS COMPLETE"
    assert hire_impact["financial_loss"] >= 0
    assert hire_impact["delay_probability"] >= 0
    assert hire_impact["most_affected_teams"]
    assert hire_impact["recovery_strategy"]["immediate_actions"]
    assert hire_impact["hiring_requirements"]["required_hires"] >= 0
    assert "HR Agent" in {item["agent"] for item in hire_impact["agent_council"]}
    assert "Finance Agent" in {item["agent"] for item in hire_impact["agent_council"]}
    assert "Project Agent" in {item["agent"] for item in hire_impact["agent_council"]}
    assert "Executive Agent" in {item["agent"] for item in hire_impact["agent_council"]}
    assert {
        "financial_loss_calculator",
        "delay_prediction_engine",
        "team_impact_engine",
        "recovery_strategy_engine",
        "hiring_requirements_engine",
        "employee_digital_twin",
        "team_digital_twin",
        "department_digital_twin",
        "project_digital_twin",
        "company_digital_twin",
    }.issubset(set(hire_impact["source_systems"]))
    assert {"HR Agent", "Finance Agent", "Project Agent", "Knowledge Agent", "Risk Agent", "Executive Agent"}.issubset(
        {item["agent"] for item in hire_payload["agent_council"]}
    )
    assert {item["twin"] for item in hire_payload["digital_twin_sync"]} == {"employee", "team", "department", "project", "company"}
    assert Path(hire_payload["storage"]).exists()
    assert hire_payload["decision_readiness_score"] != budget_payload["decision_readiness_score"]
    assert budget_payload["burnout_impact"][0]["projected"] >= budget_payload["burnout_impact"][0]["baseline"]

    scenario_id = f"pytest-what-if-expansion-{uuid4()}"
    created = client.post(
        "/api/v1/what-if/decision-engine/scenarios",
        headers=headers,
        json={
            "scenario_id": scenario_id,
            "scenario_name": "Pytest international expansion",
            "question": "What if we expand internationally?",
            "scenario_type": "international_expansion",
            "horizon_months": 18,
            "employee_delta": 40,
            "target_region": "Europe",
            "expansion_investment": 3500000,
        },
    )
    assert created.status_code == 200
    created_payload = created.json()
    assert created_payload["scenario"]["scenario_id"] == scenario_id
    assert created_payload["simulation"]["scenario"]["scenario_type"] == "international_expansion"
    listed = client.get("/api/v1/what-if/decision-engine/scenarios", headers=headers)
    assert listed.status_code == 200
    assert scenario_id in {item["scenario_id"] for item in listed.json()}

    assistant = client.post(
        "/api/v1/what-if/decision-engine/ask",
        headers=headers,
        json={"question": "What happens if we hire 50 employees?", "horizon_months": 12},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["intent"] == "hiring"
    assert "readiness" in assistant_payload["answer"]
    assert assistant_payload["simulation"]["scenario"]["employee_delta"] == 50
    assert assistant_payload["recommended_actions"]
    assert assistant_payload["cited_evidence"]

    resignation_assistant = client.post(
        "/api/v1/what-if/decision-engine/ask",
        headers=headers,
        json={"question": "What if 30 employees resign tomorrow?", "horizon_months": 12},
    )
    assert resignation_assistant.status_code == 200
    resignation_payload = resignation_assistant.json()
    assert resignation_payload["intent"] == "engineer_resignation"
    assert resignation_payload["simulation"]["scenario"]["employee_delta"] == -30
    assert resignation_payload["simulation"]["scenario"]["scenario_name"] == "30 employees resign"
    assert resignation_payload["simulation"]["workforce_impact"][0]["projected"] < resignation_payload["simulation"]["workforce_impact"][0]["baseline"]
    assert any(item["category"] == "delivery" for item in resignation_payload["simulation"]["risk_analysis"])
    resignation_impact = resignation_payload["simulation"]["executive_impact_analysis"]
    assert resignation_impact["trigger_type"] == "workforce_event"
    assert resignation_impact["financial_loss"] > 0
    assert resignation_impact["delay_probability"] > 0
    assert resignation_impact["hiring_requirements"]["required_hires"] >= 12
    assert resignation_impact["hiring_requirements"]["skills_needed"]
    assert resignation_impact["most_affected_teams"][0]["impact_score"] > 0
    assert resignation_impact["recovery_strategy"]["short_term_recovery"]
    assert resignation_impact["forecast_points"]
    assert {item["twin"] for item in resignation_payload["simulation"]["digital_twin_sync"]} == {"employee", "team", "department", "project", "company"}
    assert "Knowledge Agent" in {item["agent"] for item in resignation_payload["simulation"]["agent_council"]}
    assert next(item for item in resignation_payload["simulation"]["future_branches"] if item["case_name"] == "worst_case")["risk_score"] > 0

    with client.stream("GET", "/api/v1/what-if/decision-engine/stream", headers=headers) as stream:
        assert stream.status_code == 200
        text = next(stream.iter_text())
        assert "event: what_if_decision" in text
        assert "WHAT-IF DECISION ENGINE COMPLETE" in text

    readiness = client.get("/api/v1/system/readiness")
    assert readiness.status_code == 200
    readiness_payload = readiness.json()
    assert readiness_payload["services"]["what_if_decision_engine"] is True
    assert readiness_payload["services"]["enterprise_strategy_simulator"] is True


def test_strategic_decision_intelligence_engine_composes_future_shadow_boardroom_and_impact() -> None:
    headers = auth_headers()
    response = client.post(
        "/api/v1/strategic/decision-engine/ask",
        headers=headers,
        json={"question": "Should we reduce workforce by 20%?", "horizon_months": 12},
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["model"] == "NEXUSMIND Strategic Decision Intelligence Engine"
    assert payload["final_verdict"] == "STRATEGIC DECISION INTELLIGENCE ENGINE COMPLETE"
    assert payload["future_simulation_status"] == "working"
    assert payload["digital_twin_status"] == "working"
    assert payload["chain_reaction_status"] == "working"
    assert payload["boardroom_status"] == "working"
    assert payload["shadow_company_status"] == "working"
    assert payload["demo_mode_status"] == "working"
    assert payload["strategic_risk_score"] > 0
    assert payload["confidence_score"] >= 70
    assert "Do NOT reduce workforce by 20%" in payload["recommended_action"]

    what_if = payload["what_if_simulation"]
    shadow = payload["shadow_company_simulation"]
    assert what_if["scenario"]["scenario_type"] == "layoff"
    assert what_if["scenario"]["employee_delta"] <= -20
    assert what_if["scenario"]["scenario_name"] == "Reduce workforce by 20%"
    assert shadow["scenario"]["scenario_type"] == "budget_reduction"
    assert shadow["scenario"]["employee_delta"] <= -20
    assert shadow["simulated_outcome"]["employees"] < shadow["baseline_outcome"]["employees"]

    assert {item["twin"] for item in what_if["digital_twin_sync"]} == {"employee", "team", "department", "project", "company"}
    assert len(payload["chain_reaction"]) >= 7
    assert {item["title"] for item in payload["chain_reaction"]}.issuperset(
        {
            "Team capacity drops",
            "Workload and burnout rise",
            "Project delay risk increases",
            "Revenue risk increases",
            "Client satisfaction drops",
            "Company health falls",
        }
    )
    assert len(payload["decision_options"]) == 3
    assert any(item["recommended"] for item in payload["decision_options"])
    assert payload["impact_panel"]["financial_loss"] >= 0
    assert payload["impact_panel"]["delay_probability"] > 0
    assert payload["impact_panel"]["most_affected_teams"]
    assert payload["impact_panel"]["hiring_requirements"]["required_hires"] >= 0
    agents = {item["agent"] for item in payload["boardroom_findings"]}
    assert {"HR Agent", "Finance Agent", "Project Agent", "Security Agent", "Executive Agent"}.issubset(agents)
    assert {
        "strategic_decision_engine",
        "what_if_decision_engine",
        "shadow_company_engine",
        "chain_reaction_engine",
        "executive_impact_analysis_panel",
        "ai_boardroom",
        "company_digital_twin",
    }.issubset(set(payload["source_systems"]))

    default = client.get("/api/v1/strategic/decision-engine/default", headers=headers)
    assert default.status_code == 200
    assert default.json()["question"] == "Should we reduce workforce by 20%?"

    with client.stream("GET", "/api/v1/strategic/decision-engine/stream", headers=headers) as stream:
        assert stream.status_code == 200
        text = next(stream.iter_text())
        assert "event: strategic_decision" in text
        assert "STRATEGIC DECISION INTELLIGENCE ENGINE COMPLETE" in text


def test_virtual_employee_generator_runs_agent_based_workforce_simulation_assistant_and_streams() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/workforce/virtual-employees/default", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["model"] == "NEXUSMIND Synthetic Workforce Twin Generator + Agent-Based Enterprise Simulator"
    assert payload["summary"]["generated_employees"] >= 12
    assert payload["summary"]["readiness_score"] > 0
    assert payload["virtual_employees"]
    assert payload["team_interactions"]
    assert payload["stress_propagation"]
    assert payload["project_outcome"]["delivery_confidence"] >= 0
    assert payload["forecast"]
    assert {
        "virtual_employee_generator",
        "employee_personality_engine",
        "behavior_modeling_engine",
        "productivity_modeling_engine",
        "stress_propagation_engine",
        "team_interaction_engine",
        "project_outcome_simulator",
        "hiring_impact_engine",
        "leadership_simulation_engine",
        "employee_digital_twin",
        "company_time_machine",
        "multi_agent_workforce",
    }.issubset(set(payload["source_systems"]))
    first_employee = payload["virtual_employees"][0]
    assert first_employee["identity"]["employee_id"].startswith("vemp-")
    assert first_employee["skills"]["technical_skills"]
    assert first_employee["skills"]["soft_skills"]
    assert first_employee["skills"]["leadership_skills"]
    assert 0 <= first_employee["personality"]["big_five"]["openness"] <= 100
    assert first_employee["personality"]["communication_style"] in {"direct", "written-first", "balanced"}
    assert first_employee["work_characteristics"]["productivity_pattern"]
    assert first_employee["behavior"]["productivity_score"] >= 0
    assert "Digital Twin" in " ".join(payload["integration_evidence"])

    generated = client.post(
        "/api/v1/workforce/virtual-employees/generate",
        headers=headers,
        json={
            "count": 12,
            "department": "AI Platform",
            "role_family": "Data Science",
            "experience_mix": "senior_heavy",
            "seed": 9090,
        },
    )
    assert generated.status_code == 200
    generated_payload = generated.json()
    assert generated_payload["summary"]["generated_employees"] == 12
    assert any("Data" in item["identity"]["role"] or "ML" in item["identity"]["role"] for item in generated_payload["virtual_employees"])
    assert len({item["personality"]["introversion_extroversion"] for item in generated_payload["virtual_employees"]}) >= 2
    assert Path(generated_payload["storage"]).exists()

    low_pressure = client.post(
        "/api/v1/workforce/virtual-employees/simulate",
        headers=headers,
        json={
            "question": "Baseline workload simulation.",
            "scenario_type": "baseline",
            "employee_count": 18,
            "workload_delta_percent": 0,
            "horizon_weeks": 12,
            "seed": 3030,
        },
    )
    high_pressure = client.post(
        "/api/v1/workforce/virtual-employees/simulate",
        headers=headers,
        json={
            "question": "Show stress propagation across Engineering.",
            "scenario_type": "stress_propagation",
            "employee_count": 18,
            "workload_delta_percent": 45,
            "resignation_count": 2,
            "horizon_weeks": 12,
            "seed": 3030,
        },
    )
    assert low_pressure.status_code == 200
    assert high_pressure.status_code == 200
    low_payload = low_pressure.json()
    high_payload = high_pressure.json()
    assert high_payload["summary"]["average_stress"] > low_payload["summary"]["average_stress"]
    assert high_payload["summary"]["burnout_risk"] > low_payload["summary"]["burnout_risk"]
    assert high_payload["project_outcome"]["delivery_delay_weeks"] >= low_payload["project_outcome"]["delivery_delay_weeks"]
    assert high_payload["forecast"][-1]["stress"] > high_payload["forecast"][0]["stress"]
    assert any(edge["stress_transfer"] > 0 for edge in high_payload["stress_propagation"])

    no_hiring = client.post(
        "/api/v1/workforce/virtual-employees/simulate",
        headers=headers,
        json={
            "question": "Simulate no hiring under workload growth.",
            "scenario_type": "hiring_impact",
            "employee_count": 18,
            "hiring_count": 0,
            "workload_delta_percent": 20,
            "horizon_weeks": 12,
            "seed": 4040,
        },
    )
    hiring = client.post(
        "/api/v1/workforce/virtual-employees/simulate",
        headers=headers,
        json={
            "question": "Simulate hiring 5 engineers.",
            "scenario_type": "hiring_impact",
            "employee_count": 18,
            "hiring_count": 5,
            "workload_delta_percent": 20,
            "horizon_weeks": 12,
            "seed": 4040,
        },
    )
    assert no_hiring.status_code == 200
    assert hiring.status_code == 200
    no_hiring_payload = no_hiring.json()
    hiring_payload = hiring.json()
    assert hiring_payload["summary"]["delivery_confidence"] >= no_hiring_payload["summary"]["delivery_confidence"]
    assert hiring_payload["project_outcome"]["resource_risk"] <= no_hiring_payload["project_outcome"]["resource_risk"]
    assert hiring_payload["recommendations"]

    assistant = client.post(
        "/api/v1/workforce/virtual-employees/ask",
        headers=headers,
        json={"question": "What happens if 2 senior engineers leave?", "horizon_weeks": 12},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["intent"] == "project_outcome"
    assert "virtual employees" in assistant_payload["answer"]
    assert assistant_payload["simulation"]["project_outcome"]["delivery_delay_weeks"] > 0
    assert assistant_payload["cited_evidence"]
    assert assistant_payload["recommended_actions"]

    with client.stream("GET", "/api/v1/workforce/virtual-employees/stream", headers=headers) as stream:
        assert stream.status_code == 200
        text = next(stream.iter_text())
        assert "event: virtual_employee_workforce" in text
        assert "NEXUSMIND Synthetic Workforce Twin Generator" in text


def test_enterprise_impact_summary_uses_persisted_audit_snapshots() -> None:
    response = client.get("/api/v1/impact/summary", headers=auth_headers())
    assert response.status_code == 200
    payload = response.json()
    summary = payload["summary"]
    assert payload["model"] == "Persisted Enterprise Impact Snapshot"
    assert summary["net_savings"] >= 0
    assert summary["baseline_annual_loss"] >= summary["net_savings"]
    assert summary["capabilities_total"] >= summary["capabilities_ready"]
    assert summary["realtime_streams"] >= 0
    assert 0 <= summary["recruiter_score"] <= 100
    assert 0 <= summary["judge_wow_score"] <= 100
    assert summary["residual_risk_level"] in {"low", "medium", "high"}
    assert payload["top_business_insight"]
    assert payload["strongest_signal"]
    assert payload["proof_points"]
    assert "roi_intelligence_history.jsonl" in payload["source_histories"]
    assert "complete_platform_history.jsonl" in payload["source_histories"]
    assert "recruiter_impression_history.jsonl" in payload["source_histories"]


def test_organizational_structure_optimizer_graph_simulates_assists_and_streams() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/organization/optimizer/default", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "Graph AI Organizational Structure Optimizer"
    assert payload["summary"]["graph_nodes"] >= 20
    assert payload["summary"]["graph_edges"] >= 20
    assert payload["manager_load"]
    assert payload["reporting_structure"]
    assert payload["communication_flows"]
    assert payload["team_recommendations"]
    assert payload["silo_risks"]
    assert payload["skill_distribution"]
    assert payload["simulations"]
    assert payload["forecasts"]
    assert payload["recommendations"]
    assert "organizational_optimizer_history.jsonl" in payload["storage"]
    assert Path(payload["storage"]).exists()
    assert (Path(payload["storage"]).parent / "organizational_optimizer_graph.json").exists()

    node_types = {node["node_type"] for node in payload["graph_nodes"]}
    assert {"employee", "manager", "team", "department", "project", "skill"}.issubset(node_types)
    edge_types = {edge["edge_type"] for edge in payload["graph_edges"]}
    assert {"reports_to", "communicates_with", "works_on", "has_skill"}.issubset(edge_types)
    assert {
        "organizational_analytics_engine",
        "graph_ai_engine",
        "reporting_structure_analyzer",
        "team_optimization_engine",
        "collaboration_intelligence_engine",
        "communication_flow_analyzer",
        "organizational_simulation_engine",
        "organizational_ai_assistant",
        "company_digital_twin",
        "employee_digital_twin",
        "team_digital_twin",
        "talent_marketplace",
        "knowledge_brain",
        "networkx_graph_algorithms",
    }.issubset(set(payload["source_systems"]))

    custom_employees = [
        {
            "employee_id": "org-test-manager",
            "name": "Overloaded Platform Director",
            "role": "Engineering Director",
            "department": "Engineering",
            "team": "Platform Core",
            "manager_id": None,
            "location": "Bangalore",
            "skills": ["kubernetes", "architecture", "leadership"],
            "projects": ["Platform Reliability"],
            "communicates_with": ["org-test-product", "org-test-sec"],
            "workload": 1.24,
            "stress_score": 82,
            "collaboration_score": 45,
            "leadership_score": 84,
            "productivity_score": 70,
        },
        {
            "employee_id": "org-test-product",
            "name": "Product Liaison",
            "role": "Product Manager",
            "department": "Product",
            "team": "Product Strategy",
            "manager_id": "org-test-manager",
            "skills": ["roadmap", "analytics"],
            "projects": ["Platform Reliability"],
            "communicates_with": ["org-test-manager"],
            "workload": 0.72,
        },
        {
            "employee_id": "org-test-sec",
            "name": "Security Liaison",
            "role": "Security Architect",
            "department": "Security",
            "team": "Security Architecture",
            "manager_id": "org-test-manager",
            "skills": ["security", "kubernetes"],
            "projects": ["Platform Reliability"],
            "communicates_with": ["org-test-manager"],
            "workload": 0.83,
        },
    ]
    for index in range(12):
        custom_employees.append(
            {
                "employee_id": f"org-test-engineer-{index}",
                "name": f"Platform Engineer {index}",
                "role": "Platform Engineer",
                "department": "Engineering",
                "team": "Platform Core",
                "manager_id": "org-test-manager",
                "location": "Bangalore",
                "skills": ["kubernetes", "python", "incident response"],
                "projects": ["Platform Reliability"],
                "communicates_with": ["org-test-manager"],
                "workload": 0.86 + index * 0.02,
                "stress_score": 62 + index,
                "collaboration_score": 58,
                "leadership_score": 48,
                "productivity_score": 74,
            }
        )
    custom = client.post(
        "/api/v1/organization/optimizer/analyze",
        headers=headers,
        json={
            "cycle_name": "Overloaded Platform Org Test",
            "horizon_months": 12,
            "employees": custom_employees,
            "teams": [
                {
                    "team_id": "org-test-team-platform",
                    "name": "Platform Core",
                    "department": "Engineering",
                    "manager_id": "org-test-manager",
                    "location": "Bangalore",
                    "strategic_importance": 0.92,
                    "delivery_pressure": 86,
                }
            ],
        },
    )
    assert custom.status_code == 200
    custom_payload = custom.json()
    top_manager = custom_payload["manager_load"][0]
    assert top_manager["manager_name"] == "Overloaded Platform Director"
    assert top_manager["direct_reports"] >= 12
    assert top_manager["overload_risk"] >= 70
    assert any("split" in item["recommended_structure"].lower() for item in custom_payload["team_recommendations"])
    assert any(item["single_point_of_failure"] for item in custom_payload["skill_distribution"])

    simulation = client.post(
        "/api/v1/organization/optimizer/simulate",
        headers=headers,
        json={
            "scenario_type": "split_team",
            "question": "What happens if Engineering Platform splits into 3 teams?",
            "target_team": "Engineering Platform",
            "new_team_count": 3,
            "horizon_months": 12,
        },
    )
    assert simulation.status_code == 200
    simulation_payload = simulation.json()
    first_simulation = simulation_payload["simulations"][0]
    assert first_simulation["scenario_type"] == "split_team"
    assert first_simulation["productivity_impact"] > 0
    assert first_simulation["communication_impact"] != 0
    assert first_simulation["required_actions"]
    assert first_simulation["digital_twin_evidence"]

    assistant = client.post(
        "/api/v1/organization/optimizer/assistant",
        headers=headers,
        json={"question": "Which managers are overloaded?", "horizon_months": 12},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["intent"] == "manager_overload"
    assert "direct reports" in assistant_payload["answer"]
    assert assistant_payload["cited_evidence"]
    assert assistant_payload["recommended_actions"]

    with client.stream("GET", "/api/v1/organization/optimizer/stream", headers=headers) as stream:
        assert stream.status_code == 200
        text = next(stream.iter_text())
        assert "event: organizational_optimizer" in text
        assert "Graph AI Organizational Structure Optimizer" in text


def test_ai_organizational_brain_builds_gnn_company_graph_assists_and_streams() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/organization/brain/default", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "AI Organizational Brain - GNN Organizational Intelligence Network"
    assert payload["final_verdict"] == "AI ORGANIZATIONAL BRAIN COMPLETE"
    assert payload["production_readiness_score"] >= 92
    assert payload["research_innovation_score"] >= 92
    assert payload["summary"]["graph_nodes"] >= 60
    assert payload["summary"]["graph_edges"] >= 100
    assert payload["graph_database"]["status"] == "ready"
    assert "Embedded JSON Graph Store" in payload["graph_database"]["engine"]
    assert "organizational_brain_graph_store.json" in payload["graph_database"]["storage"]
    assert Path(payload["graph_database"]["storage"]).exists()

    node_types = {node["node_type"] for node in payload["graph_nodes"]}
    assert {"employee", "team", "department", "project", "skill", "client", "knowledge_asset", "location"}.issubset(node_types)
    edge_types = {edge["edge_type"] for edge in payload["graph_edges"]}
    assert {
        "reports_to",
        "works_with",
        "communicates_with",
        "collaborates_with",
        "depends_on",
        "mentors",
        "shares_knowledge_with",
    }.issubset(edge_types)

    gnn = payload["gnn_engine"]
    assert set(gnn["supported_models"]) == {"GraphSAGE", "GAT", "GCN", "GIN"}
    assert gnn["status"] == "ready"
    assert gnn["node_embedding_dimensions"] == 8
    assert gnn["validation_mae"] < 0.08
    assert gnn["embeddings"]
    assert len(gnn["embeddings"][0]["embedding"]) == 8
    assert gnn["relationship_predictions"]

    assert payload["communication_flow"]
    assert payload["knowledge_flow"]
    assert payload["team_dependencies"]
    assert payload["bottlenecks"]
    assert payload["influence_network"]
    assert payload["silo_detection"]
    assert payload["risk_predictions"]
    assert payload["recommendations"]
    assert payload["graph_visualization"]["supports_zoom"] is True
    assert payload["graph_visualization"]["supports_search"] is True
    assert payload["graph_visualization"]["supports_filters"] is True
    assert payload["integration_status"]["employee_twin"] == "ready"
    assert payload["integration_status"]["time_machine"] == "ready"
    assert payload["integration_status"]["executive_dashboard"] == "ready"
    assert {
        "embedded_graph_database_layer",
        "organizational_graph_engine",
        "graph_neural_network_engine",
        "knowledge_flow_engine",
        "communication_analytics_engine",
        "team_dependency_engine",
        "graph_visualization_layer",
        "organizational_ai_assistant",
    }.issubset(set(payload["source_systems"]))

    assistant = client.post(
        "/api/v1/organization/brain/assistant",
        headers=headers,
        json={"question": "Who is the most influential employee?", "horizon_months": 12},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["intent"] == "influence"
    assert "most influential" in assistant_payload["answer"]
    assert assistant_payload["cited_nodes"]
    assert assistant_payload["gnn_evidence"]
    assert assistant_payload["recommended_actions"]

    readiness = client.get("/api/v1/system/readiness")
    assert readiness.status_code == 200
    readiness_payload = readiness.json()
    assert readiness_payload["services"]["ai_organizational_brain"] is True
    assert readiness_payload["services"]["gnn_based_organizational_intelligence"] is True

    with client.stream("GET", "/api/v1/organization/brain/stream", headers=headers) as stream:
        assert stream.status_code == 200
        text = next(stream.iter_text())
        assert "event: organizational_brain" in text
        assert "AI ORGANIZATIONAL BRAIN COMPLETE" in text


def test_realtime_crisis_management_ai_runs_command_center_assistant_simulation_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/crisis/management/default", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "Realtime Crisis Management AI - Emergency Command Center"
    assert payload["summary"]["active_crises"] >= 3
    assert payload["summary"]["highest_severity_score"] >= 50
    assert payload["active_crises"]
    assert payload["containment_actions"]
    assert payload["recovery_plans"]
    assert payload["business_continuity"]
    assert payload["simulations"]
    assert payload["executive_alerts"]
    assert payload["heatmap"]
    assert payload["recommendations"]
    assert payload["agent_council"]
    assert payload["final_verdict"] == "AI CRISIS SIMULATOR COMPLETE"
    assert payload["production_readiness_score"] >= 95
    assert payload["innovation_score"] >= 90
    required_crisis_scenarios = {
        "cyber_attack",
        "ransomware",
        "data_breach",
        "mass_resignation",
        "server_failure",
        "cloud_outage",
        "database_corruption",
        "project_collapse",
        "product_launch_failure",
        "revenue_crash",
        "major_client_loss",
        "supply_chain_disruption",
        "regulatory_incident",
        "public_relations_crisis",
        "financial_crash",
    }
    assert required_crisis_scenarios.issubset(set(payload["supported_scenarios"]))
    assert required_crisis_scenarios.issubset({item["scenario_type"] for item in payload["simulations"]})
    for simulation_item in payload["simulations"]:
        assert simulation_item["systems_affected"]
        assert simulation_item["forecast_timeline"]
        assert simulation_item["recovery_strategy"]
        assert simulation_item["executive_recommendations"]
        assert simulation_item["agent_contributions"]
        assert simulation_item["long_term_impact"] >= 0
        impact_panel = simulation_item["executive_impact_analysis"]
        assert impact_panel["final_verdict"] == "EXECUTIVE IMPACT ANALYSIS COMPLETE"
        assert impact_panel["trigger_type"] == "crisis_simulation"
        assert impact_panel["financial_loss"] >= simulation_item["financial_impact"]
        assert impact_panel["delay_probability"] > 0
        assert impact_panel["most_affected_teams"]
        assert impact_panel["recovery_strategy"]["immediate_actions"]
        assert impact_panel["recovery_strategy"]["short_term_recovery"]
        assert impact_panel["hiring_requirements"]["required_hires"] >= 0
        assert impact_panel["hiring_requirements"]["skills_needed"]
        assert impact_panel["agent_council"]
        assert impact_panel["forecast_points"]
        assert {
            "crisis_simulation_engine",
            "financial_loss_calculator",
            "delay_prediction_engine",
            "team_impact_engine",
            "recovery_strategy_engine",
            "hiring_requirements_engine",
            "company_digital_twin",
            "multi_agent_crisis_council",
        }.issubset(set(impact_panel["source_systems"]))
    assert "crisis_management_history.jsonl" in payload["storage"]
    assert Path(payload["storage"]).exists()
    assert {
        "crisis_detection_engine",
        "ai_crisis_simulator",
        "crisis_scenario_builder",
        "incident_classification_engine",
        "impact_analysis_engine",
        "executive_impact_analysis_panel",
        "financial_loss_calculator",
        "delay_prediction_engine",
        "team_impact_engine",
        "hiring_requirements_engine",
        "crisis_severity_engine",
        "recovery_planning_engine",
        "recovery_strategy_engine",
        "risk_containment_engine",
        "business_continuity_engine",
        "crisis_simulation_engine",
        "crisis_forecast_engine",
        "executive_alert_engine",
        "crisis_ai_assistant",
        "multi_agent_crisis_council",
        "company_digital_twin",
        "team_digital_twin",
        "department_digital_twin",
        "cybersecurity_brain",
        "client_intelligence",
        "boardroom_dashboard",
    }.issubset(set(payload["source_systems"]))
    assert any(
        item["severity_band"] in {"level_4_critical", "level_5_company_threatening"}
        for item in payload["active_crises"]
    )
    assert all(item["recovery_plan"]["recovery_sequence"] for item in payload["active_crises"])

    custom = client.post(
        "/api/v1/crisis/management/analyze",
        headers=headers,
        json={
            "cycle_name": "Security and Infrastructure Crisis Test",
            "horizon_hours": 72,
            "incidents": [
                {
                    "incident_id": "test-ransomware",
                    "incident_type": "ransomware",
                    "title": "Ransomware encryption spike in production",
                    "description": "Mass file modification, backup access attempts, and privileged-token abuse detected.",
                    "affected_systems": ["Production API", "Database Cluster", "Object Storage"],
                    "affected_departments": ["Security", "Engineering"],
                    "affected_clients": ["Strategic Accounts"],
                    "affected_projects": ["Revenue Platform"],
                    "financial_exposure": 9_200_000,
                    "revenue_at_risk": 5_400_000,
                    "workforce_impact": 54,
                    "client_impact": 74,
                    "security_impact": 98,
                    "reputation_impact": 90,
                    "operational_impact": 95,
                    "detection_confidence": 0.93,
                    "recovery_complexity": 92,
                    "time_to_detect_minutes": 22,
                    "active_users_affected": 11000,
                    "employee_count_affected": 58,
                    "controls_triggered": ["ransomware_behavior_detection", "edr_isolation", "backup_recovery_engine"],
                },
                {
                    "incident_id": "test-service-degradation",
                    "incident_type": "server_failure",
                    "title": "Analytics worker degradation",
                    "affected_systems": ["Analytics Workers"],
                    "affected_departments": ["Data"],
                    "financial_exposure": 350_000,
                    "revenue_at_risk": 120_000,
                    "workforce_impact": 14,
                    "client_impact": 18,
                    "security_impact": 6,
                    "reputation_impact": 16,
                    "operational_impact": 34,
                    "detection_confidence": 0.83,
                    "recovery_complexity": 28,
                    "time_to_detect_minutes": 10,
                    "controls_triggered": ["service_health_monitor"],
                },
            ],
        },
    )
    assert custom.status_code == 200
    custom_payload = custom.json()
    top = custom_payload["active_crises"][0]
    assert top["incident_id"] == "test-ransomware"
    assert top["severity_band"] in {"level_4_critical", "level_5_company_threatening"}
    assert top["risk_level"] in {"critical", "company_threatening"}
    assert any("Isolate infected servers" in item["action"] for item in top["containment_actions"])
    assert top["recovery_plan"]["estimated_recovery_hours"] > 10

    simulation = client.post(
        "/api/v1/crisis/management/simulate",
        headers=headers,
        json={
            "scenario_type": "ransomware",
            "question": "What if ransomware affects production?",
            "affected_scope": "production",
            "severity_multiplier": 1.2,
            "horizon_hours": 72,
        },
    )
    assert simulation.status_code == 200
    simulation_payload = simulation.json()
    first_simulation = simulation_payload["simulations"][0]
    assert first_simulation["scenario_type"] == "ransomware"
    assert first_simulation["financial_impact"] > 0
    assert first_simulation["operational_impact"] >= 70
    assert first_simulation["required_resources"]
    assert first_simulation["recommended_response"]
    assert first_simulation["forecast_timeline"]
    assert first_simulation["recovery_strategy"]
    assert first_simulation["executive_recommendations"]
    assert first_simulation["agent_contributions"]
    assert first_simulation["digital_twin_evidence"]
    first_impact = first_simulation["executive_impact_analysis"]
    assert first_impact["final_verdict"] == "EXECUTIVE IMPACT ANALYSIS COMPLETE"
    assert first_impact["trigger_type"] == "crisis_simulation"
    assert first_impact["financial_loss"] >= first_simulation["financial_impact"]
    assert first_impact["delay_probability"] >= first_simulation["operational_impact"] * 0.6
    assert first_impact["most_affected_teams"][0]["impact_score"] > 0
    assert first_impact["recovery_strategy"]["executive_recommendations"]
    assert first_impact["hiring_requirements"]["required_hires"] >= 2
    assert first_impact["hiring_requirements"]["urgency_days"] <= 45
    assert {"Incident Response", "Backup Recovery"}.issubset(set(first_impact["hiring_requirements"]["skills_needed"]))
    assert {"employee_twin=workforce exposure recalculated", "company_twin=revenue, reputation, and operational pressure updated"}.issubset(
        set(first_impact["twin_updates"])
    )
    assert {"Security Agent", "HR Agent", "Finance Agent", "Project Agent", "Executive Agent"}.issubset(
        {agent["agent"] for agent in first_impact["agent_council"]}
    )

    scenario_builder = client.post(
        "/api/v1/crisis/management/scenarios",
        headers=headers,
        json={
            "scenario_name": "Largest client loss board simulation",
            "scenario_type": "major_client_loss",
            "question": "What happens if our biggest client leaves?",
            "affected_scope": "enterprise revenue",
            "severity_multiplier": 1.1,
            "horizon_hours": 168,
            "execute": True,
        },
    )
    assert scenario_builder.status_code == 200
    scenario_payload = scenario_builder.json()
    assert scenario_payload["scenario"]["execution_status"] == "executed"
    assert scenario_payload["scenario"]["scenario_type"] == "major_client_loss"
    assert scenario_payload["simulation"]["scenario_type"] == "major_client_loss"
    assert scenario_payload["simulation"]["financial_impact"] > 0
    scenario_impact = scenario_payload["simulation"]["executive_impact_analysis"]
    assert scenario_impact["final_verdict"] == "EXECUTIVE IMPACT ANALYSIS COMPLETE"
    assert scenario_impact["financial_loss"] >= scenario_payload["simulation"]["financial_impact"]
    assert scenario_impact["most_affected_teams"]
    assert scenario_impact["recovery_strategy"]["risk_reduction_actions"]
    assert scenario_payload["command_center"]["final_verdict"] == "AI CRISIS SIMULATOR COMPLETE"
    assert "crisis_scenario_builder_history.jsonl" in scenario_payload["storage"]
    assert Path(scenario_payload["storage"]).exists()

    assistant = client.post(
        "/api/v1/crisis/management/assistant",
        headers=headers,
        json={"question": "What is our biggest crisis?", "horizon_hours": 72},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["intent"] == "biggest_crisis"
    assert "biggest active crisis" in assistant_payload["answer"].lower()
    assert assistant_payload["cited_incidents"]
    assert assistant_payload["recommended_actions"]

    forecast_assistant = client.post(
        "/api/v1/crisis/management/assistant",
        headers=headers,
        json={"question": "What happens if our biggest client leaves?", "horizon_hours": 168},
    )
    assert forecast_assistant.status_code == 200
    forecast_payload = forecast_assistant.json()
    assert forecast_payload["intent"] == "simulation"
    assert forecast_payload["simulation"]["scenario_type"] == "major_client_loss"
    assert forecast_payload["simulation"]["forecast_timeline"]

    with client.stream("GET", "/api/v1/crisis/management/stream", headers=headers) as stream:
        assert stream.status_code == 200
        text = next(stream.iter_text())
        assert "event: crisis_command_center" in text
        assert "Realtime Crisis Management AI - Emergency Command Center" in text


def test_attrition_prediction_system_is_real_dynamic_and_streamed() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/attrition/default", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "RandomForest/XGBoost Attrition Forecasting Engine"
    assert payload["predictions"]
    assert payload["team_trends"]
    assert payload["heatmap"]
    assert payload["recommendations"]
    assert payload["summary"]["employees_analyzed"] >= 4
    top = payload["predictions"][0]
    assert 0 <= top["resignation_probability"] <= 100
    assert top["feature_attributions"]
    assert top["recommended_interventions"]
    assert {"random_forest", "xgboost", "logistic_regression", "ensemble"}.issubset(top["model_probabilities"])
    assert any(item["direction"] == "increases_attrition" for item in top["feature_attributions"])
    assert "attrition_predictions.jsonl" in payload["storage"]

    response = client.post(
        "/api/v1/attrition/analyze",
        headers=headers,
        json={
            "horizon_days": 90,
            "sensitivity": 0.78,
            "realtime": True,
            "employees": [
                {
                    "employee_id": "emp-critical-attrition",
                    "employee_name": "Critical Engineer",
                    "department": "Engineering",
                    "team_name": "Core Platform",
                    "role": "Principal API Architect",
                    "burnout_score": 94,
                    "productivity_score": 38,
                    "productivity_trend": -0.64,
                    "overtime_hours_30d": 108,
                    "meeting_hours_weekly": 24,
                    "salary_satisfaction": 0.28,
                    "sentiment_score": -0.78,
                    "manager_compatibility": 0.34,
                    "team_stress": 0.93,
                    "promotion_delay_months": 36,
                    "work_life_balance": 0.21,
                    "attendance_rate": 0.75,
                    "absences_90d": 12,
                    "tenure_months": 27,
                    "knowledge_criticality": 0.98,
                    "annual_salary": 196000,
                    "billable_revenue_per_day": 4200,
                },
                {
                    "employee_id": "emp-stable-attrition",
                    "employee_name": "Stable Engineer",
                    "department": "Operations",
                    "team_name": "Automation Team",
                    "role": "Automation Engineer",
                    "burnout_score": 16,
                    "productivity_score": 96,
                    "productivity_trend": 0.28,
                    "overtime_hours_30d": 3,
                    "meeting_hours_weekly": 4,
                    "salary_satisfaction": 0.92,
                    "sentiment_score": 0.72,
                    "manager_compatibility": 0.93,
                    "team_stress": 0.14,
                    "promotion_delay_months": 2,
                    "work_life_balance": 0.9,
                    "attendance_rate": 1,
                    "absences_90d": 0,
                    "tenure_months": 40,
                    "knowledge_criticality": 0.4,
                    "annual_salary": 128000,
                    "billable_revenue_per_day": 1700,
                },
            ],
        },
    )
    assert response.status_code == 200
    custom = response.json()
    by_id = {item["employee_id"]: item for item in custom["predictions"]}
    critical = by_id["emp-critical-attrition"]
    stable = by_id["emp-stable-attrition"]
    assert critical["resignation_probability"] > stable["resignation_probability"]
    assert critical["resignation_probability"] >= 70
    assert stable["resignation_probability"] <= 45
    assert critical["risk_level"] in {"high", "critical"}
    assert critical["replacement_cost_exposure"] > stable["replacement_cost_exposure"]
    assert custom["summary"]["high_risk_employees"] >= 1
    assert custom["recommendations"]

    with client.stream("GET", "/api/v1/attrition/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: attrition" in first_chunk
        assert "RandomForest/XGBoost Attrition Forecasting Engine" in first_chunk


def test_smart_hiring_ai_system_is_real_dynamic_ranked_and_streamed() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/hiring/default", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "TF-IDF Semantic Matcher + RandomForest Smart Hiring Ranker"
    assert payload["rankings"]
    assert payload["recommendations"]
    assert payload["recruiter_trends"]
    assert payload["summary"]["candidates_analyzed"] >= 4
    top = payload["rankings"][0]
    assert top["compatibility_score"] >= payload["rankings"][-1]["compatibility_score"]
    assert {"random_forest_ranker", "semantic_similarity", "skill_coverage", "fraud_anomaly_risk"}.issubset(top["model_scores"])
    assert top["matched_skills"]
    assert "hiring_analytics.jsonl" in payload["storage"]

    response = client.post(
        "/api/v1/hiring/analyze",
        headers=headers,
        json={
            "realtime": True,
            "role": {
                "role_id": "role-ai-platform",
                "title": "Backend AI Platform Engineer",
                "job_description": "Build secure Python FastAPI services, Kubernetes automation, PostgreSQL and Redis reliability, MLOps model serving, API observability, and incident response.",
                "required_skills": ["python", "kubernetes", "api reliability", "security", "postgresql"],
                "preferred_skills": ["redis", "mlops", "incident response", "microservices", "testing"],
                "seniority": "senior",
                "team_context": "Enterprise AI platform team operating realtime analytics and model-serving APIs.",
                "culture_values": ["ownership", "clear communication", "collaboration", "incident discipline"],
                "domain_keywords": ["enterprise ai", "platform reliability", "secure api", "model serving"],
            },
            "candidates": [
                {
                    "candidate_id": "cand-elite",
                    "candidate_name": "Elite Candidate",
                    "current_title": "Senior Platform Engineer",
                    "years_experience": 9,
                    "expected_salary": 188000,
                    "declared_skills": ["Python", "FastAPI", "Kubernetes", "PostgreSQL", "Redis", "Security", "MLOps"],
                    "certifications": ["CKA", "AWS Solutions Architect"],
                    "resume_text": "Led Python FastAPI services for model serving, migrated workloads to Kubernetes, optimized PostgreSQL, added Redis caching, owned JWT security reviews, built observability, and reduced API latency by 41%. Mentored engineers and ran incident postmortems.",
                    "interview_transcript": "I clarify customer impact, communicate tradeoffs, document recovery steps, and pair with teammates during incidents. I care about ownership and clear handoffs.",
                    "portfolio_summary": "Built a secure MLOps gateway with canary deployments, tracing, rate limits, and model monitoring.",
                },
                {
                    "candidate_id": "cand-gap",
                    "candidate_name": "Gap Candidate",
                    "current_title": "Backend Engineer",
                    "years_experience": 5,
                    "expected_salary": 136000,
                    "declared_skills": ["Python", "Django", "Docker", "SQL", "Testing"],
                    "certifications": [],
                    "resume_text": "Built Python APIs, Django services, Docker workflows, SQL reports, and automated tests. Supported production incidents and helped split a monolith into microservices.",
                    "interview_transcript": "I learn infrastructure quickly and communicate blockers early.",
                    "portfolio_summary": "Payment reconciliation API and CI test harness.",
                },
                {
                    "candidate_id": "cand-risk",
                    "candidate_name": "Risk Candidate",
                    "current_title": "Principal Everything Architect",
                    "years_experience": 3,
                    "expected_salary": 280000,
                    "declared_skills": ["Python", "Kubernetes", "Security", "MLOps", "AWS", "Leadership"],
                    "certifications": ["Self certified cloud expert"],
                    "resume_text": "Personally owned every architecture decision for dozens of unicorn-scale platforms and mastered all cloud, security, AI, Kubernetes, databases, frontend, backend, and leadership functions without team dependency. 20 years Kubernetes experience.",
                    "interview_transcript": "I prefer to work alone and do not need reviews or postmortems because I already know the answer.",
                    "portfolio_summary": "No public projects available.",
                },
            ],
        },
    )
    assert response.status_code == 200
    custom = response.json()
    by_id = {item["candidate_id"]: item for item in custom["rankings"]}
    elite = by_id["cand-elite"]
    gap = by_id["cand-gap"]
    risk = by_id["cand-risk"]
    assert elite["compatibility_score"] > gap["compatibility_score"]
    assert elite["compatibility_score"] > risk["compatibility_score"]
    assert elite["hiring_recommendation"] in {"strong_hire", "hire"}
    assert gap["missing_skills"]
    assert risk["fraud_signals"]
    assert risk["hiring_risk_score"] > elite["hiring_risk_score"]
    assert custom["summary"]["fraud_risk_count"] >= 1
    assert custom["skill_gap_heatmap"]

    with client.stream("GET", "/api/v1/hiring/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: hiring" in first_chunk
        assert "TF-IDF Semantic Matcher" in first_chunk


def test_ai_smart_interviewer_conducts_scores_reports_ranks_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/interviews/smart/default", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "NEXUSMIND AI Smart Interviewer Panel"
    assert payload["summary"]["active_interviews"] >= 4
    assert payload["summary"]["report_count"] >= payload["summary"]["active_interviews"]
    assert len(payload["generated_questions"]) >= 7
    question_types = {item["interview_type"] for item in payload["generated_questions"]}
    assert {"technical", "behavioral", "system_design", "coding", "cloud", "database", "cybersecurity"}.issubset(question_types)
    top = payload["candidate_rankings"][0]
    assert top["overall_score"] >= payload["candidate_rankings"][-1]["overall_score"]
    assert top["technical_score"] > 50
    assert top["behavioral_score"] > 50
    assert top["voice_analysis"]["confidence_score"] > 50
    assert {"Programming", "Problem Solving", "System Design", "Communication", "Technical Depth"}.issubset(
        {item["skill"] for item in top["skill_scores"]}
    )
    assert Path(top["report"]["pdf_path"]).exists()
    assert Path(top["report"]["docx_path"]).exists()
    assert "smart_interviewer_history.jsonl" in payload["storage"]
    assert {
        "interview_engine",
        "question_generation_engine",
        "resume_analysis_engine",
        "candidate_scoring_engine",
        "voice_confidence_engine",
        "cheating_detection_engine",
        "interview_report_generator",
        "smart_hiring_ranker_adapter",
    }.issubset(set(payload["source_systems"]))

    response = client.post(
        "/api/v1/interviews/smart/run",
        headers=headers,
        json={
            "realtime": True,
            "interview_types": ["technical", "behavioral", "system_design", "coding", "cloud", "database", "cybersecurity"],
            "role": {
                "role_id": "role-smart-interviewer",
                "title": "Senior AI Platform Engineer",
                "job_description": "Build secure Python FastAPI services, Kubernetes automation, PostgreSQL and Redis reliability, MLOps model serving, API observability, and incident response.",
                "required_skills": ["python", "kubernetes", "api reliability", "security", "postgresql"],
                "preferred_skills": ["redis", "mlops", "incident response", "microservices", "testing"],
                "seniority": "senior",
                "team_context": "Enterprise AI platform team operating realtime analytics and model-serving APIs.",
                "culture_values": ["ownership", "clear communication", "collaboration", "incident discipline"],
                "domain_keywords": ["enterprise ai", "platform reliability", "secure api", "model serving"],
            },
            "candidates": [
                {
                    "candidate_id": "cand-interview-elite",
                    "candidate_name": "Elite Interview Candidate",
                    "current_title": "Senior Platform Engineer",
                    "years_experience": 9,
                    "expected_salary": 188000,
                    "declared_skills": ["Python", "FastAPI", "Kubernetes", "PostgreSQL", "Redis", "Security", "MLOps"],
                    "certifications": ["CKA", "AWS Solutions Architect"],
                    "resume_text": "Led Python FastAPI services for model serving, migrated workloads to Kubernetes, optimized PostgreSQL, added Redis caching, owned JWT security reviews, built observability, and reduced API latency by 41%. Mentored engineers and ran incident postmortems.",
                    "interview_transcript": "I clarify customer impact, communicate tradeoffs, document recovery steps, and pair with teammates during incidents. I care about ownership and clear handoffs.",
                    "portfolio_summary": "Built a secure MLOps gateway with canary deployments, tracing, rate limits, and model monitoring.",
                    "answers": [
                        {
                            "question_id": "q-system",
                            "question": "Design a reliable API gateway.",
                            "interview_type": "system_design",
                            "difficulty": "senior",
                            "answer": "I would clarify traffic patterns, use load balancing, rate limits, JWT validation, least privilege, Redis caching, Postgres replicas, tracing, SLO metrics, circuit breakers, canary deployment, rollback, test gates, and incident runbooks.",
                            "response_time_seconds": 250,
                        },
                        {
                            "question_id": "q-behavior",
                            "question": "Describe incident ownership.",
                            "interview_type": "behavioral",
                            "difficulty": "senior",
                            "answer": "I led coordination, communicated customer impact, paired with teammates, protected psychological safety, and assigned follow-up owners after a blameless postmortem.",
                            "response_time_seconds": 140,
                        },
                    ],
                    "voice_metrics": {
                        "words_per_minute": 136,
                        "hesitation_count": 2,
                        "pitch_variance": 0.22,
                        "pause_ratio": 0.1,
                        "volume_stability": 0.84,
                    },
                    "monitoring_events": [],
                },
                {
                    "candidate_id": "cand-interview-risk",
                    "candidate_name": "Risk Interview Candidate",
                    "current_title": "Principal Everything Architect",
                    "years_experience": 3,
                    "expected_salary": 285000,
                    "declared_skills": ["Python", "Kubernetes", "Security", "MLOps", "AWS", "Leadership"],
                    "certifications": ["Self certified cloud expert"],
                    "resume_text": "Personally owned every architecture decision for dozens of unicorn-scale platforms and mastered all cloud, security, AI, Kubernetes, databases, frontend, backend, and leadership functions without team dependency. 20 years Kubernetes experience.",
                    "interview_transcript": "I prefer to work alone and do not need reviews or postmortems because I already know the answer.",
                    "portfolio_summary": "No public projects available.",
                    "answers": [
                        {
                            "question_id": "q-system",
                            "question": "Design a reliable API gateway.",
                            "interview_type": "system_design",
                            "difficulty": "senior",
                            "answer": "I have mastered all cloud and architecture. Use everything perfectly. Reviews are unnecessary.",
                            "response_time_seconds": 10,
                        }
                    ],
                    "voice_metrics": {
                        "words_per_minute": 248,
                        "hesitation_count": 0,
                        "pitch_variance": 0.68,
                        "pause_ratio": 0.02,
                        "volume_stability": 0.41,
                    },
                    "monitoring_events": [
                        {"event_type": "copy_paste", "timestamp_offset_seconds": 15, "severity_weight": 0.85, "details": "Large pasted answer appeared instantly."},
                        {"event_type": "suspicious_speed", "timestamp_offset_seconds": 20, "severity_weight": 0.8, "details": "Answer speed exceeded realistic response threshold."},
                        {"event_type": "external_assistance", "timestamp_offset_seconds": 39, "severity_weight": 0.74, "details": "Focus left interview tab during security answer."},
                    ],
                },
            ],
        },
    )
    assert response.status_code == 200
    custom = response.json()
    by_id = {item["candidate_id"]: item for item in custom["candidate_rankings"]}
    elite = by_id["cand-interview-elite"]
    risk = by_id["cand-interview-risk"]
    assert elite["overall_score"] > risk["overall_score"]
    assert elite["recommendation"]["decision"] in {"strong_hire", "hire"}
    assert risk["cheating_risk_score"] > elite["cheating_risk_score"]
    assert risk["cheating_report"]["copy_paste_events"] >= 1
    assert risk["cheating_report"]["external_assistance_signals"] >= 1
    assert risk["recommendation"]["decision"] in {"consider", "reject"}
    assert Path(elite["report"]["pdf_path"]).exists()
    assert Path(elite["report"]["docx_path"]).exists()

    assistant = client.post(
        "/api/v1/interviews/smart/assistant",
        headers=headers,
        json={"question": "Show top candidate."},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["intent"] == "top_candidate"
    assert assistant_payload["candidate_ids"]
    assert assistant_payload["cited_evidence"]

    report = client.post(
        "/api/v1/interviews/smart/assistant",
        headers=headers,
        json={"question": "Generate interview report."},
    )
    assert report.status_code == 200
    report_payload = report.json()
    assert report_payload["intent"] == "report"
    assert report_payload["report_artifacts"]

    with client.stream("GET", "/api/v1/interviews/smart/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: smart_interviewer" in first_chunk
        assert "NEXUSMIND AI Smart Interviewer Panel" in first_chunk


def test_strategic_intelligence_system_is_dynamic_cross_functional_and_streamed() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/strategic/enterprise", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "Strategic Enterprise Intelligence Graph"
    assert payload["competitive_intelligence"]
    assert payload["client_relationship_intelligence"]
    assert payload["internal_marketplace_matches"]
    assert payload["mentor_matches"]
    assert payload["organization_optimizations"]
    assert payload["innovation_signals"]
    assert payload["crisis_response"]["recovery_priorities"]
    assert payload["summary"]["marketplace_matches"] >= 1
    assert payload["summary"]["strategic_readiness_score"] > 0
    assert "strategic_intelligence_history.jsonl" in payload["storage"]

    response = client.post(
        "/api/v1/strategic/enterprise",
        headers=headers,
        json={
            "crisis_scenario": "competitor surge and critical client renewal collapse",
            "competitors": [
                {
                    "name": "Aggressive AI Rival",
                    "hiring_velocity": 72,
                    "product_launches_90d": 5,
                    "ai_mentions_30d": 180,
                    "funding_signal": 0.95,
                    "security_incidents": 0,
                    "technology_adoption_score": 94,
                    "market_sentiment": 0.72,
                },
                {
                    "name": "Slow Legacy Vendor",
                    "hiring_velocity": 4,
                    "product_launches_90d": 0,
                    "ai_mentions_30d": 8,
                    "funding_signal": 0.05,
                    "security_incidents": 5,
                    "technology_adoption_score": 32,
                    "market_sentiment": -0.2,
                },
            ],
            "clients": [
                {
                    "client_id": "client-critical",
                    "name": "Critical Renewal",
                    "contract_value": 5000000,
                    "delivery_slippage_days": 34,
                    "sentiment_score": -0.72,
                    "payment_delay_days": 24,
                    "escalation_count": 8,
                    "usage_trend_percent": -35,
                    "executive_engagement_score": 22,
                },
                {
                    "client_id": "client-stable",
                    "name": "Stable Account",
                    "contract_value": 900000,
                    "delivery_slippage_days": 1,
                    "sentiment_score": 0.58,
                    "payment_delay_days": 0,
                    "escalation_count": 0,
                    "usage_trend_percent": 18,
                    "executive_engagement_score": 91,
                },
            ],
            "talent": [
                {
                    "employee_id": "emp-platform",
                    "name": "Platform Expert",
                    "role": "Principal Platform Engineer",
                    "department": "Engineering",
                    "skills": ["python", "kubernetes", "mlops", "incident response"],
                    "mentor_topics": ["kubernetes", "incident response"],
                    "capacity_hours": 40,
                    "allocated_hours": 26,
                    "stress_score": 28,
                    "leadership_score": 86,
                    "innovation_signals": 8,
                },
                {
                    "employee_id": "emp-learner",
                    "name": "Rising Engineer",
                    "role": "Backend Engineer",
                    "department": "Engineering",
                    "skills": ["python", "api reliability"],
                    "mentor_topics": [],
                    "capacity_hours": 40,
                    "allocated_hours": 32,
                    "stress_score": 42,
                    "leadership_score": 55,
                    "innovation_signals": 2,
                },
            ],
            "projects": [
                {
                    "project_id": "project-defense",
                    "title": "AI Market Defense",
                    "department": "Strategy",
                    "required_skills": ["python", "kubernetes", "mlops"],
                    "priority": 5,
                    "revenue_impact": 6000000,
                    "deadline_pressure": 84,
                }
            ],
            "org_units": [
                {
                    "unit": "Platform",
                    "headcount": 38,
                    "manager_count": 2,
                    "dependency_load": 92,
                    "stress_score": 81,
                    "collaboration_score": 49,
                    "decision_latency_days": 12,
                    "critical_skills_gap": 7,
                }
            ],
        },
    )
    assert response.status_code == 200
    custom = response.json()
    assert custom["competitive_intelligence"][0]["competitor"] == "Aggressive AI Rival"
    assert custom["competitive_intelligence"][0]["market_pressure_score"] > custom["competitive_intelligence"][1]["market_pressure_score"]
    assert custom["client_relationship_intelligence"][0]["client_name"] == "Critical Renewal"
    assert custom["client_relationship_intelligence"][0]["churn_risk"] > custom["client_relationship_intelligence"][1]["churn_risk"]
    assert custom["internal_marketplace_matches"][0]["employee_name"] == "Platform Expert"
    assert custom["mentor_matches"]
    assert custom["organization_optimizations"][0]["optimization_pressure"] >= 60
    assert custom["crisis_response"]["severity_score"] >= payload["crisis_response"]["severity_score"]

    with client.stream("GET", "/api/v1/strategic/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: strategic" in first_chunk
        assert "Strategic Enterprise Intelligence Graph" in first_chunk


def test_internal_talent_marketplace_matches_projects_mentors_jobs_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/talent/marketplace/default", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "Internal Talent Marketplace Graph + TF-IDF Recommendation Engine"
    assert payload["profiles"]
    assert payload["skill_intelligence"]
    assert payload["project_matches"]
    assert payload["mentor_matches"]
    assert payload["internal_role_matches"]
    assert payload["learning_paths"]
    assert payload["expert_rankings"]
    assert payload["reputation_scores"]
    assert payload["badges"]
    assert payload["graph_nodes"]
    assert payload["graph_edges"]
    assert payload["recommendations"]
    assert payload["summary"]["project_matches"] >= 1
    assert payload["summary"]["mentor_matches"] >= 1
    assert payload["summary"]["badges_awarded"] >= 1
    assert {
        "talent_profile_engine",
        "skill_intelligence_engine",
        "project_matching_engine",
        "mentor_matching_engine",
        "internal_job_matching_engine",
        "learning_recommendation_engine",
        "reputation_engine",
        "talent_ai_assistant",
    }.issubset(set(payload["source_systems"]))

    search = client.post(
        "/api/v1/talent/marketplace/search",
        headers=headers,
        json={"query": "kubernetes mlops project", "limit": 6},
    )
    assert search.status_code == 200
    search_payload = search.json()
    assert search_payload["results"]
    assert any(result["entity_type"] in {"employee", "project"} for result in search_payload["results"])

    assistant = client.post(
        "/api/v1/talent/marketplace/assistant",
        headers=headers,
        json={"question": "Who can mentor me on Kubernetes?"},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["intent"] == "mentors"
    assert assistant_payload["cited_profiles"]
    assert assistant_payload["recommended_actions"]

    custom = client.post(
        "/api/v1/talent/marketplace/analyze",
        headers=headers,
        json={
            "focus_skills": ["python", "rag", "vector search", "mlops", "kubernetes", "system design"],
            "profiles": [
                {
                    "employee_id": "talent-priya",
                    "employee_name": "Priya Raman",
                    "role": "Senior AI Engineer",
                    "department": "AI Platform",
                    "location": "Bangalore",
                    "skills": ["python", "rag", "vector search", "mlops"],
                    "experience_years": 7,
                    "certifications": ["Machine Learning Specialization"],
                    "projects": ["Payment failure RAG assistant", "Vector search evaluation"],
                    "achievements": ["Improved retrieval relevance by 30%", "Mentored engineers on RAG evaluation"],
                    "interests": ["ai platform", "knowledge graph"],
                    "career_goals": ["Principal AI Platform Architect"],
                    "learning_goals": ["kubernetes", "system design"],
                    "expertise_areas": ["rag", "mlops", "python"],
                    "offered_expertise": ["rag", "mlops", "vector search"],
                    "wants_mentorship": True,
                    "wants_projects": True,
                    "wants_internal_roles": True,
                    "capacity_hours": 40,
                    "allocated_hours": 24,
                    "performance_score": 93,
                    "learning_velocity": 0.9,
                    "mentorship_hours": 28,
                    "knowledge_contributions": 21,
                    "reputation_events": 26,
                },
                {
                    "employee_id": "talent-nikhil",
                    "employee_name": "Nikhil Shah",
                    "role": "Backend Engineer",
                    "department": "Engineering",
                    "location": "Pune",
                    "skills": ["python", "fastapi", "postgresql"],
                    "experience_years": 4,
                    "certifications": ["AWS Cloud Practitioner"],
                    "projects": ["Billing API stabilization"],
                    "achievements": ["Reduced billing API latency"],
                    "interests": ["cloud", "platform engineering"],
                    "career_goals": ["Staff Backend Engineer"],
                    "learning_goals": ["mlops", "kubernetes"],
                    "expertise_areas": ["fastapi", "postgresql"],
                    "offered_expertise": ["fastapi"],
                    "wants_mentorship": True,
                    "wants_projects": True,
                    "wants_internal_roles": True,
                    "capacity_hours": 40,
                    "allocated_hours": 31,
                    "performance_score": 84,
                    "learning_velocity": 0.74,
                    "mentorship_hours": 2,
                    "knowledge_contributions": 8,
                    "reputation_events": 11,
                },
            ],
            "projects": [
                {
                    "project_id": "talent-project-rag",
                    "title": "Enterprise RAG Quality Upgrade",
                    "department": "AI Platform",
                    "description": "Improve retrieval quality for company brain workflows.",
                    "required_skills": ["python", "rag", "vector search", "mlops"],
                    "stretch_skills": ["kubernetes", "knowledge graph"],
                    "priority": 5,
                    "duration_weeks": 8,
                    "open_slots": 2,
                    "reputation_boost": 18,
                    "business_impact": 91,
                }
            ],
            "internal_roles": [
                {
                    "role_id": "talent-role-platform",
                    "title": "Principal AI Platform Architect",
                    "department": "AI Platform",
                    "level": "Principal",
                    "required_skills": ["python", "rag", "mlops", "system design"],
                    "preferred_skills": ["kubernetes", "vector search"],
                    "career_track": "technical_leadership",
                    "growth_score": 94,
                    "vacancy_urgency": 72,
                }
            ],
        },
    )
    assert custom.status_code == 200
    custom_payload = custom.json()
    assert custom_payload["project_matches"][0]["employee_name"] == "Priya Raman"
    assert custom_payload["project_matches"][0]["match_score"] > 75
    assert any(match["mentor_name"] == "Priya Raman" and match["mentee_name"] == "Nikhil Shah" for match in custom_payload["mentor_matches"])
    assert custom_payload["internal_role_matches"][0]["employee_name"] == "Priya Raman"
    assert any(path["employee_name"] == "Nikhil Shah" and path["target_skill"] in {"mlops", "kubernetes"} for path in custom_payload["learning_paths"])
    assert any(badge["employee_name"] == "Priya Raman" for badge in custom_payload["badges"])

    with client.stream("GET", "/api/v1/talent/marketplace/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: talent_marketplace" in first_chunk
        assert "Internal Talent Marketplace Graph" in first_chunk


def test_recruiter_impression_audit_scores_startup_quality_and_streams() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/recruiter-impression/summary", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "Recruiter-Grade Enterprise Product Quality Auditor"
    assert payload["summary"]["overall_score"] >= 88
    assert payload["summary"]["startup_score"] >= 88
    assert payload["summary"]["research_score"] >= 88
    assert payload["summary"]["recruiter_score"] >= 88
    assert "enterprise-grade" in payload["summary"]["verdict"].lower()

    dimensions = {dimension["name"]: dimension for dimension in payload["dimensions"]}
    expected_dimensions = {
        "Real-World Problem Solving",
        "Enterprise Business Intelligence",
        "Advanced AI Engineering",
        "Full-Stack Engineering Quality",
        "Data Science and Analytics Depth",
        "Enterprise Scalability Mindset",
        "Startup-Level Product Clarity",
        "Industry-Level Enterprise Platform",
        "Research-Level Innovation",
        "Recruiter Signal Strength",
        "Judge WOW Factor",
    }
    assert expected_dimensions.issubset(dimensions)
    assert all(dimension["status"] in {"elite", "strong"} for dimension in dimensions.values())
    assert any(metric["label"] == "Business case" and "$" in metric["value"] for metric in payload["metrics"])
    assert len(payload["demo_moments"]) >= 5
    proof = " ".join(payload["technical_proof"])
    assert "Random Forest" in proof
    assert "ROI Intelligence" in proof
    assert "recruiter_impression_history.jsonl" in payload["storage"]

    with client.stream("GET", "/api/v1/recruiter-impression/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: recruiter_impression" in first_chunk
        assert "overall_score" in first_chunk


def test_judge_impact_validation_scores_world_class_enterprise_platform() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/judge-impact/validation", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["model"] == "NEXUSMIND Judge Impact + Enterprise Product Auditor"
    assert payload["final_verdict"] == "WORLD-CLASS ENTERPRISE AI PLATFORM"
    assert payload["missing_components"] == []
    assert payload["scorecard"]["minimum_score"] >= 90
    for key in (
        "innovation_score",
        "enterprise_readiness_score",
        "product_maturity_score",
        "startup_potential_score",
        "technical_complexity_score",
        "judge_wow_factor_score",
        "recruiter_impact_score",
        "production_readiness_score",
    ):
        assert payload["scorecard"][key] >= 90

    expected_evaluators = {
        "College Project Judge",
        "Hackathon Judge",
        "Startup Investor",
        "Enterprise CTO",
        "Enterprise CIO",
        "Product Manager",
        "AI Researcher",
        "Recruiter",
    }
    evaluator_names = {item["evaluator"] for item in payload["evaluator_audits"]}
    assert evaluator_names == expected_evaluators
    for evaluator in payload["evaluator_audits"]:
        assert evaluator["status"] == "elite"
        assert evaluator["impressive"]
        assert evaluator["enterprise_grade"]
        assert evaluator["production_belief"].startswith("Yes.")
        assert evaluator["fake_signals"]

    product_dimensions = {item["name"] for item in payload["product_audit"]}
    assert {
        "Silicon Valley Startup Product",
        "Enterprise SaaS Validation",
        "Research-Level Innovation",
        "Future Company Operating System",
        "Executive Wow Factor",
        "Production Readiness",
    }.issubset(product_dimensions)
    assert len(payload["differentiation_report"]) == 5
    assert {item["status"] for item in payload["integration_status"]} == {"connected"}
    assert any(item["integration"] == "Multi-Agent Workforce -> Executive Decisions" for item in payload["integration_status"])
    assert any("Multi-Agent AI Workforce" in item for item in payload["fixed_components"])
    assert any("Judge Impact Validation" in item for item in payload["regenerated_components"])
    assert {
        "judge_impression_auditor",
        "product_differentiation_engine",
        "production_readiness_auditor",
        "multi_agent_ai_workforce_validator",
    }.issubset(set(payload["source_systems"]))
    assert "judge_impact_validation_history.jsonl" in payload["storage"]
    assert Path(payload["storage"]).exists()

    with client.stream("GET", "/api/v1/judge-impact/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: judge_impact_validation" in first_chunk
        assert "WORLD-CLASS ENTERPRISE AI PLATFORM" in first_chunk


def test_unified_enterprise_system_proves_modules_are_connected() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/unified-enterprise/verification", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["model"] == "NEXUSMIND Unified Autonomous Enterprise Intelligence Auditor"
    assert payload["final_verdict"] == "TRUE AUTONOMOUS AI-DRIVEN ENTERPRISE INTELLIGENCE SYSTEM"
    assert payload["modules_disconnected"] == []
    assert payload["missing_components"] == []
    assert payload["scorecard"]["minimum_score"] >= 90
    for key in (
        "unified_platform_score",
        "enterprise_architecture_score",
        "integration_score",
        "automation_score",
        "ai_intelligence_score",
        "production_readiness_score",
    ):
        assert payload["scorecard"][key] >= 90

    expected_modules = {
        "HR Intelligence",
        "Workforce Intelligence",
        "Talent Marketplace",
        "Knowledge Brain",
        "Project Intelligence",
        "Client Intelligence",
        "Competitive Intelligence",
        "Crisis Management",
        "Cybersecurity Brain",
        "Business Prediction Engine",
        "Simulation Lab",
        "Digital Twin System",
        "Multi-Agent AI Workforce",
        "Executive Boardroom Dashboard",
        "Voice AI Assistant",
    }
    assert set(payload["modules_connected"]) == expected_modules
    module_status = {item["module"]: item for item in payload["module_status"]}
    assert set(module_status) == expected_modules
    for module in module_status.values():
        assert module["status"] == "connected"
        assert module["boardroom_visible"] is True
        assert module["agent_accessible"] is True
        assert module["workflow_connected"] is True
        assert module["shared_data"]

    data_entities = {item["entity"] for item in payload["single_source_of_truth"]}
    assert {"Workforce Twins", "Teams", "Departments", "Projects", "Clients", "Risks", "Knowledge", "Forecasts", "Simulations"}.issubset(data_entities)
    assert {item["status"] for item in payload["single_source_of_truth"]} == {"connected"}
    workflow_names = {item["name"] for item in payload["cross_module_workflows"]}
    assert {
        "Burnout-to-Boardroom Risk Chain",
        "Client Churn Retention Chain",
        "Cyber Threat Crisis Chain",
        "Project Delay Resource Chain",
        "Knowledge Loss Talent Chain",
    }.issubset(workflow_names)
    assert {item["status"] for item in payload["cross_module_workflows"]} == {"connected"}
    assert {item["status"] for item in payload["autonomous_actions"]} == {"connected"}
    assert payload["agent_collaboration"]["status"] == "connected"
    assert len(payload["agent_collaboration"]["agents"]) == 8
    assert payload["agent_collaboration"]["messages"] >= 8
    assert payload["executive_experience"]["status"] == "connected"
    assert "Simulate losing 20 engineers." in payload["executive_experience"]["voice_commands"]
    assert "Emotion Analytics" in payload["digital_twin_sync_sources"]
    assert "Incidents" in payload["knowledge_brain_sources"]
    assert any("Unified audit" in item for item in payload["fixed_components"])
    assert any("Unified Enterprise AI Operating System" in item for item in payload["regenerated_components"])
    assert "unified_enterprise_system_history.jsonl" in payload["storage"]
    assert Path(payload["storage"]).exists()

    with client.stream("GET", "/api/v1/unified-enterprise/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: unified_enterprise_system" in first_chunk
        assert "TRUE AUTONOMOUS AI-DRIVEN ENTERPRISE INTELLIGENCE SYSTEM" in first_chunk


def test_living_company_brain_integrates_memory_reasoning_simulation_agents_learning_and_twins() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/living-company-brain/default", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["model"] == "NEXUSMIND AI Living Company Brain"
    assert payload["company_brain_status"] == "active"
    assert payload["organism_score"] >= 90
    assert payload["final_verdict"] == "LIVING AI COMPANY BRAIN COMPLETE"
    assert payload["missing_components"] == []
    assert payload["errors_found"] == []
    assert payload["awareness"]["employees_mirrored"] > 0
    assert payload["awareness"]["teams_mirrored"] > 0
    assert payload["awareness"]["projects_mirrored"] > 0
    assert payload["memory"]["documents_indexed"] > 0
    assert payload["memory"]["graph_nodes"] > 0
    assert payload["memory"]["sample_answer"]
    assert len(payload["reasoning_chain"]) >= 3
    assert {"burnout", "attrition", "project_delay", "revenue"}.issubset({item["domain"] for item in payload["predictions"]})
    assert payload["simulation"]["scenario"] == "What happens if 30 engineers resign tomorrow?"
    assert payload["simulation"]["risk_propagation_path"]
    assert payload["simulation"]["digital_twin_evidence"]
    assert payload["multi_agent"]["active_agents"] == 8
    assert payload["multi_agent"]["shared_memory_records"] >= 8
    assert payload["multi_agent"]["council_discussion"]
    assert payload["learning"]["learning_maturity_score"] >= 90
    assert payload["learning"]["feedback_loops"] >= 1
    assert payload["digital_twin"]["mirror_sync_completeness"] >= 90
    assert payload["digital_twin"]["twin_updates"]
    assert payload["executive_intelligence"]["answer"]
    assert payload["executive_intelligence"]["recommended_actions"]
    assert {item["status"] for item in payload["component_signals"]} <= {"active", "watch"}
    assert len(payload["integration_graph"]) >= 5
    assert {
        "enterprise_knowledge_brain",
        "company_simulation_lab",
        "multi_agent_workforce",
        "self_learning_ai",
        "shadow_company_engine",
    }.issubset(set(payload["source_systems"]))
    assert "living_company_brain_history.jsonl" in payload["storage"]
    assert Path(payload["storage"]).exists()

    memory = client.post(
        "/api/v1/living-company-brain/ask",
        headers=headers,
        json={"question": "How did we solve this before and who knows Kubernetes?", "horizon_months": 3},
    )
    assert memory.status_code == 200
    memory_payload = memory.json()
    assert memory_payload["mode"] == "enterprise_memory"
    assert memory_payload["answer"]
    assert memory_payload["recommended_actions"]
    assert "enterprise_knowledge_brain" in memory_payload["consulted_engines"]

    future = client.post(
        "/api/v1/living-company-brain/ask",
        headers=headers,
        json={"question": "What happens if 30 engineers resign tomorrow?", "horizon_months": 12},
    )
    assert future.status_code == 200
    future_payload = future.json()
    assert future_payload["mode"] == "future_simulation"
    assert future_payload["confidence"] >= 0.6
    assert future_payload["recommended_actions"]
    assert "company_simulation_lab" in future_payload["consulted_engines"]

    with client.stream("GET", "/api/v1/living-company-brain/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: living_company_brain" in first_chunk
        assert "LIVING AI COMPANY BRAIN COMPLETE" in first_chunk


def test_self_learning_company_ai_tracks_feedback_knowledge_agents_and_twins() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/self-learning/verification", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["model"] == "NEXUSMIND Self-Learning Company AI"
    assert payload["final_verdict"] == "SELF-EVOLVING AI SYSTEM COMPLETE"
    assert payload["learning_engine_status"] == "ready"
    assert payload["adaptive_ai_status"] == "ready"
    assert payload["knowledge_evolution_status"] == "ready"
    assert payload["agent_learning_status"] == "ready"
    assert payload["digital_twin_learning_status"] == "ready"
    assert payload["recommendation_accuracy"] >= 90
    assert payload["forecast_accuracy"] >= 90
    assert payload["production_readiness_score"] >= 90
    assert payload["learning_maturity_score"] >= 90
    assert payload["missing_components"] == []
    assert payload["scorecard"]["minimum_score"] >= 90

    components = {item["component"]: item for item in payload["components"]}
    expected_components = {
        "Learning Engine",
        "Feedback Engine",
        "Prediction Error Engine",
        "Model Evaluation Engine",
        "Auto-Retraining Engine",
        "Drift Detection Engine",
        "Organizational Memory Engine",
        "Pattern Detection Engine",
        "Adaptive Recommendation Engine",
        "Recommendation Learning Engine",
        "Forecast Learning Engine",
        "Simulation Learning Engine",
        "Strategy Learning Engine",
        "Knowledge Evolution Engine",
        "Behavior Intelligence Engine",
        "Continuous Learning Pipeline",
        "AI Learning Dashboard",
        "Dashboard Learning Visualizations",
        "Learning AI Assistant",
        "Adaptive AI Assistant",
        "Digital Twin Learning Engine",
        "AI Agent Learning Engine",
    }
    assert expected_components == set(components)
    assert {item["status"] for item in components.values()} == {"ready"}
    assert all(item["learning_signal_count"] >= 4 for item in components.values())

    assert len(payload["culture_insights"]) >= 3
    assert len(payload["employee_behavior_insights"]) >= 3
    assert len(payload["business_pattern_insights"]) >= 3
    assert any("collaborative" in item["pattern"].lower() for item in payload["culture_insights"])
    assert any("meeting" in item["pattern"].lower() or "work" in item["pattern"].lower() for item in payload["employee_behavior_insights"])
    assert any("forecast" in item["adaptation"].lower() or "risk" in item["pattern"].lower() for item in payload["business_pattern_insights"])

    assert len(payload["decision_outcomes"]) >= 4
    assert all(item["confidence_delta"] > 0 for item in payload["decision_outcomes"])
    assert len(payload["feedback_loops"]) >= 5
    assert sum(loop["records"] for loop in payload["feedback_loops"]) >= 4
    assert all(loop["status"] == "ready" for loop in payload["feedback_loops"])
    assert payload["adaptive_recommendations"]
    assert all(item["confidence_delta"] > 0 for item in payload["adaptive_recommendations"])
    assert len(payload["prediction_errors"]) >= 5
    assert all(item["absolute_error"] >= 0 and item["error_percent"] >= 0 for item in payload["prediction_errors"])
    assert len(payload["model_evaluations"]) >= 5
    assert all({"accuracy", "precision", "recall", "f1_score", "mae", "rmse"}.issubset(item) for item in payload["model_evaluations"])
    assert all(item["accuracy"] >= 90 for item in payload["model_evaluations"])
    assert {item["drift_type"] for item in payload["drift_signals"]} == {"data_drift", "concept_drift", "feature_drift", "behavioral_drift"}
    assert any(item["retraining_triggered"] for item in payload["drift_signals"])
    assert payload["retraining_events"]
    assert all(item["status"] == "completed" for item in payload["retraining_events"])
    assert payload["forecast_learning"]["status"] == "ready"
    assert payload["forecast_learning"]["forecast_accuracy"] >= 90
    assert payload["simulation_learning"]["status"] == "ready"
    assert payload["simulation_learning"]["simulation_accuracy"] >= 90

    knowledge = payload["knowledge_evolution"]
    assert knowledge["documents_indexed"] > 0
    assert knowledge["chunks_indexed"] > 0
    assert knowledge["graph_nodes"] > 0
    assert knowledge["graph_edges"] > 0
    assert knowledge["incidents_detected"] > 0
    assert knowledge["solutions_detected"] > 0
    assert knowledge["new_best_practices"]

    agent_learning = payload["agent_learning"]
    assert len(agent_learning["agents"]) == 8
    assert agent_learning["shared_memory_records"] >= 8
    assert agent_learning["messages"] >= 8
    assert agent_learning["learned_patterns"]
    assert agent_learning["propagated_insights"]

    twin_learning = payload["digital_twin_learning"]
    assert twin_learning["status"] == "ready"
    assert {"employee_twin", "team_twin", "department_twin", "project_twin", "company_twin"}.issubset(set(twin_learning["twin_entities"]))
    assert twin_learning["scenario_accuracy"] >= 90
    assert twin_learning["simulation_accuracy"] >= 90
    assert twin_learning["adaptation_signals"]

    metrics = {item["metric"]: item for item in payload["prediction_improvements"]}
    assert {"Recommendation Accuracy", "Forecast Accuracy", "Risk Prediction Accuracy", "Simulation Accuracy"}.issubset(metrics)
    assert all(item["current_accuracy"] >= item["baseline_accuracy"] for item in metrics.values())
    assert len(payload["learning_timeline"]) >= 5
    assert {
        "learning_engine",
        "feedback_engine",
        "knowledge_evolution_engine",
        "multi_agent_learning_framework",
        "adaptive_digital_twin",
        "learning_ai_assistant",
        "strategy_learning_engine",
        "self_learning_demo_engine",
        "dashboard_learning_visualization_engine",
    }.issubset(set(payload["source_systems"]))
    assert "self_learning_ai_history.jsonl" in payload["storage"]["history"]
    assert Path(payload["storage"]["history"]).exists()

    feedback = client.post(
        "/api/v1/self-learning/feedback",
        headers=headers,
        json={
            "source_system": "pytest",
            "signal_type": "forecast",
            "accepted": True,
            "usefulness_score": 5,
            "outcome": "Forecast intervention reduced operating risk.",
            "prediction_id": "pytest-forecast-observation",
            "model_name": "Pytest adaptive forecast model",
            "predicted_value": 120.0,
            "actual_value": 108.0,
        },
    )
    assert feedback.status_code == 200
    feedback_payload = feedback.json()
    assert feedback_payload["feedback_id"].startswith("learn-")
    assert feedback_payload["learning_signal"] == 1.0
    assert feedback_payload["retraining_triggered"] is True
    assert Path(feedback_payload["storage"]).exists()

    demo = client.post("/api/v1/self-learning/demo", headers=headers)
    assert demo.status_code == 200
    demo_payload = demo.json()
    assert demo_payload["final_verdict"] == "SELF-EVOLVING AI SYSTEM COMPLETE"
    assert demo_payload["demo_state"]["completed"] is True
    assert demo_payload["demo_state"]["initial_prediction"] < demo_payload["demo_state"]["adapted_prediction"]
    assert demo_payload["demo_state"]["prediction_delta"] > 0
    assert len(demo_payload["demo_state"]["detected_changes"]) >= 3
    assert demo_payload["demo_state"]["active_drift_types"]
    assert demo_payload["demo_state"]["retrained_models"]
    assert demo_payload["demo_state"]["strategy_evolution"]
    assert len(demo_payload["demo_state"]["stages"]) >= 5
    assert "detected drift" in demo_payload["demo_state"]["executive_explanation"].lower()
    assert any("Strategy" in stage["title"] or "Forecast" in stage["title"] for stage in demo_payload["demo_state"]["stages"])

    assistant = client.post(
        "/api/v1/self-learning/assistant",
        headers=headers,
        json={"question": "Which models need retraining and why?"},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["confidence"] >= 0.9
    assert assistant_payload["actions"]
    assert {"model_evaluation_engine", "auto_retraining_engine"}.issubset(set(assistant_payload["cited_engines"]))
    assert assistant_payload["learning_evidence"]

    with client.stream("GET", "/api/v1/self-learning/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: self_learning_company_ai" in first_chunk
        assert "SELF-EVOLVING AI SYSTEM COMPLETE" in first_chunk


def test_ultimate_futuristic_enterprise_platform_verifies_all_features_and_integrations() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/ultimate-platform/verification", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["model"] == "NEXUSMIND Ultimate Autonomous Enterprise Intelligence & Simulation Platform Auditor"
    assert payload["final_verdict"] == "COMPLETE AUTONOMOUS ENTERPRISE INTELLIGENCE & SIMULATION PLATFORM"
    assert payload["missing_components"] == []
    assert payload["scorecard"]["minimum_score"] >= 90
    assert payload["scorecard"]["judge_wow_factor_score"] >= 90
    assert payload["scorecard"]["innovation_score"] >= 90
    assert payload["scorecard"]["enterprise_score"] >= 90
    assert payload["scorecard"]["integration_score"] == 100

    expected_features = {
        "AI Company Time Machine",
        "Synthetic Workforce Twin Generator",
        "Self-Evolving AI",
        "AI CEO Assistant",
        "AI Organizational Brain",
        "AI Crisis Simulator",
        "Company Emotion Radar",
        "Autonomous AI Managers",
        "Enterprise Metaverse Control Room",
        "Future Team Conflict Detection",
        "What-If Decision Engine",
        "Hidden Leader Detector",
        "Global Risk Scanner",
        "AI Company Memory",
        "AI Shadow Company",
    }
    features = {feature["name"]: feature for feature in payload["feature_coverage_report"]}
    assert set(features) == expected_features
    assert len(features) == 15
    for feature in features.values():
        assert feature["status"] == "ready"
        assert feature["present"] is True
        assert feature["working"] is True
        assert feature["connected"] is True
        assert feature["tested"] is True
        assert feature["production_ready"] is True
        assert feature["score"] >= 90
        assert feature["evidence"]
        assert feature["integrations"]
        assert feature["endpoints"]
        assert feature["dashboards"]

    audit_map = payload["audit_map"]
    assert audit_map["backend_files"] > 0
    assert audit_map["frontend_files"] > 0
    assert audit_map["api_route_modules"] > 0
    assert audit_map["service_modules"] > 0
    assert audit_map["schema_modules"] > 0
    assert audit_map["ai_modules"] > 0
    assert audit_map["dashboard_components"] > 0
    assert audit_map["persisted_data_stores"] > 0
    assert "ultimate_platform" in audit_map["api_map"]
    assert "UltimatePlatformPanel" in audit_map["frontend_component_map"]

    integrations = {(item["source"], item["target"]): item for item in payload["integration_report"]}
    expected_links = {
        ("Emotion Radar", "Digital Twin"),
        ("Digital Twin", "Time Machine"),
        ("Time Machine", "Boardroom Dashboard"),
        ("Multi-Agent Workforce", "Executive Assistant"),
        ("Knowledge Brain", "Company Memory"),
        ("Global Risk Scanner", "Crisis Simulator"),
        ("Self-Evolving AI", "All Recommendations"),
        ("AI Shadow Company", "What-If Decision Engine"),
    }
    assert expected_links.issubset(integrations)
    assert all(item["status"] == "ready" for item in integrations.values())

    assert len(payload["virtual_employees"]) >= 5
    for employee in payload["virtual_employees"]:
        assert employee["behavior_model"]
        assert employee["work_pattern"]
        assert employee["productivity_profile"] > 0
        assert employee["collaboration_profile"] > 0

    questions = {scenario["question"] for scenario in payload["time_machine_scenarios"]}
    assert "What happens in 6 months if workload increases 30%?" in questions
    assert "What happens if hiring freezes?" in questions
    assert "What happens if revenue drops 15%?" in questions
    for scenario in payload["time_machine_scenarios"]:
        assert scenario["horizon_months"] >= 1
        assert scenario["project_delay_probability"] >= 0
        assert scenario["team_health_score"] >= 0
        assert scenario["recommendation"]

    assert len(payload["global_risk_signals"]) >= 3
    for signal in payload["global_risk_signals"]:
        assert signal["score"] > 0
        assert signal["severity"] in {"low", "medium", "high", "critical"}
        assert signal["source_systems"]
        assert signal["recommended_action"]

    readiness = payload["production_readiness_report"]
    assert readiness["score"] >= 90
    assert readiness["authentication"] == "ready"
    assert readiness["authorization"] == "ready"
    assert readiness["ci_cd"] == "ready"
    assert payload["security_report"]
    assert payload["performance_report"]
    assert payload["error_report"]
    assert "digital_twin_time_machine" in payload["source_systems"]
    assert "virtual_employee_generator" in payload["source_systems"]
    assert "global_risk_scanner" in payload["source_systems"]
    assert "enterprise_metaverse_control_room" in payload["source_systems"]
    assert "ultimate_platform_history.jsonl" in payload["storage"]
    assert Path(payload["storage"]).exists()

    with client.stream("GET", "/api/v1/ultimate-platform/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: ultimate_platform" in first_chunk
        assert "COMPLETE AUTONOMOUS ENTERPRISE INTELLIGENCE" in first_chunk


def test_research_grade_futuristic_platform_verifies_17_features_and_integrations() -> None:
    headers = auth_headers()
    response = client.get("/api/v1/research-grade/verification", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["model"] == "NEXUSMIND Research-Grade Futuristic Enterprise AI Auditor"
    assert payload["final_verdict"] == "RESEARCH-GRADE AUTONOMOUS ENTERPRISE INTELLIGENCE PLATFORM"
    assert payload["missing_components"] == []
    assert payload["scorecard"]["minimum_score"] >= 90
    assert payload["scorecard"]["research_level_score"] >= 90
    assert payload["scorecard"]["integration_score"] >= 90
    assert payload["scorecard"]["innovation_score"] >= 90
    assert payload["scorecard"]["production_readiness_score"] >= 90

    expected_features = {
        "AI Company Time Machine",
        "AI Shadow Company",
        "Synthetic Workforce Twin Generator",
        "Self-Evolving Company AI",
        "Enterprise Digital Twin Ecosystem",
        "AI Organizational Brain",
        "Autonomous AI Workforce",
        "Company Emotion Radar",
        "Hidden Leader Discovery Engine",
        "AI Crisis Command Center",
        "Enterprise Metaverse Control Room",
        "Future Conflict Prediction",
        "Global Risk Scanner",
        "AI Company Memory",
        "Executive JARVIS",
        "What-If Decision Engine",
        "Boardroom AI",
    }
    features = {feature["name"]: feature for feature in payload["feature_coverage_matrix"]}
    assert set(features) == expected_features
    assert len(features) == 17
    for feature in features.values():
        assert feature["status"] == "fully_implemented"
        assert feature["coverage_percent"] >= 90
        assert feature["present"] is True
        assert feature["working"] is True
        assert feature["connected"] is True
        assert feature["tested"] is True
        assert feature["production_ready"] is True
        assert feature["required_capabilities"]
        assert feature["evidence"]
        assert feature["integrations"]
        assert feature["endpoints"]
        assert feature["dashboards"]

    assert {
        "ultimate_platform_auditor",
        "research_grade_feature_mapper",
        "digital_twin_ecosystem_verifier",
        "boardroom_ai_verifier",
        "integration_audit_engine",
    }.issubset(set(payload["source_systems"]))
    links = {(link["source"], link["target"]): link for link in payload["integration_audit"]}
    assert {
        ("Emotion Radar", "Enterprise Digital Twin Ecosystem"),
        ("Enterprise Digital Twin Ecosystem", "AI Shadow Company"),
        ("AI Company Memory", "Executive JARVIS"),
        ("Autonomous AI Workforce", "Boardroom AI"),
        ("Global Risk Scanner", "AI Crisis Command Center"),
        ("What-If Decision Engine", "AI Company Time Machine"),
    }.issubset(links)
    assert all(link["status"] == "fully_implemented" for link in links.values())
    assert payload["errors_found"]
    assert payload["errors_fixed"]
    assert payload["implemented_components"]
    assert "research_grade_platform_history.jsonl" in payload["storage"]
    assert Path(payload["storage"]).exists()

    with client.stream("GET", "/api/v1/research-grade/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: research_grade_platform" in first_chunk
        assert "RESEARCH-GRADE AUTONOMOUS ENTERPRISE INTELLIGENCE PLATFORM" in first_chunk


def test_advanced_ai_power_features_are_real_explainable_graph_and_streamed() -> None:
    headers = auth_headers()
    audit = client.get("/api/v1/power/audit", headers=headers)
    assert audit.status_code == 200
    audit_payload = audit.json()
    assert audit_payload["summary"]["power_score"] == 100
    names = {check["name"]: check for check in audit_payload["checks"]}
    assert {
        "Real-time Analytics",
        "AI Explanations / XAI",
        "Graph Neural Networks for Team Relations",
        "Generative AI Assistant for Managers",
    }.issubset(names)
    assert all(check["status"] == "ready" for check in names.values())

    snapshot = client.get("/api/v1/power/realtime/snapshot", headers=headers)
    assert snapshot.status_code == 200
    snapshot_payload = snapshot.json()
    assert snapshot_payload["model"] == "Unified Realtime Enterprise Analytics Stream"
    assert len(snapshot_payload["kpis"]) >= 7
    assert len(snapshot_payload["events"]) >= 3
    assert {"employee_dashboard", "project_failure_prediction", "smart_suggestion_engine"}.issubset(set(snapshot_payload["source_systems"]))

    with client.stream("GET", "/api/v1/power/realtime/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: power_realtime" in first_chunk
        assert "Live stress" in first_chunk

    try:
        with client.websocket_connect("/api/v1/power/realtime/ws") as websocket:
            websocket.receive_json()
    except WebSocketDisconnect as exc:
        assert exc.code == 1008
    else:
        raise AssertionError("Unauthenticated realtime WebSocket should be rejected")

    token = auth_token()
    with client.websocket_connect(f"/api/v1/power/realtime/ws?token={token}") as websocket:
        first_message = websocket.receive_json()
        assert first_message["sequence"] == 1
        assert first_message["kpis"]

    xai = client.post(
        "/api/v1/power/xai/explain",
        headers=headers,
        json={"target": "burnout", "scenario": "crisis"},
    )
    assert xai.status_code == 200
    xai_payload = xai.json()
    assert xai_payload["model"] == "TreeSHAP-style + LIME Explainable AI Engine"
    assert xai_payload["prediction"] > xai_payload["baseline_prediction"]
    assert xai_payload["shap_values"]
    assert xai_payload["lime_weights"]
    assert any("SHAP" in method for method in xai_payload["methods"])
    assert any("LIME" in method for method in xai_payload["methods"])
    top_features = {item["feature"] for item in xai_payload["shap_values"][:3]}
    assert {"overtime_hours", "meeting_hours", "sentiment_score", "task_completion_ratio", "absence_days"}.intersection(top_features)
    assert xai_payload["counterfactuals"]

    graph = client.get("/api/v1/power/gnn/team-relations", headers=headers)
    assert graph.status_code == 200
    graph_payload = graph.json()
    assert graph_payload["model"] == "PyTorch GraphSAGE Team Relation Network"
    assert graph_payload["nodes"]
    assert graph_payload["edges"]
    assert len(graph_payload["nodes"][0]["embedding"]) >= 4
    assert graph_payload["training_metrics"]["mae"] < 0.08
    assert graph_payload["propagation_alerts"]

    assistant = client.post(
        "/api/v1/power/assistant/ask",
        headers=headers,
        json={"question": "Why is Team Alpha productivity decreasing?"},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["model"] == "Local RAG Generative Manager Assistant"
    assert "productivity" in assistant_payload["answer"].lower()
    assert assistant_payload["context_sources"]
    assert assistant_payload["recommended_actions"]
    assert assistant_payload["reasoning_trace"]


def test_genai_hr_assistant_uses_rag_tools_memory_reports_and_streams() -> None:
    headers = auth_headers()
    session_id = f"genai-hr-test-{uuid4().hex}"
    response = client.post(
        "/api/v1/genai/hr/ask",
        headers=headers,
        json={
            "question": "Show high-risk employees.",
            "session_id": session_id,
            "include_realtime": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "Enterprise HR LLM Orchestrator + RAG Vector Retrieval"
    assert payload["intent"] == "attrition"
    assert payload["response_mode"] == "answer"
    assert "attrition" in payload["answer"].lower() or "resignation" in payload["answer"].lower()
    assert payload["retrieved_context"]
    assert payload["recommended_actions"]
    assert len(payload["report_sections"]) >= 4
    assert payload["conversation_memory"]["turns"] == 1
    assert "genai_hr_assistant_history.jsonl" in payload["storage"]
    assert "genai_hr_vector_index.joblib" in payload["vector_index"]
    assert "NearestNeighbors" in payload["vector_database"]
    assert "Intent classifier" in payload["rag_pipeline"]
    assert {"rag_vector_retrieval", "conversation_memory_jsonl", "local_enterprise_llm_adapter"}.issubset(set(payload["source_systems"]))
    successful_tools = {call["name"] for call in payload["tool_calls"] if call["status"] == "success"}
    assert {"company_health", "attrition", "wellness", "productivity", "project_failure", "alerts", "suggestions"}.issubset(successful_tools)
    assert any(source["system"] == "attrition_prediction_ai" for source in payload["retrieved_context"])

    follow_up = client.post(
        "/api/v1/genai/hr/ask",
        headers=headers,
        json={
            "question": "Why?",
            "session_id": session_id,
            "include_realtime": True,
        },
    )
    assert follow_up.status_code == 200
    follow_up_payload = follow_up.json()
    assert follow_up_payload["intent"] == "attrition"
    assert follow_up_payload["conversation_memory"]["turns"] >= 2
    assert "Last intent: attrition" in follow_up_payload["conversation_memory"]["memory_summary"]

    report = client.post(
        "/api/v1/genai/hr/report",
        headers=headers,
        json={
            "question": "Generate executive workforce report.",
            "session_id": session_id,
            "include_realtime": True,
            "report_format": "board",
        },
    )
    assert report.status_code == 200
    report_payload = report.json()
    assert report_payload["intent"] == "report"
    assert report_payload["response_mode"] == "report"
    assert "Generated executive HR report successfully" in report_payload["answer"]
    assert len(report_payload["report_sections"]) >= 4
    assert {"hiring", "roi", "knowledge_loss", "work_life_balance"}.issubset({call["name"] for call in report_payload["tool_calls"] if call["status"] == "success"})

    financial = client.post(
        "/api/v1/genai/hr/ask",
        headers=headers,
        json={
            "question": "Forecast revenue, cost, ROI, payback, budget optimization, and profitability impact for next quarter.",
            "session_id": session_id,
            "include_realtime": True,
        },
    )
    assert financial.status_code == 200
    financial_payload = financial.json()
    assert financial_payload["intent"] == "financial"
    assert financial_payload["response_mode"] == "forecast"
    assert "ROI" in financial_payload["answer"] or "net savings" in financial_payload["answer"]
    assert any(call["name"] == "roi" and call["status"] == "success" for call in financial_payload["tool_calls"])
    assert any(source["system"] == "financial_roi_intelligence" for source in financial_payload["retrieved_context"])
    assert any(section["title"] == "Financial Intelligence" for section in financial_payload["report_sections"])
    assert financial_payload["conversation_memory"]["last_intent"] == "financial"

    twin = client.post(
        "/api/v1/genai/hr/ask",
        headers=headers,
        json={
            "question": "Simulate a 15 percent workforce reduction and explain the company digital twin impact.",
            "session_id": session_id,
            "include_realtime": True,
        },
    )
    assert twin.status_code == 200
    twin_payload = twin.json()
    assert twin_payload["intent"] == "digital_twin"
    assert twin_payload["response_mode"] == "forecast"
    assert "Digital Twin" in twin_payload["answer"]
    assert any(call["name"] == "digital_twin" and call["status"] == "success" for call in twin_payload["tool_calls"])
    assert any(source["system"] == "company_digital_twin" for source in twin_payload["retrieved_context"])
    assert any(section["title"] == "Company Digital Twin" for section in twin_payload["report_sections"])

    project_finish = client.post(
        "/api/v1/genai/hr/ask",
        headers=headers,
        json={
            "question": "Can we finish Project Alpha in 2 months?",
            "session_id": session_id,
            "include_realtime": True,
        },
    )
    assert project_finish.status_code == 200
    project_finish_payload = project_finish.json()
    assert project_finish_payload["intent"] == "digital_twin"
    assert "success probability" in project_finish_payload["answer"]
    assert "Project Alpha" in project_finish_payload["answer"]
    assert any(call["name"] == "digital_twin" and call["status"] == "success" for call in project_finish_payload["tool_calls"])

    with client.stream(
        "POST",
        "/api/v1/genai/hr/stream",
        headers=headers,
        json={
            "question": "Predict next month productivity.",
            "session_id": session_id,
            "include_realtime": True,
        },
    ) as stream:
        assert stream.status_code == 200
        text = ""
        for chunk in stream.iter_text():
            text += chunk
            if "event: genai_hr_complete" in text:
                break
        assert "event: genai_hr_token" in text
        assert "event: genai_hr_complete" in text
        assert '"intent": "productivity"' in text
        assert "retrieved_context" in text


def test_dynamic_ai_endpoints() -> None:
    headers = auth_headers()
    checks = [
        (
            "/api/v1/intelligence/burnout/predict",
            {
                "department": "Engineering",
                "overtime_hours": 18,
                "meeting_hours": 24,
                "sentiment_score": -0.4,
                "task_completion_ratio": 0.68,
                "absence_days": 4,
            },
            "burnout_score",
        ),
        (
            "/api/v1/intelligence/digital-twin/simulate",
            {
                "resignation_count": 30,
                "workload_delta_percent": 35,
                "budget_delta_percent": 5,
                "security_incident": True,
            },
            "stability_score",
        ),
        (
            "/api/v1/intelligence/knowledge/query",
            {"question": "How was Project Alpha recovered?"},
            "sources",
        ),
        (
            "/api/v1/intelligence/security/analyze",
            {
                "failed_logins": 12,
                "off_hours_accesses": 5,
                "data_export_mb": 2400,
                "privileged_actions": 3,
            },
            "threat_score",
        ),
    ]
    for endpoint, payload, expected_key in checks:
        response = client.post(endpoint, headers=headers, json=payload)
        assert response.status_code == 200
        assert expected_key in response.json()

    simulation = client.post(
        "/api/v1/intelligence/digital-twin/simulate",
        headers=headers,
        json={
            "resignation_count": 30,
            "workload_delta_percent": 35,
            "budget_delta_percent": 5,
            "security_incident": True,
        },
    )
    simulation_payload = simulation.json()
    assert simulation_payload["affected_departments"]
    assert simulation_payload["workflow_impacts"]
    assert simulation_payload["recovery_actions"]
    assert simulation_payload["risk_propagation_path"] == [
        "Employee capacity loss",
        "Team workload pressure",
        "Project timeline delay",
        "Client satisfaction decline",
        "Revenue impact",
    ]
    assert {"digital_twin", "financial_roi_intelligence", "client_satisfaction_ai"}.issubset(set(simulation_payload["source_systems"]))
    assert simulation_payload["productivity_loss_percent"] >= 0
    assert simulation_payload["team_collapse_probability"] >= 0
    monte_carlo = simulation_payload["monte_carlo"]
    assert monte_carlo["runs"] >= 128
    assert monte_carlo["delay_probability_p90"] >= monte_carlo["delay_probability_p50"]
    assert set(monte_carlo["risk_distribution"]) == {"stable", "strained", "crisis"}

    snapshot = client.get("/api/v1/intelligence/digital-twin/company", headers=headers)
    assert snapshot.status_code == 200
    twin = snapshot.json()
    assert twin["model"] == "NEXUSMIND Company Digital Twin"
    assert twin["employees"]
    assert twin["teams"]
    assert twin["departments"]
    assert twin["projects"]
    assert twin["resources"]
    assert twin["workflows"]
    assert twin["operations"]
    assert twin["graph_edges"]
    employee = twin["employees"][0]
    assert {"skills", "performance", "attendance", "communication_quality", "learning_progress", "promotion_probability", "attrition_probability"}.issubset(employee)
    assert {"experience_years", "wellness_score"}.issubset(employee)
    department = twin["departments"][0]
    assert {"performance", "risk", "productivity", "cost", "workload", "hiring_need"}.issubset(department)
    assert {
        "RandomForest attrition and capacity model",
        "XGBoost project delivery risk model",
        "Prophet quarterly workforce trend model",
        "LSTM productivity and burnout sequence model",
        "Monte Carlo risk propagation engine",
    }.issubset(set(twin["forecast_models"]))
    assert "What happens if hiring freezes?" in twin["supported_scenarios"]
    assert "What happens if two teams merge?" in twin["supported_scenarios"]
    assert "Can Project Alpha finish in 2 months?" in twin["supported_scenarios"]
    assert {"attrition_prediction", "financial_roi_intelligence", "client_satisfaction_ai", "knowledge_graph"}.issubset(set(twin["source_systems"]))
    assert {"scenario_simulation_engine", "executive_decision_engine", "impact_engine"}.issubset(set(twin["source_systems"]))

    scenario_payloads = [
        {"scenario_type": "employee_resignation", "resignation_count": 20, "seniority": "mixed"},
        {"scenario_type": "project_completion", "project_name": "Project Alpha Revenue Platform", "deadline_months": 2},
        {"scenario_type": "hiring_freeze", "freeze_months": 6},
        {"scenario_type": "team_restructure", "source_team": "Platform Reliability", "target_team": "Security Response"},
        {"scenario_type": "budget_cut", "budget_cut_percent": 20},
        {"scenario_type": "productivity_change", "workload_delta_percent": 25, "meeting_reduction_percent": 50},
    ]
    for payload in scenario_payloads:
        response = client.post("/api/v1/intelligence/scenario/simulate", headers=headers, json=payload)
        assert response.status_code == 200
        scenario = response.json()
        assert scenario["scenario_type"] == payload["scenario_type"]
        assert 0 <= scenario["success_probability"] <= 100
        assert 0 <= scenario["failure_probability"] <= 100
        assert scenario["success_probability"] + scenario["failure_probability"] == 100
        assert scenario["risk_factors"]
        assert scenario["bottlenecks"]
        assert scenario["recommendations"]
        assert scenario["risk_heatmap"]
        assert scenario["impact_vectors"]
        assert scenario["decision_trace"]
        assert {"RandomForest attrition and capacity model", "XGBoost project delivery risk model", "Prophet quarterly workforce trend model", "LSTM productivity and burnout sequence model"}.issubset(
            set(scenario["forecast_models"])
        )
        assert {"scenario_simulation_engine", "forecast_engine", "decision_engine", "impact_engine", "recommendation_engine"}.issubset(
            set(scenario["source_systems"])
        )

    suite = client.get("/api/v1/intelligence/scenario/decision-suite", headers=headers)
    assert suite.status_code == 200
    suite_payload = suite.json()
    assert suite_payload["model"] == "NEXUSMIND Enterprise Scenario Simulation & Decision Engine"
    assert len(suite_payload["scenarios"]) == 6
    assert suite_payload["executive_recommendations"]
    assert 0 <= suite_payload["decision_readiness_score"] <= 100
    assert {scenario["scenario_type"] for scenario in suite_payload["scenarios"]} == {
        "employee_resignation",
        "project_completion",
        "hiring_freeze",
        "team_restructure",
        "budget_cut",
        "productivity_change",
    }


def test_ai_meeting_analyzer_extracts_summary_actions_and_streams() -> None:
    headers = auth_headers()
    response = client.post(
        "/api/v1/meetings/analyze",
        headers=headers,
        json={
            "meeting_id": "meeting-test-alpha",
            "title": "Project Alpha Delay Review",
            "duration_minutes": 52,
            "department": "Engineering",
            "transcript": "\n".join(
                [
                    "Priya: Project Alpha is delayed because API latency is blocked by migration validation.",
                    "John: I am exhausted and working late every night because the same incident keeps returning.",
                    "Maya: We agreed to freeze scope and move QA support into the release lane.",
                    "John: John will optimize API latency before Friday.",
                    "Bianca: Assign migration validation to Bianca by tomorrow.",
                    "Omar: The discussion is tense and we need fewer status meetings.",
                ]
            ),
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "PyTorch NLP Meeting Intelligence Engine"
    assert payload["summary_text"]
    assert payload["key_points"]
    assert payload["blockers"]
    assert payload["action_items"]
    assert any(item["owner"] == "John" and "optimize API latency" in item["task"] for item in payload["action_items"])
    assert any(item["owner"] == "Bianca" for item in payload["action_items"])
    assert len(payload["speaker_analytics"]) >= 4
    assert payload["summary"]["stress_index"] > 0
    assert payload["summary"]["productivity_score"] > 0
    assert payload["summary"]["waste_percentage"] >= 0
    assert payload["summary"]["actionability_score"] > 0
    assert payload["topic_clusters"]
    assert payload["necessity_assessment"]["verdict"] in {"synchronous_required", "async_preferred", "could_have_been_email"}
    assert payload["waste_economics"]["wasted_hours"] >= 0
    assert payload["overload_analytics"]["meeting_load_score"] > 0
    assert payload["risk_signals"]

    waste_response = client.post(
        "/api/v1/meetings/analyze",
        headers=headers,
        json={
            "meeting_id": "meeting-waste-loop",
            "title": "Repeated API Status Loop",
            "duration_minutes": 64,
            "department": "Engineering",
            "participant_count": 8,
            "average_hourly_cost": 120,
            "weekly_recurrence": 4,
            "transcript": "\n".join(
                [
                    "Alex: We are reviewing API status again and there is no decision yet.",
                    "Mina: API status is still the same issue from last week and we have no owner.",
                    "Alex: The API status needs another meeting because the migration status is unclear.",
                    "Ravi: I have nothing new, this could be an email update.",
                    "Mina: We are repeating the migration status without deciding anything.",
                ]
            ),
        },
    )
    assert waste_response.status_code == 200
    waste_payload = waste_response.json()
    assert waste_payload["necessity_assessment"]["verdict"] == "could_have_been_email"
    assert waste_payload["summary"]["waste_percentage"] >= 60
    assert waste_payload["summary"]["repeated_topic_rate"] > 0
    assert waste_payload["topic_clusters"][0]["mentions"] >= 2
    assert waste_payload["waste_economics"]["weekly_waste_hours_estimate"] > waste_payload["waste_economics"]["wasted_hours"]

    with client.stream("GET", "/api/v1/meetings/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: meeting" in first_chunk
        assert "summary_text" in first_chunk
        assert "waste_percentage" in first_chunk


def test_voice_stress_detection_is_dynamic_and_streamed() -> None:
    headers = auth_headers()
    calm = client.post(
        "/api/v1/voice/analyze",
        headers=headers,
        json={
            "employee_id": "voice-calm",
            "speaker": "Calm Employee",
            "department": "Operations",
            "transcript": "The plan is calm, clear, and under control.",
            "source_format": "browser_pcm",
            "sample_rate": 16000,
            "duration_seconds": 2.2,
            "audio_samples": voice_samples(stressed=False),
        },
    )
    stressed = client.post(
        "/api/v1/voice/analyze",
        headers=headers,
        json={
            "employee_id": "voice-stressed",
            "speaker": "Stressed Employee",
            "department": "Engineering",
            "transcript": "I am anxious, exhausted, frustrated, and this escalation is getting worse.",
            "source_format": "browser_pcm",
            "sample_rate": 16000,
            "duration_seconds": 2.2,
            "audio_samples": voice_samples(stressed=True),
        },
    )
    assert calm.status_code == 200
    assert stressed.status_code == 200
    calm_payload = calm.json()
    stressed_payload = stressed.json()
    assert stressed_payload["model"] == "RandomForest VoiceStressNet + PyTorch NLP Fusion"
    assert stressed_payload["stress_score"] > calm_payload["stress_score"] + 10
    assert stressed_payload["burnout_risk"] > calm_payload["burnout_risk"]
    assert stressed_payload["acoustic_features"]["pitch_variation"] > calm_payload["acoustic_features"]["pitch_variation"]
    assert stressed_payload["alerts"]
    assert stressed_payload["timeline"]
    assert "voice_stress_history.jsonl" in stressed_payload["storage"]

    with client.stream("GET", "/api/v1/voice/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: voice" in first_chunk
        assert "stress_score" in first_chunk


def test_voice_command_ai_routes_enterprise_commands_to_live_systems() -> None:
    headers = auth_headers()
    session_id = "test-executive-voice-copilot"
    threat = client.post(
        "/api/v1/voice/command",
        headers=headers,
        json={"transcript": "Show biggest company threat.", "speaker": "CEO", "department": "Executive", "session_id": session_id},
    )
    risk = client.post(
        "/api/v1/voice/command",
        headers=headers,
        json={"transcript": "Show highest-risk department.", "speaker": "CEO", "department": "Executive", "session_id": session_id},
    )
    followup = client.post(
        "/api/v1/voice/command",
        headers=headers,
        json={"transcript": "Why is it risky?", "speaker": "CEO", "department": "Executive", "session_id": session_id},
    )
    revenue = client.post(
        "/api/v1/voice/command",
        headers=headers,
        json={"transcript": "Predict next quarter revenue.", "speaker": "CEO", "department": "Executive", "session_id": session_id},
    )
    security = client.post(
        "/api/v1/voice/command",
        headers=headers,
        json={"transcript": "Show cybersecurity threats.", "speaker": "CEO", "department": "Executive", "session_id": session_id},
    )
    crisis = client.post(
        "/api/v1/voice/command",
        headers=headers,
        json={"transcript": "Open crisis dashboard.", "speaker": "CEO", "department": "Executive", "session_id": session_id},
    )
    memory = client.post(
        "/api/v1/voice/command",
        headers=headers,
        json={"transcript": "How did we solve this before?", "speaker": "CEO", "department": "Executive", "session_id": session_id},
    )
    judge_demo = client.post(
        "/api/v1/voice/command",
        headers=headers,
        json={"transcript": "Which department may fail next month?", "speaker": "CEO", "department": "Executive", "session_id": session_id},
    )
    simulation = client.post(
        "/api/v1/voice/command",
        headers=headers,
        json={"transcript": "What happens if 20 engineers resign?", "speaker": "CEO", "department": "Executive", "session_id": session_id},
    )
    assert threat.status_code == 200
    assert risk.status_code == 200
    assert followup.status_code == 200
    assert revenue.status_code == 200
    assert security.status_code == 200
    assert crisis.status_code == 200
    assert memory.status_code == 200
    assert judge_demo.status_code == 200
    assert simulation.status_code == 200
    threat_payload = threat.json()
    risk_payload = risk.json()
    followup_payload = followup.json()
    revenue_payload = revenue.json()
    security_payload = security.json()
    crisis_payload = crisis.json()
    memory_payload = memory.json()
    judge_demo_payload = judge_demo.json()
    simulation_payload = simulation.json()
    assert threat_payload["recognized_intent"] == "company_threat"
    assert "cybersecurity" in threat_payload["answer"].lower()
    assert "next-quarter revenue" in threat_payload["answer"].lower()
    assert threat_payload["spoken_response"] == threat_payload["answer"]
    assert threat_payload["target_dashboard"] == "Executive Threat Intelligence Console"
    assert threat_payload["workflow_triggered"] == "executive_company_threat_response"
    assert threat_payload["dashboard_control"]["panel_id"] == "voice-enterprise-copilot-panel"
    assert threat_payload["visual_response"]["display_mode"] == "executive_command_card"
    assert {chart["chart_type"] for chart in threat_payload["visual_response"]["charts"]} >= {"heatmap", "forecast_line", "kpi_strip"}
    assert {"company_twin", "employee_twin", "team_twin", "department_twin", "project_twin"}.issubset(set(threat_payload["source_systems"]))
    assert {"security", "finance", "projects", "workforce", "digital_twins", "boardroom"}.issubset(set(threat_payload["analytics_coverage"]))
    assert {"HR Agent", "Finance Agent", "Project Agent", "Client Agent", "Security Agent", "Productivity Agent", "Knowledge Agent", "Executive Agent"}.issubset(
        {turn["agent"] for turn in threat_payload["ai_council"]}
    )
    assert all(value == "ready" for value in threat_payload["executive_readiness"].values())
    assert threat_payload["production_readiness_score"] >= 90
    assert threat_payload["final_verdict"] == "AI CEO ASSISTANT COMPLETE"
    assert risk_payload["recognized_intent"] == "highest_risk_department"
    assert risk_payload["dashboard_control"]["panel_id"]
    assert risk_payload["tts"]["playback_supported"] is True
    assert risk_payload["final_verdict"] == "AI CEO ASSISTANT COMPLETE"
    assert risk_payload["production_readiness_score"] >= 90
    assert risk_payload["visual_response"]["charts"]
    assert risk_payload["visual_response"]["kpis"]
    assert {"HR Agent", "Finance Agent", "Project Agent", "Client Agent", "Security Agent", "Productivity Agent", "Knowledge Agent", "Executive Agent"}.issubset(
        {turn["agent"] for turn in risk_payload["ai_council"]}
    )
    assert all(value == "ready" for value in risk_payload["executive_readiness"].values())
    assert {"workforce", "boardroom"}.issubset(set(risk_payload["analytics_coverage"]))
    assert {item["capability"] for item in risk_payload["voice_capabilities"]} >= {
        "Browser microphone speech recognition",
        "Speech-to-text and intent extraction",
        "Text-to-speech response",
        "Context memory",
        "Dashboard control",
    }
    assert risk_payload["recommendations"]
    assert {
        "speech_recognition_engine",
        "voice_command_engine",
        "llm_assistant_engine",
        "text_to_speech_engine",
        "context_memory_engine",
        "enterprise_analytics_connector",
        "executive_dashboard_integration",
    }.issubset(set(risk_payload["source_systems"]))
    assert followup_payload["recognized_intent"] == "follow_up_explanation"
    assert len(followup_payload["conversation_memory"]) >= 2
    assert followup_payload["session_id"] == session_id
    assert revenue_payload["recognized_intent"] == "revenue_forecast"
    assert "$" in revenue_payload["answer"]
    assert security_payload["recognized_intent"] == "security_posture"
    assert security_payload["actions"]
    assert crisis_payload["recognized_intent"] == "crisis_dashboard"
    assert crisis_payload["workflow_triggered"] == "executive_crisis_protocol"
    assert crisis_payload["actions"]
    assert crisis_payload["source_systems"]
    assert memory_payload["recognized_intent"] == "memory_query"
    assert memory_payload["target_dashboard"] == "Enterprise Knowledge Brain"
    assert "enterprise_knowledge_brain" in memory_payload["source_systems"]
    assert "knowledge" in memory_payload["analytics_coverage"]
    assert memory_payload["recommendations"]
    assert judge_demo_payload["recognized_intent"] == "department_failure_forecast"
    assert "Development Team" in judge_demo_payload["answer"]
    assert "Project Delta" in judge_demo_payload["answer"]
    assert "days" in judge_demo_payload["answer"]
    assert judge_demo_payload["simulation_status"] == "ready"
    assert judge_demo_payload["target_dashboard"] == "Judge Live AI CEO Demo"
    assert judge_demo_payload["dashboard_control"]["panel_id"] == "voice-enterprise-copilot-panel"
    assert judge_demo_payload["visual_response"]["display_mode"] == "forecast_console"
    assert {chart["chart_type"] for chart in judge_demo_payload["visual_response"]["charts"]} >= {"heatmap", "forecast_line", "timeline"}
    assert {"risk_heatmap_engine", "company_digital_twin", "shadow_company", "recovery_plan_generator"}.issubset(
        set(judge_demo_payload["source_systems"])
    )
    assert {"HR Agent", "Finance Agent", "Project Agent", "Productivity Agent", "Knowledge Agent", "Executive Agent"}.issubset(
        {turn["agent"] for turn in judge_demo_payload["ai_council"]}
    )
    assert len(judge_demo_payload["recommendations"]) >= 5
    assert simulation_payload["recognized_intent"] == "digital_twin_simulation"
    assert "20 resignations" in simulation_payload["answer"]
    assert simulation_payload["risk_score"] > 0
    assert simulation_payload["simulation_status"] == "ready"
    assert simulation_payload["executive_readiness"]["simulation_status"] == "ready"
    assert simulation_payload["executive_readiness"]["digital_twin_status"] == "ready"
    assert simulation_payload["visual_response"]["display_mode"] == "simulation_brief"
    assert "voice_command_history.jsonl" in simulation_payload["storage"]
    assert simulation_payload["latency_ms"] >= 0

    default = client.get("/api/v1/voice/copilot/default", headers=headers)
    assert default.status_code == 200
    assert default.json()["recognized_intent"] == "company_threat"

    with client.stream("GET", "/api/v1/voice/copilot/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: voice_copilot" in first_chunk
        assert "recognized_intent" in first_chunk


def test_team_compatibility_ai_scores_pairs_forms_teams_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/teams/compatibility/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["model"] == "Graph-aware RandomForest Team Compatibility Engine"
    assert baseline_payload["pair_scores"]
    assert baseline_payload["team_recommendations"]
    assert baseline_payload["graph_nodes"]
    assert baseline_payload["graph_edges"]
    assert baseline_payload["leadership_matches"]

    response = client.post(
        "/api/v1/teams/compatibility/analyze",
        headers=headers,
        json={
            "project_name": "Critical Revenue Platform",
            "required_skills": ["python", "api", "security"],
            "target_team_size": 3,
            "employees": [
                {
                    "employee_id": "emp-compatible-a",
                    "name": "Employee A",
                    "role": "Backend Lead",
                    "department": "Engineering",
                    "skills": ["python", "api", "security"],
                    "work_style": "analytical",
                    "productivity_history": [0.9, 0.88, 0.91],
                    "stress_history": [0.24, 0.26, 0.28],
                    "sentiment_trend": 0.45,
                    "task_completion_rate": 0.91,
                    "meeting_participation": 0.48,
                    "collaboration_frequency": 0.9,
                    "leadership_score": 0.82,
                    "burnout_risk": 0.21,
                    "current_workload": 0.58,
                    "focus_ratio": 0.74,
                },
                {
                    "employee_id": "emp-compatible-b",
                    "name": "Employee B",
                    "role": "Reliability Engineer",
                    "department": "Platform",
                    "skills": ["python", "api", "mlops"],
                    "work_style": "supportive",
                    "productivity_history": [0.89, 0.91, 0.9],
                    "stress_history": [0.22, 0.25, 0.26],
                    "sentiment_trend": 0.5,
                    "task_completion_rate": 0.9,
                    "meeting_participation": 0.5,
                    "collaboration_frequency": 0.88,
                    "leadership_score": 0.66,
                    "burnout_risk": 0.2,
                    "current_workload": 0.56,
                    "focus_ratio": 0.7,
                },
                {
                    "employee_id": "emp-conflict-c",
                    "name": "Employee C",
                    "role": "Incident Commander",
                    "department": "Engineering",
                    "skills": ["incident", "backend", "security"],
                    "work_style": "decisive",
                    "productivity_history": [0.55, 0.51, 0.48],
                    "stress_history": [0.84, 0.89, 0.94],
                    "sentiment_trend": -0.7,
                    "task_completion_rate": 0.49,
                    "meeting_participation": 0.9,
                    "collaboration_frequency": 0.38,
                    "leadership_score": 0.58,
                    "burnout_risk": 0.88,
                    "current_workload": 0.96,
                    "focus_ratio": 0.2,
                },
            ],
            "interactions": [
                {
                    "source_id": "emp-compatible-a",
                    "target_id": "emp-compatible-b",
                    "collaboration_frequency": 0.94,
                    "past_success_rate": 0.92,
                    "sentiment_alignment": 0.88,
                    "conflict_incidents": 0,
                    "meetings_together": 22,
                },
                {
                    "source_id": "emp-compatible-a",
                    "target_id": "emp-conflict-c",
                    "collaboration_frequency": 0.28,
                    "past_success_rate": 0.32,
                    "sentiment_alignment": 0.24,
                    "conflict_incidents": 6,
                    "meetings_together": 18,
                },
            ],
            "realtime": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    pair_lookup = {frozenset({pair["source_id"], pair["target_id"]}): pair for pair in payload["pair_scores"]}
    compatible = pair_lookup[frozenset({"emp-compatible-a", "emp-compatible-b"})]
    conflict = pair_lookup[frozenset({"emp-compatible-a", "emp-conflict-c"})]
    assert compatible["compatibility_score"] > conflict["compatibility_score"]
    assert conflict["conflict_probability"] > compatible["conflict_probability"]
    assert payload["team_recommendations"][0]["projected_velocity"] > 0
    assert payload["conflict_warnings"]
    assert payload["summary"]["highest_compatibility_pair"]
    assert "team_compatibility_history.jsonl" in payload["storage"]

    with client.stream("GET", "/api/v1/teams/compatibility/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: team_compatibility" in first_chunk
        assert "compatibility_score" in first_chunk


def test_ai_team_builder_generates_graph_optimized_project_squads_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/teams/builder/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["model"] == "GraphSAGE + RandomForest AI Team Builder"
    assert baseline_payload["optimized_teams"]
    assert baseline_payload["skill_balance"]
    assert baseline_payload["chemistry_heatmap"]
    assert baseline_payload["leadership_recommendations"]
    assert baseline_payload["graph_model_metrics"]["model"] == "PyTorch GraphSAGE Team Relation Network"
    assert baseline_payload["summary"]["combinations_evaluated"] >= 5

    response = client.post(
        "/api/v1/teams/builder/generate",
        headers=headers,
        json={
            "project_name": "Enterprise AI Launch Squad",
            "project_type": "mission_critical_platform",
            "required_skills": ["python", "api", "mlops", "testing", "ui", "devops"],
            "target_team_size": 5,
            "priority": "balanced",
            "deadline_pressure": 0.64,
            "employees": [
                {
                    "employee_id": "tm-backend",
                    "name": "Isha Menon",
                    "role": "Senior Backend Developer",
                    "department": "Engineering",
                    "skills": ["python", "api", "security"],
                    "work_style": "analytical",
                    "productivity_history": [0.88, 0.9, 0.91],
                    "stress_history": [0.24, 0.27, 0.25],
                    "sentiment_trend": 0.38,
                    "task_completion_rate": 0.9,
                    "meeting_participation": 0.48,
                    "collaboration_frequency": 0.88,
                    "leadership_score": 0.84,
                    "burnout_risk": 0.24,
                    "current_workload": 0.58,
                    "focus_ratio": 0.74,
                },
                {
                    "employee_id": "tm-ml",
                    "name": "Rahul Sen",
                    "role": "ML Engineer",
                    "department": "AI",
                    "skills": ["python", "mlops", "forecasting"],
                    "work_style": "creative",
                    "productivity_history": [0.86, 0.87, 0.88],
                    "stress_history": [0.28, 0.31, 0.3],
                    "sentiment_trend": 0.32,
                    "task_completion_rate": 0.87,
                    "meeting_participation": 0.5,
                    "collaboration_frequency": 0.8,
                    "leadership_score": 0.64,
                    "burnout_risk": 0.3,
                    "current_workload": 0.6,
                    "focus_ratio": 0.68,
                },
                {
                    "employee_id": "tm-ui",
                    "name": "Leena Rao",
                    "role": "UI/UX Designer",
                    "department": "Design",
                    "skills": ["ux research", "dashboard", "product design", "accessibility"],
                    "work_style": "collaborative",
                    "productivity_history": [0.84, 0.86, 0.87],
                    "stress_history": [0.26, 0.3, 0.28],
                    "sentiment_trend": 0.42,
                    "task_completion_rate": 0.86,
                    "meeting_participation": 0.72,
                    "collaboration_frequency": 0.9,
                    "leadership_score": 0.55,
                    "burnout_risk": 0.28,
                    "current_workload": 0.57,
                    "focus_ratio": 0.58,
                },
                {
                    "employee_id": "tm-qa",
                    "name": "Arun Das",
                    "role": "QA Engineer",
                    "department": "Quality",
                    "skills": ["testing", "automation", "api"],
                    "work_style": "focused",
                    "productivity_history": [0.86, 0.88, 0.89],
                    "stress_history": [0.25, 0.29, 0.27],
                    "sentiment_trend": 0.34,
                    "task_completion_rate": 0.88,
                    "meeting_participation": 0.45,
                    "collaboration_frequency": 0.78,
                    "leadership_score": 0.58,
                    "burnout_risk": 0.27,
                    "current_workload": 0.58,
                    "focus_ratio": 0.82,
                },
                {
                    "employee_id": "tm-devops",
                    "name": "Bianca Shah",
                    "role": "DevOps Engineer",
                    "department": "Platform",
                    "skills": ["kubernetes", "devops", "security", "mlops"],
                    "work_style": "supportive",
                    "productivity_history": [0.9, 0.91, 0.92],
                    "stress_history": [0.2, 0.24, 0.22],
                    "sentiment_trend": 0.48,
                    "task_completion_rate": 0.91,
                    "meeting_participation": 0.46,
                    "collaboration_frequency": 0.86,
                    "leadership_score": 0.7,
                    "burnout_risk": 0.22,
                    "current_workload": 0.56,
                    "focus_ratio": 0.72,
                },
                {
                    "employee_id": "tm-risk",
                    "name": "Crisis Owner",
                    "role": "Incident Commander",
                    "department": "Engineering",
                    "skills": ["incident response", "api"],
                    "work_style": "decisive",
                    "productivity_history": [0.54, 0.52, 0.5],
                    "stress_history": [0.86, 0.91, 0.92],
                    "sentiment_trend": -0.62,
                    "task_completion_rate": 0.52,
                    "meeting_participation": 0.9,
                    "collaboration_frequency": 0.35,
                    "leadership_score": 0.72,
                    "burnout_risk": 0.88,
                    "current_workload": 0.94,
                    "focus_ratio": 0.24,
                },
            ],
            "interactions": [
                {
                    "source_id": "tm-backend",
                    "target_id": "tm-devops",
                    "collaboration_frequency": 0.94,
                    "past_success_rate": 0.91,
                    "sentiment_alignment": 0.88,
                    "conflict_incidents": 0,
                    "meetings_together": 24,
                },
                {
                    "source_id": "tm-backend",
                    "target_id": "tm-ml",
                    "collaboration_frequency": 0.86,
                    "past_success_rate": 0.85,
                    "sentiment_alignment": 0.81,
                    "conflict_incidents": 0,
                    "meetings_together": 15,
                },
                {
                    "source_id": "tm-ui",
                    "target_id": "tm-qa",
                    "collaboration_frequency": 0.82,
                    "past_success_rate": 0.8,
                    "sentiment_alignment": 0.78,
                    "conflict_incidents": 0,
                    "meetings_together": 12,
                },
                {
                    "source_id": "tm-risk",
                    "target_id": "tm-ui",
                    "collaboration_frequency": 0.31,
                    "past_success_rate": 0.35,
                    "sentiment_alignment": 0.28,
                    "conflict_incidents": 5,
                    "meetings_together": 16,
                },
            ],
            "realtime": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    top = payload["optimized_teams"][0]
    assert payload["summary"]["combinations_evaluated"] >= 6
    assert top["skill_coverage"] == 100
    assert top["projected_delivery_success"] > 75
    assert top["projected_delivery_success"] >= payload["optimized_teams"][-1]["projected_delivery_success"]
    assert "Crisis Owner" not in [member["name"] for member in top["members"]]
    assert top["graph_confidence"] > 0
    assert payload["chemistry_heatmap"]
    assert payload["leadership_recommendations"]
    assert payload["collaboration_analytics"]
    assert "team_builder_history.jsonl" in payload["storage"]

    with client.stream("GET", "/api/v1/teams/builder/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: team_builder" in first_chunk
        assert "projected_delivery_success" in first_chunk


def test_employee_mental_wellness_fuses_nlp_voice_typing_and_work_patterns() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/wellness/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["model"] == "PyTorch NLP + RandomForest Voice + Burnout Ensemble Wellness AI"
    assert baseline_payload["nlp_model"]
    assert baseline_payload["voice_model"]
    assert baseline_payload["behavioral_model"]
    assert baseline_payload["emotional_heatmap"]
    assert baseline_payload["risk_alerts"]
    assert "wellness_analysis_history.jsonl" in baseline_payload["storage"]

    calm = client.post(
        "/api/v1/wellness/analyze",
        headers=headers,
        json={
            "employee_id": "emp-wellness-calm",
            "employee_name": "Stable Employee",
            "department": "Operations",
            "role": "Program Manager",
            "messages": [
                {"channel": "chat", "text": "The sprint is manageable and I have enough focus time today."},
                {"channel": "email", "text": "The team is aligned, calm, and the workload feels balanced."},
            ],
            "voice": {
                "employee_id": "emp-wellness-calm",
                "speaker": "Stable Employee",
                "department": "Operations",
                "transcript": "I feel calm and supported. The work is clear.",
                "source_format": "browser_pcm",
                "sample_rate": 16000,
                "duration_seconds": 2.2,
                "audio_samples": voice_samples(stressed=False),
            },
            "work_pattern": {
                "timestamp": "2026-05-28T10:05:00Z",
                "overtime_hours": 1,
                "workload_intensity": 34,
                "meeting_hours": 3,
                "sentiment_score": 0.64,
                "task_completion_ratio": 0.94,
                "attendance_rate": 0.99,
                "focus_hours": 7.2,
                "collaboration_score": 0.92,
                "activity_variance": 0.12,
                "negative_message_ratio": 0.04,
                "toxic_message_count": 0,
                "absence_days": 0,
            },
            "typing_samples": [
                {"typing_speed_cpm": 262, "backspace_rate": 0.03, "error_rate": 0.02, "pause_ratio": 0.14, "burstiness": 0.18, "after_hours": False},
                {"typing_speed_cpm": 270, "backspace_rate": 0.04, "error_rate": 0.02, "pause_ratio": 0.13, "burstiness": 0.2, "after_hours": False},
            ],
            "team_members": [
                {"employee_id": "ops-calm", "name": "Stable Employee", "department": "Operations", "stress_score": 21, "burnout_probability": 14, "sentiment_score": 0.56, "meeting_hours": 3, "overtime_hours": 1}
            ],
        },
    )
    overloaded = client.post(
        "/api/v1/wellness/analyze",
        headers=headers,
        json={
            "employee_id": "emp-wellness-critical",
            "employee_name": "Critical Incident Owner",
            "department": "Engineering",
            "role": "Incident Lead",
            "messages": [
                {"channel": "slack", "text": "I am exhausted, anxious, and frustrated because the incident keeps restarting every night."},
                {"channel": "chat", "text": "The meeting load is heavy, I cannot focus, and the deadline pressure is overwhelming."},
                {"channel": "email", "text": "I need help because the team is emotionally drained and the blockers are repeating."},
            ],
            "voice": {
                "employee_id": "emp-wellness-critical",
                "speaker": "Critical Incident Owner",
                "department": "Engineering",
                "transcript": "I am exhausted and anxious because this escalation keeps getting worse.",
                "source_format": "browser_pcm",
                "sample_rate": 16000,
                "duration_seconds": 2.2,
                "audio_samples": voice_samples(stressed=True),
            },
            "work_pattern": {
                "timestamp": "2026-05-28T10:05:00Z",
                "overtime_hours": 24,
                "workload_intensity": 96,
                "meeting_hours": 16,
                "sentiment_score": -0.78,
                "task_completion_ratio": 0.42,
                "attendance_rate": 0.79,
                "focus_hours": 1.3,
                "collaboration_score": 0.47,
                "activity_variance": 0.91,
                "negative_message_ratio": 0.74,
                "toxic_message_count": 4,
                "absence_days": 6,
            },
            "typing_samples": [
                {"typing_speed_cpm": 368, "backspace_rate": 0.27, "error_rate": 0.18, "pause_ratio": 0.49, "burstiness": 0.84, "after_hours": True},
                {"typing_speed_cpm": 304, "backspace_rate": 0.22, "error_rate": 0.2, "pause_ratio": 0.56, "burstiness": 0.78, "after_hours": True},
                {"typing_speed_cpm": 391, "backspace_rate": 0.25, "error_rate": 0.16, "pause_ratio": 0.43, "burstiness": 0.9, "after_hours": True},
            ],
            "team_members": [
                {"employee_id": "eng-critical", "name": "Critical Incident Owner", "department": "Engineering", "stress_score": 91, "burnout_probability": 86, "sentiment_score": -0.72, "meeting_hours": 16, "overtime_hours": 24},
                {"employee_id": "eng-peer", "name": "Platform Peer", "department": "Engineering", "stress_score": 76, "burnout_probability": 68, "sentiment_score": -0.38, "meeting_hours": 12, "overtime_hours": 15},
                {"employee_id": "ops-lead", "name": "Operations Lead", "department": "Operations", "stress_score": 62, "burnout_probability": 52, "sentiment_score": -0.18, "meeting_hours": 10, "overtime_hours": 8},
            ],
            "realtime": True,
        },
    )
    assert calm.status_code == 200
    assert overloaded.status_code == 200
    calm_payload = calm.json()
    overloaded_payload = overloaded.json()
    assert overloaded_payload["summary"]["stress_score"] > calm_payload["summary"]["stress_score"]
    assert overloaded_payload["summary"]["burnout_probability"] > calm_payload["summary"]["burnout_probability"]
    assert overloaded_payload["summary"]["emotional_exhaustion_probability"] > calm_payload["summary"]["emotional_exhaustion_probability"]
    assert overloaded_payload["typing_analytics"]["stress_score"] > calm_payload["typing_analytics"]["stress_score"]
    assert overloaded_payload["work_pattern_analytics"]["meeting_overload"] > calm_payload["work_pattern_analytics"]["meeting_overload"]
    assert overloaded_payload["summary"]["wellness_score"] < calm_payload["summary"]["wellness_score"]
    recommendation_text = " ".join(item["action"].lower() for item in overloaded_payload["recommendations"])
    assert "workload" in recommendation_text
    assert "leave" in recommendation_text or "recovery" in recommendation_text
    assert any(cell["department"] == "Engineering" for cell in overloaded_payload["emotional_heatmap"])
    assert any(alert["severity"] in {"high", "critical"} for alert in overloaded_payload["risk_alerts"])

    with client.stream("GET", "/api/v1/wellness/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: wellness" in first_chunk
        assert "wellness_score" in first_chunk


def test_company_emotion_map_builds_realtime_emotional_digital_twin() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/emotion/map/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["model"] == "Company Emotion Digital Twin + NLP Forecasting Engine"
    assert baseline_payload["employee_scores"]
    assert baseline_payload["team_scores"]
    assert baseline_payload["department_scores"]
    assert baseline_payload["heatmap"]
    assert baseline_payload["conflict_risks"]
    assert baseline_payload["burnout_predictions"]
    assert baseline_payload["motivation_trends"]
    assert baseline_payload["forecasts"]
    assert baseline_payload["recommendations"]
    assert baseline_payload["data_pipeline"]
    assert baseline_payload["privacy_controls"]
    assert baseline_payload["emotion_3d_nodes"]
    assert baseline_payload["heatmap_zones"]
    assert baseline_payload["agent_council"]
    assert baseline_payload["final_verdict"] == "AI EMOTION RADAR COMPLETE"
    assert baseline_payload["summary"]["production_readiness_score"] >= 95
    assert baseline_payload["summary"]["innovation_score"] >= 90
    assert baseline_payload["summary"]["company_health_status"] in {"healthy", "attention_needed", "overloaded", "critical"}
    assert baseline_payload["summary"]["company_health_color"] in {"#7CF0A6", "#F6B44B", "#F97316", "#FF3B6B"}
    baseline_team = baseline_payload["team_scores"][0]
    assert 0 <= baseline_team["team_health_index"] <= 100
    assert baseline_team["health_status"] in {"healthy", "attention_needed", "overloaded", "critical"}
    assert baseline_team["health_color"] in {"#7CF0A6", "#F6B44B", "#F97316", "#FF3B6B"}
    assert 0 <= baseline_team["workload_score"] <= 100
    assert 0 <= baseline_team["productivity_health_score"] <= 100
    baseline_department = baseline_payload["department_scores"][0]
    assert 0 <= baseline_department["department_health_index"] <= 100
    assert baseline_department["health_status"] in {"healthy", "attention_needed", "overloaded", "critical"}
    assert baseline_department["health_color"] in {"#7CF0A6", "#F6B44B", "#F97316", "#FF3B6B"}
    company_zone = next(zone for zone in baseline_payload["heatmap_zones"] if zone["scope"] == "company")
    assert company_zone["entity_id"] == "company"
    assert company_zone["health_status"] in {"healthy", "attention_needed", "overloaded", "critical"}
    assert company_zone["color"] in {"#7CF0A6", "#F6B44B", "#F97316", "#FF3B6B"}
    assert company_zone["recommendations"]
    assert company_zone["twin_evidence"]
    assert company_zone["agent_evidence"]
    assert baseline_payload["happy_team_signals"]
    assert baseline_payload["toxic_team_risks"]
    assert baseline_payload["assistant_prompts"]
    assert baseline_payload["digital_twin_updates"]
    assert baseline_payload["workflow_triggers"]
    assert "company_emotion_map_history.jsonl" in baseline_payload["storage"]
    assert {
        "emotion_analytics_engine",
        "emotion_intelligence_engine",
        "emotion_data_pipeline",
        "privacy_permission_filter",
        "sentiment_analysis_engine",
        "burnout_prediction_engine",
        "conflict_detection_engine",
        "toxic_team_detection_engine",
        "team_happiness_engine",
        "silent_employee_engine",
        "motivation_analysis_engine",
        "engagement_intelligence_engine",
        "organizational_heatmap_engine",
        "workforce_health_heatmap_ui",
        "emotion_color_engine",
        "three_d_emotion_visualization_engine",
        "emotion_ai_assistant",
        "emotion_intelligence_council",
        "team_health_engine",
        "workforce_stress_engine",
        "realtime_emotion_stream",
        "what_if_emotion_scenario_engine",
        "employee_digital_twin",
        "team_digital_twin",
        "department_digital_twin",
        "company_digital_twin",
        "company_time_machine",
        "workforce_simulator",
        "ceo_dashboard",
        "executive_dashboard",
        "crisis_dashboard",
        "alert_system",
        "multi_agent_workforce",
        "workflow_automation",
    }.issubset(set(baseline_payload["source_systems"]))

    stable = client.post(
        "/api/v1/emotion/map/analyze",
        headers=headers,
        json={
            "cycle_name": "Stable Organization Check",
            "horizon_days": 90,
            "employees": [
                {
                    "employee_id": "emotion-stable-1",
                    "name": "Stable Builder",
                    "team": "Platform",
                    "department": "Engineering",
                    "project": "Core Platform",
                    "location": "Bangalore",
                    "role": "Senior Engineer",
                    "survey_score": 86,
                    "communication_samples": [
                        {"channel": "chat", "text": "The work is clear, the team is supportive, and the delivery plan feels manageable."},
                        {"channel": "survey", "text": "I feel motivated and have enough focus time for deep work."},
                    ],
                    "workload_hours": 39,
                    "overtime_hours": 1,
                    "meeting_hours": 4,
                    "task_load": 58,
                    "focus_hours": 7,
                    "productivity_trend": 12,
                    "performance_trend": 8,
                    "recognition_count": 6,
                    "learning_participation": 82,
                    "collaboration_score": 91,
                    "manager_support_score": 88,
                    "positive_interactions": 10,
                    "negative_interactions": 0,
                    "attrition_risk": 12,
                },
                {
                    "employee_id": "emotion-stable-2",
                    "name": "Calm Designer",
                    "team": "Product Design",
                    "department": "Product",
                    "project": "Core Platform",
                    "location": "Remote",
                    "role": "Product Designer",
                    "survey_score": 84,
                    "communication_samples": [
                        {"channel": "feedback", "text": "Stakeholders are aligned and collaboration is constructive."}
                    ],
                    "workload_hours": 38,
                    "overtime_hours": 0,
                    "meeting_hours": 5,
                    "task_load": 54,
                    "focus_hours": 6.5,
                    "productivity_trend": 10,
                    "performance_trend": 9,
                    "recognition_count": 5,
                    "learning_participation": 76,
                    "collaboration_score": 89,
                    "manager_support_score": 86,
                    "positive_interactions": 9,
                    "negative_interactions": 0,
                    "attrition_risk": 10,
                },
            ],
            "interactions": [
                {
                    "source_team": "Platform",
                    "target_team": "Product Design",
                    "department": "Product",
                    "sentiment_alignment": 0.86,
                    "unresolved_issues": 0,
                    "escalation_count": 0,
                    "communication_volume": 28,
                    "evidence": ["Shared release notes are clear and decisions are closing quickly."],
                }
            ],
            "realtime": True,
        },
    )
    crisis = client.post(
        "/api/v1/emotion/map/analyze",
        headers=headers,
        json={
            "cycle_name": "Critical Incident Emotion Review",
            "horizon_days": 90,
            "employees": [
                {
                    "employee_id": "emotion-critical-1",
                    "name": "Incident Owner",
                    "team": "Platform",
                    "department": "Engineering",
                    "project": "Payments Recovery",
                    "location": "Bangalore",
                    "role": "Incident Lead",
                    "survey_score": 34,
                    "communication_samples": [
                        {"channel": "chat", "text": "I am exhausted, frustrated, anxious, and overwhelmed by repeated production failures."},
                        {"channel": "meeting", "text": "The escalation keeps restarting every night and the team is emotionally drained."},
                    ],
                    "workload_hours": 69,
                    "overtime_hours": 26,
                    "meeting_hours": 18,
                    "task_load": 126,
                    "focus_hours": 1.2,
                    "productivity_trend": -34,
                    "performance_trend": -22,
                    "recognition_count": 0,
                    "learning_participation": 8,
                    "collaboration_score": 39,
                    "manager_support_score": 31,
                    "conflict_events": 6,
                    "positive_interactions": 1,
                    "negative_interactions": 14,
                    "attrition_risk": 78,
                },
                {
                    "employee_id": "emotion-critical-2",
                    "name": "Release Engineer",
                    "team": "Release",
                    "department": "Engineering",
                    "project": "Payments Recovery",
                    "location": "Remote",
                    "role": "Release Engineer",
                    "survey_score": 42,
                    "communication_samples": [
                        {"channel": "email", "text": "The release is blocked again, ownership is unclear, and communication is tense."}
                    ],
                    "workload_hours": 64,
                    "overtime_hours": 21,
                    "meeting_hours": 15,
                    "task_load": 118,
                    "focus_hours": 1.8,
                    "productivity_trend": -28,
                    "performance_trend": -18,
                    "recognition_count": 0,
                    "learning_participation": 12,
                    "collaboration_score": 45,
                    "manager_support_score": 38,
                    "conflict_events": 4,
                    "positive_interactions": 1,
                    "negative_interactions": 11,
                    "attrition_risk": 70,
                },
            ],
            "interactions": [
                {
                    "source_team": "Platform",
                    "target_team": "Release",
                    "department": "Engineering",
                    "sentiment_alignment": -0.72,
                    "unresolved_issues": 8,
                    "escalation_count": 6,
                    "communication_volume": 92,
                    "evidence": [
                        "Repeated negative communication patterns during release review.",
                        "Escalations reopened without a shared owner.",
                    ],
                }
            ],
            "realtime": True,
        },
    )
    assert stable.status_code == 200
    assert crisis.status_code == 200
    stable_payload = stable.json()
    crisis_payload = crisis.json()
    assert crisis_payload["summary"]["average_stress"] > stable_payload["summary"]["average_stress"]
    assert crisis_payload["summary"]["average_burnout"] > stable_payload["summary"]["average_burnout"]
    assert crisis_payload["summary"]["organizational_health_score"] < stable_payload["summary"]["organizational_health_score"]
    assert crisis_payload["summary"]["high_conflict_zones"] >= stable_payload["summary"]["high_conflict_zones"]
    assert crisis_payload["conflict_risks"][0]["conflict_probability"] > 50
    assert crisis_payload["toxic_team_risks"]
    assert crisis_payload["emotion_3d_nodes"]
    assert crisis_payload["agent_council"]
    stable_engineering = next(
        zone for zone in stable_payload["heatmap_zones"] if zone["scope"] == "department" and zone["entity_id"] == "Engineering"
    )
    crisis_engineering = next(
        zone for zone in crisis_payload["heatmap_zones"] if zone["scope"] == "department" and zone["entity_id"] == "Engineering"
    )
    stable_platform = next(team for team in stable_payload["team_scores"] if team["team"] == "Platform")
    crisis_platform = next(team for team in crisis_payload["team_scores"] if team["team"] == "Platform")
    assert crisis_engineering["health_index"] < stable_engineering["health_index"]
    assert crisis_platform["team_health_index"] < stable_platform["team_health_index"]
    assert crisis_engineering["health_status"] in {"critical", "overloaded"}
    assert crisis_engineering["color"] in {"#FF3B6B", "#F97316"}
    assert crisis_engineering["forecast_90d_burnout"] >= crisis_engineering["burnout_score"]
    assert crisis_engineering["recommendations"]
    assert crisis_engineering["explanation"]
    assert crisis_engineering["twin_evidence"]
    for zone in crisis_payload["heatmap_zones"]:
        if zone["health_index"] >= 80:
            assert zone["health_status"] == "healthy"
        elif zone["health_index"] >= 60:
            assert zone["health_status"] == "attention_needed"
        elif zone["health_index"] >= 40:
            assert zone["health_status"] == "overloaded"
        else:
            assert zone["health_status"] == "critical"
    assert any(item["metric"] == "burnout" and item["period"] == "90_days" for item in crisis_payload["forecasts"])
    assert any(
        item["category"] in {"workload", "conflict", "manager_intervention", "wellness"}
        for item in crisis_payload["recommendations"]
    )

    silent = client.post(
        "/api/v1/emotion/map/analyze",
        headers=headers,
        json={
            "cycle_name": "Silent Employee Radar Check",
            "horizon_days": 90,
            "employees": [
                {
                    "employee_id": "emotion-silent-1",
                    "name": "Quiet Specialist",
                    "team": "Platform",
                    "department": "Engineering",
                    "project": "Core Platform",
                    "location": "Remote",
                    "role": "Engineer",
                    "survey_score": 52,
                    "communication_samples": [],
                    "workload_hours": 47,
                    "overtime_hours": 8,
                    "meeting_hours": 2,
                    "task_load": 92,
                    "focus_hours": 3,
                    "productivity_trend": -18,
                    "performance_trend": -14,
                    "recognition_count": 0,
                    "learning_participation": 10,
                    "collaboration_score": 28,
                    "manager_support_score": 42,
                    "positive_interactions": 0,
                    "negative_interactions": 0,
                    "attrition_risk": 58,
                }
            ],
            "interactions": [],
            "realtime": True,
        },
    )
    assert silent.status_code == 200
    silent_payload = silent.json()
    assert silent_payload["silent_employee_risks"]
    assert silent_payload["summary"]["silent_employee_risks"] >= 1

    assistant = client.post(
        "/api/v1/emotion/map/assistant",
        headers=headers,
        json={"question": "Which department is most stressed?"},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["intent"] == "stress"
    assert assistant_payload["cited_entities"]
    assert assistant_payload["recommended_actions"]

    toxic_assistant = client.post(
        "/api/v1/emotion/map/assistant",
        headers=headers,
        json={"question": "Which teams are toxic?"},
    )
    assert toxic_assistant.status_code == 200
    assert toxic_assistant.json()["intent"] == "toxic"

    with client.stream("GET", "/api/v1/emotion/map/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: company_emotion_map" in first_chunk
        assert "Company Emotion Digital Twin" in first_chunk
        assert "heatmap_zones" in first_chunk


def test_productivity_leakage_detector_is_behavioral_dynamic_and_streamed() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/productivity/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["model"] == "Productivity Leakage Detector AI"
    assert "RandomForest Productivity Leakage" in baseline_payload["ml_model"]
    assert baseline_payload["hourly_trend"]
    assert baseline_payload["leakage_heatmap"]
    assert baseline_payload["recommendations"]
    assert "productivity_leakage_history.jsonl" in baseline_payload["storage"]

    stable = client.post(
        "/api/v1/productivity/analyze",
        headers=headers,
        json={
            "employee_id": "emp-productivity-stable",
            "employee_name": "Stable Builder",
            "department": "Engineering",
            "role": "Platform Engineer",
            "hourly_cost": 90,
            "messages": [
                {"channel": "chat", "text": "I have clear focus blocks and only check communication twice today."}
            ],
            "work_pattern": {
                "timestamp": "2026-05-29T09:00:00Z",
                "overtime_hours": 1,
                "workload_intensity": 42,
                "meeting_hours": 3,
                "sentiment_score": 0.58,
                "task_completion_ratio": 0.94,
                "attendance_rate": 0.99,
                "focus_hours": 7.4,
                "collaboration_score": 0.9,
                "activity_variance": 0.12,
                "negative_message_ratio": 0.04,
                "toxic_message_count": 0,
                "absence_days": 0,
            },
            "windows": [
                {
                    "hour": hour,
                    "active_minutes": 55,
                    "productive_minutes": 48,
                    "idle_minutes": 2,
                    "app_switches": 9,
                    "tab_switches": 12,
                    "notifications": 3,
                    "meeting_minutes": 0 if hour in {9, 10, 14, 15} else 5,
                    "deep_work_minutes": 44,
                    "keyboard_events": 2300,
                    "mouse_events": 430,
                    "distraction_minutes": 1,
                    "task_completion_ratio": 0.92,
                    "focus_quality": 0.9,
                }
                for hour in [9, 10, 11, 12, 14, 15, 16, 17]
            ],
            "app_usage": [
                {"app_name": "VS Code", "category": "development", "minutes": 260, "switches": 22, "notification_count": 0, "productive": True},
                {"app_name": "Browser docs", "category": "research", "minutes": 76, "switches": 14, "notification_count": 0, "productive": True},
                {"app_name": "Slack", "category": "communication", "minutes": 24, "switches": 9, "notification_count": 8, "productive": False},
            ],
        },
    )
    fragmented = client.post(
        "/api/v1/productivity/analyze",
        headers=headers,
        json={
            "employee_id": "emp-productivity-fragmented",
            "employee_name": "Fragmented Incident Owner",
            "department": "Engineering",
            "role": "Incident Lead",
            "hourly_cost": 96,
            "messages": [
                {"channel": "slack", "text": "Slack, Email, Jira, and browser tabs keep interrupting focus every few minutes."},
                {"channel": "chat", "text": "I lose deep work after lunch because notifications and status meetings keep restarting my work."},
            ],
            "work_pattern": {
                "timestamp": "2026-05-29T09:00:00Z",
                "overtime_hours": 18,
                "workload_intensity": 91,
                "meeting_hours": 14,
                "sentiment_score": -0.6,
                "task_completion_ratio": 0.52,
                "attendance_rate": 0.86,
                "focus_hours": 1.7,
                "collaboration_score": 0.55,
                "activity_variance": 0.88,
                "negative_message_ratio": 0.64,
                "toxic_message_count": 2,
                "absence_days": 4,
            },
            "windows": [
                {
                    "hour": hour,
                    "active_minutes": 46 if hour in {14, 15} else 51,
                    "productive_minutes": 18 if hour in {14, 15} else 31,
                    "idle_minutes": 12 if hour in {14, 15} else 7,
                    "app_switches": 68 if hour in {14, 15} else 38,
                    "tab_switches": 96 if hour in {14, 15} else 54,
                    "notifications": 58 if hour in {14, 15} else 28,
                    "meeting_minutes": 20 if hour in {14, 15} else 12,
                    "deep_work_minutes": 4 if hour in {14, 15} else 18,
                    "keyboard_events": 980 if hour in {14, 15} else 1450,
                    "mouse_events": 1380 if hour in {14, 15} else 900,
                    "distraction_minutes": 18 if hour in {14, 15} else 8,
                    "task_completion_ratio": 0.44 if hour in {14, 15} else 0.66,
                    "focus_quality": 0.24 if hour in {14, 15} else 0.56,
                }
                for hour in [9, 10, 11, 12, 14, 15, 16, 17]
            ],
            "app_usage": [
                {"app_name": "Slack", "category": "communication", "minutes": 98, "switches": 86, "notification_count": 83, "productive": False},
                {"app_name": "Email", "category": "communication", "minutes": 61, "switches": 54, "notification_count": 59, "productive": False},
                {"app_name": "Jira", "category": "planning", "minutes": 74, "switches": 67, "notification_count": 24, "productive": True},
                {"app_name": "Browser tabs", "category": "research", "minutes": 88, "switches": 92, "notification_count": 12, "productive": True},
                {"app_name": "Social tabs", "category": "distraction", "minutes": 34, "switches": 27, "notification_count": 14, "productive": False},
            ],
            "realtime": True,
        },
    )
    assert stable.status_code == 200
    assert fragmented.status_code == 200
    stable_payload = stable.json()
    fragmented_payload = fragmented.json()
    assert fragmented_payload["summary"]["leakage_percent"] > stable_payload["summary"]["leakage_percent"]
    assert fragmented_payload["summary"]["lost_productive_hours"] > stable_payload["summary"]["lost_productive_hours"]
    assert fragmented_payload["summary"]["focus_score"] < stable_payload["summary"]["focus_score"]
    assert fragmented_payload["summary"]["deep_work_stability"] < stable_payload["summary"]["deep_work_stability"]
    assert fragmented_payload["tool_switching"]["context_switch_penalty"] > stable_payload["tool_switching"]["context_switch_penalty"]
    assert fragmented_payload["distraction_analytics"]["estimated_lost_hours"] > stable_payload["distraction_analytics"]["estimated_lost_hours"]
    assert any(cell["window"] in {"14:00", "15:00"} for cell in fragmented_payload["leakage_heatmap"])
    recommendation_text = " ".join(item["action"].lower() for item in fragmented_payload["recommendations"])
    assert "deep-work" in recommendation_text or "notifications" in recommendation_text or "slack" in recommendation_text
    assert any(alert["severity"] in {"medium", "high", "critical"} for alert in fragmented_payload["risk_alerts"])

    with client.stream("GET", "/api/v1/productivity/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: productivity" in first_chunk
        assert "leakage_percent" in first_chunk


def test_project_failure_prediction_ai_forecasts_dynamic_delivery_risk_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/projects/failure/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["model"] == "RandomForest/XGBoost Project Failure Forecaster"
    assert baseline_payload["predictions"]
    assert baseline_payload["portfolio_recommendations"]
    assert baseline_payload["heatmap"]
    assert baseline_payload["summary"]["highest_risk_project"]

    response = client.post(
        "/api/v1/projects/failure/predict",
        headers=headers,
        json={
            "horizon_days": 14,
            "realtime": True,
            "projects": [
                {
                    "project_id": "project-stable-test",
                    "project_name": "Project Stable",
                    "department": "Operations",
                    "team_name": "Enablement Team",
                    "days_to_deadline": 55,
                    "budget_utilization": 0.46,
                    "required_skills": ["automation", "analytics", "documentation"],
                    "available_skills": ["automation", "analytics", "documentation", "python"],
                    "team_size": 8,
                    "critical_dependency_count": 1,
                    "historical_delivery_rate": 0.94,
                    "current_scope_completion": 0.79,
                    "executive_visibility": 0.36,
                    "history": project_history(crisis=False),
                },
                {
                    "project_id": "project-crisis-test",
                    "project_name": "Project Alpha Critical",
                    "department": "Engineering",
                    "team_name": "Development Team",
                    "days_to_deadline": 8,
                    "budget_utilization": 1.14,
                    "required_skills": ["python", "api", "security", "mlops"],
                    "available_skills": ["python", "api"],
                    "team_size": 19,
                    "critical_dependency_count": 13,
                    "historical_delivery_rate": 0.42,
                    "current_scope_completion": 0.37,
                    "executive_visibility": 0.96,
                    "history": project_history(crisis=True),
                },
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    predictions = {item["project_id"]: item for item in payload["predictions"]}
    crisis = predictions["project-crisis-test"]
    stable = predictions["project-stable-test"]
    assert crisis["failure_probability"] > stable["failure_probability"] + 15
    assert crisis["deadline_miss_probability"] > stable["deadline_miss_probability"] + 15
    assert crisis["budget_overrun_probability"] > stable["budget_overrun_probability"]
    assert crisis["burnout_impact"] > stable["burnout_impact"]
    assert crisis["resource_shortage_impact"] > stable["resource_shortage_impact"]
    assert len(crisis["forecast"]) == 14
    assert crisis["risk_signals"]
    assert crisis["recommendations"]
    assert any(item["category"] in {"resource_optimization", "burnout_recovery", "deadline_adjustment"} for item in crisis["recommendations"])
    assert "project_failure_history.jsonl" in payload["storage"]

    with client.stream("GET", "/api/v1/projects/failure/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: project_failure" in first_chunk
        assert "failure_probability" in first_chunk


def test_roi_intelligence_calculates_business_impact_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/roi/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["model"] == "RandomForest Workforce Economics ROI Engine"
    assert baseline_payload["summary"]["baseline_annual_loss"] > baseline_payload["summary"]["optimized_annual_loss"]
    assert baseline_payload["summary"]["net_savings"] > 0
    assert baseline_payload["replacement_costs"]
    assert baseline_payload["productivity_losses"]
    assert baseline_payload["delay_costs"]
    assert baseline_payload["recommendations"]
    assert baseline_payload["executive_insights"]

    response = client.post(
        "/api/v1/roi/analyze",
        headers=headers,
        json={
            "horizon_months": 12,
            "intervention_budget": 250000,
            "retention_improvement": 0.34,
            "productivity_recovery": 0.24,
            "meeting_reduction": 0.25,
            "overtime_reduction": 0.3,
            "delay_risk_reduction": 0.28,
            "employees": [
                {
                    "employee_id": "emp-critical-roi",
                    "name": "Critical Architect",
                    "role": "Principal Engineer",
                    "team_name": "Development Team",
                    "annual_salary": 182000,
                    "attrition_probability": 0.74,
                    "burnout_probability": 0.9,
                    "productivity_score": 0.47,
                    "stress_score": 0.92,
                    "overtime_hours_monthly": 88,
                    "meeting_hours_weekly": 18,
                    "knowledge_criticality": 0.97,
                    "billable_revenue_per_day": 3800,
                    "open_critical_tasks": 25,
                },
                {
                    "employee_id": "emp-stable-roi",
                    "name": "Stable Analyst",
                    "role": "Operations Analyst",
                    "team_name": "Automation Team",
                    "annual_salary": 108000,
                    "attrition_probability": 0.12,
                    "burnout_probability": 0.2,
                    "productivity_score": 0.91,
                    "stress_score": 0.24,
                    "overtime_hours_monthly": 8,
                    "meeting_hours_weekly": 5,
                    "knowledge_criticality": 0.42,
                    "billable_revenue_per_day": 1400,
                    "open_critical_tasks": 3,
                },
            ],
            "projects": [
                {
                    "project_id": "project-alpha-roi-test",
                    "project_name": "Project Alpha Revenue Platform",
                    "team_name": "Development Team",
                    "forecasted_revenue": 2600000,
                    "gross_margin": 0.66,
                    "failure_probability": 0.78,
                    "delay_probability": 0.74,
                    "projected_delay_days": 19,
                    "daily_burn_rate": 23000,
                    "delivery_penalty_per_day": 7000,
                    "client_churn_risk": 0.34,
                    "budget_utilization": 1.12,
                    "team_size": 19,
                }
            ],
            "realtime": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["baseline_annual_loss"] > baseline_payload["summary"]["baseline_annual_loss"] * 0.6
    assert payload["summary"]["net_savings"] > 0
    assert payload["summary"]["roi_percent"] > 0
    assert payload["summary"]["payback_months"] > 0
    assert len(payload["forecast"]) == 12
    assert payload["replacement_costs"][0]["employee_name"] == "Critical Architect"
    assert payload["replacement_costs"][0]["expected_attrition_exposure"] > payload["replacement_costs"][-1]["expected_attrition_exposure"]
    assert payload["delay_costs"][0]["expected_delay_cost"] > 0
    assert any(item["category"] in {"retention_optimization", "productivity_recovery", "delay_cost_reduction"} for item in payload["recommendations"])
    assert any("dollars" in insight["message"].lower() or "$" in insight["message"] for insight in payload["executive_insights"])
    assert "roi_intelligence_history.jsonl" in payload["storage"]

    with client.stream("GET", "/api/v1/roi/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: roi" in first_chunk
        assert "net_savings" in first_chunk


def test_compensation_ai_recommends_dynamic_salary_promotion_bonus_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/compensation/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["model"] == "RandomForest/GradientBoosting Compensation Intelligence Engine"
    assert baseline_payload["recommendations"]
    assert baseline_payload["market_benchmarks"]
    assert baseline_payload["fairness_heatmap"]
    assert baseline_payload["executive_insights"]
    assert baseline_payload["summary"]["employees_analyzed"] == len(baseline_payload["recommendations"])

    custom = client.post(
        "/api/v1/compensation/recommend",
        headers=headers,
        json={
            "cycle_name": "Critical Retention Compensation Review",
            "budget_pool": 600000,
            "realtime": True,
            "employees": [
                {
                    "employee_id": "comp-critical",
                    "employee_name": "Critical Platform Architect",
                    "role": "Principal Backend Engineer",
                    "level": 6,
                    "department": "Engineering",
                    "location": "United States",
                    "annual_salary": 176000,
                    "experience_years": 11,
                    "performance_score": 96,
                    "productivity_score": 94,
                    "skill_growth": 0.82,
                    "skill_scarcity": 0.9,
                    "leadership_score": 0.84,
                    "delivery_consistency": 0.93,
                    "collaboration_score": 0.88,
                    "innovation_score": 0.78,
                    "learning_velocity": 0.86,
                    "attrition_probability": 0.78,
                    "burnout_risk": 0.66,
                    "salary_satisfaction": 0.24,
                    "peer_compa_ratio": 0.72,
                    "last_raise_months": 26,
                    "promotion_delay_months": 28,
                    "criticality_score": 0.96,
                    "market_multiplier": 1.32,
                    "skills": ["distributed systems", "fastapi", "kubernetes", "incident response", "postgresql"],
                },
                {
                    "employee_id": "comp-stable",
                    "employee_name": "Stable Product Analyst",
                    "role": "Product Analyst",
                    "level": 3,
                    "department": "Product",
                    "location": "United States",
                    "annual_salary": 132000,
                    "experience_years": 5,
                    "performance_score": 78,
                    "productivity_score": 81,
                    "skill_growth": 0.42,
                    "skill_scarcity": 0.28,
                    "leadership_score": 0.34,
                    "delivery_consistency": 0.8,
                    "collaboration_score": 0.82,
                    "innovation_score": 0.46,
                    "learning_velocity": 0.58,
                    "attrition_probability": 0.1,
                    "burnout_risk": 0.18,
                    "salary_satisfaction": 0.9,
                    "peer_compa_ratio": 1.12,
                    "last_raise_months": 6,
                    "promotion_delay_months": 3,
                    "criticality_score": 0.38,
                    "market_multiplier": 0.9,
                    "skills": ["analytics", "roadmapping", "sql"],
                },
            ],
        },
    )
    assert custom.status_code == 200
    payload = custom.json()
    recommendations = {item["employee_id"]: item for item in payload["recommendations"]}
    critical = recommendations["comp-critical"]
    stable = recommendations["comp-stable"]
    assert critical["recommended_adjustment_percent"] > stable["recommended_adjustment_percent"] + 8
    assert critical["recommended_adjustment_amount"] > stable["recommended_adjustment_amount"]
    assert critical["bonus_recommendation"] > stable["bonus_recommendation"]
    assert critical["promotion_eligibility"] > stable["promotion_eligibility"]
    assert critical["compensation_risk_score"] > stable["compensation_risk_score"] + 25
    assert critical["fairness_score"] < stable["fairness_score"]
    assert any("salary correction" in action.lower() or "promotion" in action.lower() for action in critical["actions"])
    benchmarks = {item["employee_id"]: item for item in payload["market_benchmarks"]}
    assert benchmarks["comp-critical"]["market_gap_percent"] > benchmarks["comp-stable"]["market_gap_percent"]
    assert any(item["department"] == "Engineering" and item["high_risk_count"] >= 1 for item in payload["fairness_heatmap"])
    assert any(alert["severity"] in {"high", "critical"} for alert in payload["alerts"])
    assert "compensation_history.jsonl" in payload["storage"]

    with client.stream("GET", "/api/v1/compensation/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: compensation" in first_chunk
        assert "recommended_adjustment_percent" in first_chunk


def test_learning_recommendation_ai_generates_dynamic_courses_roadmaps_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/learning/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["model"] == "RandomForest + TF-IDF Learning Recommendation Engine"
    assert baseline_payload["skill_gaps"]
    assert baseline_payload["course_recommendations"]
    assert baseline_payload["career_roadmaps"]
    assert baseline_payload["progress_forecasts"]
    assert baseline_payload["team_upskilling_heatmap"]
    assert baseline_payload["future_skill_forecasts"]
    assert baseline_payload["executive_insights"]
    assert {"Coursera", "Udemy", "LinkedIn Learning"}.intersection({item["provider"] for item in baseline_payload["course_recommendations"]})

    custom = client.post(
        "/api/v1/learning/recommend",
        headers=headers,
        json={
            "cycle_name": "Cloud AI Upskilling Sprint",
            "horizon_months": 6,
            "company_roadmap_skills": ["kubernetes", "mlops", "rag", "security", "system design"],
            "realtime": True,
            "employees": [
                {
                    "employee_id": "learn-gap",
                    "employee_name": "Cloud Gap Engineer",
                    "role": "Backend Engineer",
                    "department": "Engineering",
                    "team": "Platform",
                    "current_skills": ["python", "fastapi", "postgresql"],
                    "target_role": "Senior Platform Engineer",
                    "career_goal": "Own cloud-native AI deployment systems",
                    "project_requirements": ["kubernetes", "mlops", "security"],
                    "future_project_skills": ["kubernetes", "mlops", "rag"],
                    "interests": ["cloud", "ai infrastructure"],
                    "certifications": [],
                    "completed_courses": ["Advanced Python"],
                    "performance_score": 90,
                    "productivity_score": 88,
                    "assessment_score": 79,
                    "promotion_readiness": 0.7,
                    "learning_velocity": 0.82,
                    "learning_hours_last_90d": 30,
                    "courses_completed_last_year": 4,
                    "manager_priority": 0.92,
                    "market_alignment": 0.9,
                    "attrition_risk": 0.36,
                    "burnout_risk": 0.28,
                },
                {
                    "employee_id": "learn-covered",
                    "employee_name": "Covered Engineer",
                    "role": "Cloud Engineer",
                    "department": "Engineering",
                    "team": "Platform",
                    "current_skills": ["python", "kubernetes", "mlops", "security", "system design", "rag"],
                    "target_role": "Staff Cloud Engineer",
                    "career_goal": "Deepen architecture leadership",
                    "project_requirements": ["kubernetes", "mlops"],
                    "future_project_skills": ["kubernetes", "mlops"],
                    "interests": ["architecture"],
                    "certifications": ["CKA", "AWS Solutions Architect"],
                    "completed_courses": ["Kubernetes", "MLOps"],
                    "performance_score": 88,
                    "productivity_score": 86,
                    "assessment_score": 86,
                    "promotion_readiness": 0.62,
                    "learning_velocity": 0.76,
                    "learning_hours_last_90d": 20,
                    "courses_completed_last_year": 5,
                    "manager_priority": 0.5,
                    "market_alignment": 0.54,
                    "attrition_risk": 0.12,
                    "burnout_risk": 0.2,
                },
            ],
        },
    )
    assert custom.status_code == 200
    payload = custom.json()
    gaps = {item["employee_id"]: item for item in payload["skill_gaps"]}
    assert gaps["learn-gap"]["gap_score"] > gaps["learn-covered"]["gap_score"] + 10
    assert {"kubernetes", "mlops"}.intersection(set(gaps["learn-gap"]["missing_skills"]))
    gap_courses = [item for item in payload["course_recommendations"] if item["employee_id"] == "learn-gap"]
    covered_courses = [item for item in payload["course_recommendations"] if item["employee_id"] == "learn-covered"]
    assert gap_courses
    assert len(gap_courses) >= len(covered_courses)
    assert any(item["target_skill"] in {"kubernetes", "mlops", "rag", "security"} for item in gap_courses)
    assert all(0 <= item["completion_probability"] <= 100 for item in gap_courses)
    assert any(item["employee_id"] == "learn-gap" for item in payload["career_roadmaps"])
    assert any(item["target_skill"] in {"kubernetes", "mlops", "rag"} for item in payload["progress_forecasts"])
    assert any(item["skill"] in {"kubernetes", "mlops", "rag", "security"} for item in payload["team_upskilling_heatmap"])
    assert any(item["shortage_risk"] >= 40 for item in payload["future_skill_forecasts"])
    assert payload["summary"]["critical_skill_gaps"] >= 1
    assert "learning_recommendation_history.jsonl" in payload["storage"]

    with client.stream("GET", "/api/v1/learning/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: learning" in first_chunk
        assert "course_recommendations" in first_chunk


def test_communication_quality_analyzer_detects_toxicity_isolation_conflict_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/communication/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["model"] == "PyTorch TextEmotionNet + TF-IDF Communication Risk Ensemble"
    assert baseline_payload["message_risks"]
    assert baseline_payload["team_heatmap"]
    assert baseline_payload["interaction_graph"]
    assert baseline_payload["conflict_forecasts"]
    assert baseline_payload["isolation_risks"]
    assert baseline_payload["recommendations"]
    assert baseline_payload["alerts"]
    assert baseline_payload["executive_insights"]
    assert "communication_quality_history.jsonl" in baseline_payload["storage"]

    custom = client.post(
        "/api/v1/communication/analyze",
        headers=headers,
        json={
            "cycle_name": "Conflict Escalation Review",
            "horizon_days": 45,
            "realtime": True,
            "messages": [
                {
                    "message_id": "toxic-thread",
                    "employee_id": "emp-toxic",
                    "employee_name": "Employee A",
                    "department": "Engineering",
                    "team": "Platform",
                    "channel": "review",
                    "thread_id": "release-risk",
                    "text": "Stop making excuses. This reckless deployment keeps breaking everything and the handoff is unacceptable.",
                    "response_delay_minutes": 240,
                    "expected_response_minutes": 45,
                    "unresolved": True,
                    "recipient_ids": ["emp-calm"],
                },
                {
                    "message_id": "healthy-thread",
                    "employee_id": "emp-calm",
                    "employee_name": "Employee B",
                    "department": "Engineering",
                    "team": "Platform",
                    "channel": "chat",
                    "thread_id": "release-risk",
                    "text": "The rollback plan is clear, QA has ownership, and I can help document the deployment notes.",
                    "response_delay_minutes": 12,
                    "expected_response_minutes": 60,
                    "unresolved": False,
                    "recipient_ids": ["emp-toxic"],
                },
            ],
            "interactions": [
                {
                    "source_id": "emp-toxic",
                    "source_name": "Employee A",
                    "target_id": "emp-calm",
                    "target_name": "Employee B",
                    "department": "Engineering",
                    "team": "Platform",
                    "messages_sent": 38,
                    "messages_received": 11,
                    "average_response_minutes": 260,
                    "baseline_response_minutes": 45,
                    "collaboration_frequency": 0.24,
                    "sentiment_alignment": -0.68,
                    "conflict_incidents": 8,
                    "unanswered_threads": 9,
                    "participation_delta": -0.62,
                },
                {
                    "source_id": "emp-isolated",
                    "source_name": "Isolated Engineer",
                    "target_id": "emp-manager",
                    "target_name": "Engineering Manager",
                    "department": "Engineering",
                    "team": "Platform",
                    "messages_sent": 2,
                    "messages_received": 17,
                    "average_response_minutes": 540,
                    "baseline_response_minutes": 70,
                    "collaboration_frequency": 0.08,
                    "sentiment_alignment": -0.4,
                    "conflict_incidents": 1,
                    "unanswered_threads": 12,
                    "participation_delta": -0.74,
                },
            ],
        },
    )
    assert custom.status_code == 200
    payload = custom.json()
    risks = {item["message_id"]: item for item in payload["message_risks"]}
    assert risks["toxic-thread"]["toxicity_score"] > risks["healthy-thread"]["toxicity_score"]
    assert risks["toxic-thread"]["aggression_score"] > risks["healthy-thread"]["aggression_score"]
    assert risks["toxic-thread"]["conflict_escalation_score"] > risks["healthy-thread"]["conflict_escalation_score"]
    assert risks["toxic-thread"]["communication_quality_score"] < risks["healthy-thread"]["communication_quality_score"]
    assert any(item["employee_id"] == "emp-isolated" and item["isolation_risk"] >= 55 for item in payload["isolation_risks"])
    engineering = next(item for item in payload["team_heatmap"] if item["department"] == "Engineering")
    assert engineering["conflict_probability"] >= 55
    assert engineering["isolation_risk"] >= 40
    recommendation_categories = {item["category"] for item in payload["recommendations"]}
    assert {"toxicity", "collaboration", "isolation", "conflict"}.intersection(recommendation_categories)
    assert payload["summary"]["high_toxicity_alerts"] >= 1
    assert payload["summary"]["isolation_risks"] >= 1

    with client.stream("GET", "/api/v1/communication/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: communication_quality" in first_chunk
        assert "message_risks" in first_chunk


def test_innovation_scoring_system_mines_ideas_ranks_employees_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/innovation/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["model"] == "PyTorch TextEmotionNet + TF-IDF Innovation Impact Ensemble"
    assert baseline_payload["idea_insights"]
    assert baseline_payload["employee_scores"]
    assert baseline_payload["hidden_talent"]
    assert baseline_payload["leadership_predictions"]
    assert baseline_payload["problem_solving_insights"]
    assert baseline_payload["growth_forecasts"]
    assert baseline_payload["talent_risks"]
    assert baseline_payload["promotion_recommendations"]
    assert baseline_payload["team_heatmap"]
    assert baseline_payload["impact_forecasts"]
    assert baseline_payload["trend_points"]
    assert baseline_payload["recommendations"]
    assert baseline_payload["alerts"]
    assert baseline_payload["executive_insights"]
    assert baseline_payload["digital_twin_updates"]
    assert baseline_payload["marketplace_updates"]
    assert "innovation_scoring_history.jsonl" in baseline_payload["storage"]
    assert {
        "innovation_analytics_engine",
        "leadership_potential_engine",
        "creativity_intelligence_engine",
        "problem_solving_intelligence_engine",
        "talent_discovery_engine",
        "employee_growth_engine",
        "future_leader_prediction_engine",
        "innovation_ai_assistant",
        "talent_marketplace",
        "employee_digital_twin",
    }.issubset(set(baseline_payload["source_systems"]))

    custom = client.post(
        "/api/v1/innovation/score",
        headers=headers,
        json={
            "cycle_name": "AI Innovation Sprint",
            "horizon_days": 120,
            "realtime": True,
            "employee_profiles": [
                {
                    "employee_id": "emp-breakthrough",
                    "employee_name": "Employee A",
                    "department": "Engineering",
                    "team": "AI Platform",
                    "role": "Senior Engineer",
                    "performance_history": [0.58, 0.67, 0.79, 0.91],
                    "learning_activity": 0.94,
                    "project_contributions": 8,
                    "peer_recognition": 6,
                    "knowledge_sharing": 9,
                    "mentorship_participation": 5,
                    "ownership_score": 0.91,
                    "communication_effectiveness": 0.86,
                    "decision_quality": 0.9,
                    "incident_resolution_count": 5,
                    "root_cause_analyses": 4,
                    "strategic_thinking_score": 0.9,
                    "engagement_score": 0.88,
                    "burnout_risk": 0.22,
                    "retention_risk": 0.24,
                    "manager_visibility": 0.22,
                    "promotion_readiness": 0.82,
                },
                {
                    "employee_id": "emp-weak",
                    "employee_name": "Employee B",
                    "department": "Operations",
                    "team": "Planning",
                    "role": "Coordinator",
                    "performance_history": [0.52, 0.51, 0.5, 0.49],
                    "learning_activity": 0.22,
                    "project_contributions": 1,
                    "peer_recognition": 4,
                    "knowledge_sharing": 0,
                    "mentorship_participation": 0,
                    "ownership_score": 0.28,
                    "communication_effectiveness": 0.48,
                    "decision_quality": 0.34,
                    "incident_resolution_count": 0,
                    "root_cause_analyses": 0,
                    "strategic_thinking_score": 0.24,
                    "engagement_score": 0.46,
                    "burnout_risk": 0.16,
                    "retention_risk": 0.18,
                    "manager_visibility": 0.62,
                    "promotion_readiness": 0.18,
                },
            ],
            "ideas": [
                {
                    "idea_id": "breakthrough-idea",
                    "employee_id": "emp-breakthrough",
                    "employee_name": "Employee A",
                    "department": "Engineering",
                    "team": "AI Platform",
                    "channel": "proposal",
                    "text": "Prototype an autonomous vector retrieval and deployment optimizer that predicts risky diffs, reduces latency, creates self-healing rollback plans, and saves release engineering hours.",
                    "adoption_stage": "piloting",
                    "reactions_count": 48,
                    "cross_team_votes": 21,
                    "collaboration_mentions": 15,
                    "implementation_progress": 0.68,
                    "estimated_hours_saved": 740,
                    "estimated_cost_saving": 260000,
                    "estimated_revenue_impact": 420000,
                    "feasibility_signal": 0.86,
                    "strategic_alignment": 0.94,
                    "novelty_claim": 0.92,
                },
                {
                    "idea_id": "weak-idea",
                    "employee_id": "emp-weak",
                    "employee_name": "Employee B",
                    "department": "Operations",
                    "team": "Planning",
                    "channel": "chat",
                    "text": "Maybe we should have another meeting later and talk about improving the process when people have time.",
                    "adoption_stage": "submitted",
                    "reactions_count": 1,
                    "cross_team_votes": 0,
                    "collaboration_mentions": 0,
                    "implementation_progress": 0.02,
                    "estimated_hours_saved": 0,
                    "estimated_cost_saving": 0,
                    "estimated_revenue_impact": 0,
                    "feasibility_signal": 0.28,
                    "strategic_alignment": 0.2,
                    "novelty_claim": 0.12,
                },
            ],
        },
    )
    assert custom.status_code == 200
    payload = custom.json()
    insights = {item["idea_id"]: item for item in payload["idea_insights"]}
    assert insights["breakthrough-idea"]["originality_score"] > insights["weak-idea"]["originality_score"]
    assert insights["breakthrough-idea"]["impact_score"] > insights["weak-idea"]["impact_score"]
    assert insights["breakthrough-idea"]["adoption_probability"] > insights["weak-idea"]["adoption_probability"]
    scores = {item["employee_id"]: item for item in payload["employee_scores"]}
    assert scores["emp-breakthrough"]["innovation_score"] > scores["emp-weak"]["innovation_score"]
    assert scores["emp-breakthrough"]["creativity_rank"] == 1
    hidden = {item["employee_id"]: item for item in payload["hidden_talent"]}
    leaders = {item["employee_id"]: item for item in payload["leadership_predictions"]}
    solvers = {item["employee_id"]: item for item in payload["problem_solving_insights"]}
    growth = {item["employee_id"]: item for item in payload["growth_forecasts"]}
    risks = {item["employee_id"]: item for item in payload["talent_risks"]}
    assert hidden["emp-breakthrough"]["hidden_talent_score"] > hidden["emp-weak"]["hidden_talent_score"]
    assert hidden["emp-breakthrough"]["under_recognized_gap"] > hidden["emp-weak"]["under_recognized_gap"]
    assert leaders["emp-breakthrough"]["leadership_potential"] > leaders["emp-weak"]["leadership_potential"]
    assert leaders["emp-breakthrough"]["future_architect_probability"] > leaders["emp-weak"]["future_architect_probability"]
    assert solvers["emp-breakthrough"]["problem_solving_score"] > solvers["emp-weak"]["problem_solving_score"]
    assert growth["emp-breakthrough"]["innovation_growth_3_years"] > growth["emp-weak"]["innovation_growth_3_years"]
    assert risks["emp-breakthrough"]["flight_risk"] >= risks["emp-weak"]["flight_risk"]
    assert payload["promotion_recommendations"][0]["employee_id"] == "emp-breakthrough"
    assert payload["impact_forecasts"][0]["idea_id"] == "breakthrough-idea"
    assert payload["impact_forecasts"][0]["predicted_business_impact"] >= 70
    assert payload["summary"]["high_impact_ideas"] >= 1
    assert payload["summary"]["employees_ranked"] == 2
    assert payload["summary"]["hidden_talent_count"] >= 1
    assert payload["summary"]["future_leaders_count"] >= 1
    assert payload["summary"]["promotion_candidates"] >= 1
    assert any(item["category"] in {"idea_sponsorship", "prototype", "recognition"} for item in payload["recommendations"])

    assistant = client.post(
        "/api/v1/innovation/assistant",
        headers=headers,
        json={"question": "Who are our future leaders?"},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["intent"] == "leaders"
    assert assistant_payload["cited_employees"]
    assert assistant_payload["recommended_actions"]

    with client.stream("GET", "/api/v1/innovation/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: innovation_scoring" in first_chunk
        assert "idea_insights" in first_chunk


def test_hidden_leader_detection_finds_graph_backed_future_leaders_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/talent/hidden-leaders/default", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "NEXUSMIND Hidden Leader Detection & Talent Intelligence System"
    assert payload["final_verdict"] == "HIDDEN LEADER DETECTION SYSTEM COMPLETE"
    assert payload["summary"]["production_readiness_score"] >= 95
    assert payload["summary"]["innovation_score"] >= 95
    assert payload["summary"]["judge_wow_factor_score"] >= 90
    assert payload["leadership_scorecards"]
    assert payload["hidden_leader_candidates"]
    assert payload["influence_analysis"]
    assert payload["problem_solving_intelligence"]
    assert payload["innovation_leaders"]
    assert payload["knowledge_leaders"]
    assert payload["leadership_forecast"]
    assert payload["promotion_recommendations"]
    assert payload["digital_twin_sync"]
    assert payload["agent_council"]
    assert payload["data_quality"]["quality_score"] >= 90
    assert payload["graph_integration"]["influence_relationships_analyzed"] > 0
    assert payload["graph_integration"]["knowledge_relationships_analyzed"] > 0
    assert "hidden_leader_detection_history.jsonl" in payload["storage"]
    assert {
        "leadership_intelligence_engine",
        "talent_discovery_engine",
        "influence_analysis_engine",
        "communication_intelligence_engine",
        "innovation_detection_engine",
        "mentorship_analysis_engine",
        "knowledge_leadership_engine",
        "leadership_forecast_engine",
        "organizational_brain",
        "employee_digital_twin",
        "multi_agent_workforce",
        "hr_agent",
        "knowledge_agent",
        "executive_agent",
    }.issubset(set(payload["source_systems"]))
    top_candidate = payload["hidden_leader_candidates"][0]
    assert top_candidate["hidden_leader_score"] >= 60
    assert top_candidate["promotion_recommendation"]
    assert top_candidate["evidence"]
    assert {item["twin"] for item in payload["digital_twin_sync"]} == {"employee", "team", "department", "company", "executive_dashboard"}
    assert {item["agent"] for item in payload["agent_council"]}.issuperset({"HR Agent", "Knowledge Agent", "Executive Agent"})

    custom = client.post(
        "/api/v1/talent/hidden-leaders/analyze",
        headers=headers,
        json={
            "cycle_name": "Executive Leadership Bench Review",
            "horizon_months": 24,
            "min_candidate_score": 65,
            "include_organizational_graph": True,
            "include_talent_marketplace": True,
            "include_innovation_engine": True,
        },
    )
    assert custom.status_code == 200
    custom_payload = custom.json()
    assert custom_payload["cycle_name"] == "Executive Leadership Bench Review"
    assert custom_payload["hidden_leader_candidates"]
    assert all(item["hidden_leader_score"] >= 65 for item in custom_payload["hidden_leader_candidates"])
    assert any(item["forecast_month"] == 24 for item in custom_payload["leadership_forecast"])

    assistant = client.post(
        "/api/v1/talent/hidden-leaders/assistant",
        headers=headers,
        json={"question": "Who are our future leaders?", "horizon_months": 24},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["intent"] == "future_leaders"
    assert assistant_payload["cited_employees"]
    assert assistant_payload["recommended_actions"]

    influence_assistant = client.post(
        "/api/v1/talent/hidden-leaders/assistant",
        headers=headers,
        json={"question": "Who is influencing teams the most?", "horizon_months": 24},
    )
    assert influence_assistant.status_code == 200
    assert influence_assistant.json()["intent"] == "influence"

    with client.stream("GET", "/api/v1/talent/hidden-leaders/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: hidden_leader_detection" in first_chunk
        assert "HIDDEN LEADER DETECTION SYSTEM COMPLETE" in first_chunk

    readiness = client.get("/api/v1/system/readiness")
    assert readiness.status_code == 200
    services = readiness.json()["services"]
    assert services["hidden_leader_detection_system"] is True
    assert services["talent_intelligence_system"] is True
    assert services["ai_that_finds_hidden_leaders"] is True


def test_realtime_company_health_dashboard_scores_risks_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/company-health/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["model"] == "RandomForest Company Health + GradientBoosting KPI Forecast Engine"
    assert baseline_payload["executive_kpis"]
    assert baseline_payload["team_scores"]
    assert baseline_payload["heatmap"]
    assert baseline_payload["productivity_trends"]
    assert baseline_payload["risk_forecasts"]
    assert baseline_payload["project_scorecards"]
    assert baseline_payload["recommendations"]
    assert baseline_payload["alerts"]
    assert baseline_payload["executive_insights"]
    assert "company_health_history.jsonl" in baseline_payload["storage"]
    assert any(item["label"] == "Company Health Score" for item in baseline_payload["executive_kpis"])

    custom = client.post(
        "/api/v1/company-health/analyze",
        headers=headers,
        json={
            "cycle_name": "Board Health Stress Test",
            "horizon_days": 45,
            "realtime": True,
            "teams": [
                {
                    "team_id": "stable-team",
                    "department": "Product",
                    "team_name": "AI Product Studio",
                    "headcount": 18,
                    "employee_happiness_score": 88,
                    "productivity_score": 90,
                    "burnout_risk": 16,
                    "attrition_risk": 14,
                    "project_health": 91,
                    "collaboration_quality": 92,
                    "delivery_stability": 90,
                    "resource_utilization": 80,
                    "innovation_score": 86,
                    "security_risk": 8,
                    "communication_health": 91,
                    "meeting_efficiency": 86,
                    "workforce_engagement": 89,
                    "open_project_risks": 1,
                    "active_incidents": 0,
                },
                {
                    "team_id": "crisis-team",
                    "department": "Operations",
                    "team_name": "Incident Response",
                    "headcount": 12,
                    "employee_happiness_score": 37,
                    "productivity_score": 42,
                    "burnout_risk": 91,
                    "attrition_risk": 84,
                    "project_health": 36,
                    "collaboration_quality": 44,
                    "delivery_stability": 32,
                    "resource_utilization": 122,
                    "innovation_score": 48,
                    "security_risk": 68,
                    "communication_health": 39,
                    "meeting_efficiency": 31,
                    "workforce_engagement": 35,
                    "open_project_risks": 23,
                    "active_incidents": 9,
                },
            ],
        },
    )
    assert custom.status_code == 200
    payload = custom.json()
    teams = {item["team_id"]: item for item in payload["team_scores"]}
    assert teams["crisis-team"]["health_score"] < teams["stable-team"]["health_score"]
    assert teams["crisis-team"]["risk_score"] > teams["stable-team"]["risk_score"]
    assert teams["crisis-team"]["priority"] in {"high", "critical"}
    assert payload["summary"]["high_risk_teams"] >= 1
    assert payload["summary"]["operational_risk"] > 35
    assert any(alert["category"] in {"team_health", "burnout", "company_health"} for alert in payload["alerts"])
    assert any(item["category"] in {"burnout", "operational", "project"} for item in payload["recommendations"])
    assert payload["risk_forecasts"][-1]["operational_risk"] >= payload["risk_forecasts"][0]["operational_risk"]
    assert any(point["metric"] == "Employee happiness heatmaps" for point in payload["heatmap"])

    with client.stream("GET", "/api/v1/company-health/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: company_health" in first_chunk
        assert "team_scores" in first_chunk


def test_ai_decision_assistant_recommends_best_team_forecasts_risk_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/decisions/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["model"] == "RandomForest Decision Router + GradientBoosting Timeline Risk Forecaster"
    assert baseline_payload["rankings"]
    assert baseline_payload["risk_heatmap"]
    assert baseline_payload["timeline_forecast"]
    assert baseline_payload["capability_forecast"]
    assert baseline_payload["recommendations"]
    assert baseline_payload["alerts"]
    assert baseline_payload["executive_insights"]
    assert "decision_assistant_history.jsonl" in baseline_payload["storage"]
    assert {"resource_allocation", "project_failure_prediction", "team_builder_graph"}.issubset(set(baseline_payload["source_systems"]))
    assert baseline_payload["summary"]["recommended_team"] == baseline_payload["rankings"][0]["team_name"]

    custom = client.post(
        "/api/v1/decisions/recommend",
        headers=headers,
        json={
            "question": "Which team should handle the Project Atlas Kubernetes security migration?",
            "horizon_days": 42,
            "realtime": True,
            "project": {
                "project_id": "project-atlas-test",
                "project_name": "Project Atlas Kubernetes Security Migration",
                "description": "Move AI APIs to a secure Kubernetes runtime with observability and MLOps release controls.",
                "required_skills": ["kubernetes", "security", "observability", "fastapi", "mlops"],
                "complexity": 0.82,
                "deadline_days": 22,
                "budget": 720000,
                "revenue_impact": 2800000,
                "dependency_count": 8,
                "security_sensitivity": 0.86,
                "innovation_requirement": 0.66,
                "scope_volatility": 0.38,
                "executive_visibility": 0.91,
            },
            "teams": [
                {
                    "team_id": "fit-team",
                    "team_name": "Platform AI Delivery",
                    "department": "Engineering",
                    "skills": ["kubernetes", "security", "observability", "fastapi", "mlops", "python", "realtime streaming"],
                    "member_count": 9,
                    "historical_success_rate": 0.92,
                    "productivity_score": 0.91,
                    "current_workload": 0.66,
                    "capacity_available": 0.46,
                    "sprint_velocity": 0.9,
                    "communication_quality": 0.9,
                    "collaboration_score": 0.88,
                    "burnout_risk": 0.2,
                    "attrition_risk": 0.12,
                    "delivery_consistency": 0.92,
                    "innovation_score": 0.82,
                    "hourly_cost": 118,
                    "active_incidents": 1,
                },
                {
                    "team_id": "overloaded-team",
                    "team_name": "Security Incident Response",
                    "department": "Security",
                    "skills": ["kubernetes", "security", "observability", "fastapi", "mlops"],
                    "member_count": 7,
                    "historical_success_rate": 0.78,
                    "productivity_score": 0.72,
                    "current_workload": 1.22,
                    "capacity_available": 0.08,
                    "sprint_velocity": 0.64,
                    "communication_quality": 0.69,
                    "collaboration_score": 0.68,
                    "burnout_risk": 0.88,
                    "attrition_risk": 0.46,
                    "delivery_consistency": 0.62,
                    "innovation_score": 0.58,
                    "hourly_cost": 136,
                    "active_incidents": 7,
                },
                {
                    "team_id": "weak-team",
                    "team_name": "Design Systems",
                    "department": "Product",
                    "skills": ["dashboard", "ux research", "accessibility"],
                    "member_count": 6,
                    "historical_success_rate": 0.72,
                    "productivity_score": 0.78,
                    "current_workload": 0.62,
                    "capacity_available": 0.42,
                    "sprint_velocity": 0.68,
                    "communication_quality": 0.88,
                    "collaboration_score": 0.86,
                    "burnout_risk": 0.18,
                    "attrition_risk": 0.1,
                    "delivery_consistency": 0.74,
                    "innovation_score": 0.76,
                    "hourly_cost": 86,
                    "active_incidents": 0,
                },
            ],
        },
    )
    assert custom.status_code == 200
    payload = custom.json()
    rankings = {item["team_id"]: item for item in payload["rankings"]}
    assert payload["rankings"][0]["team_id"] == "fit-team"
    assert rankings["fit-team"]["suitability_score"] > rankings["overloaded-team"]["suitability_score"]
    assert rankings["fit-team"]["suitability_score"] > rankings["weak-team"]["suitability_score"]
    assert rankings["fit-team"]["risk_score"] < rankings["overloaded-team"]["risk_score"]
    assert rankings["fit-team"]["estimated_completion_days"] < rankings["weak-team"]["estimated_completion_days"]
    assert payload["summary"]["recommended_team_id"] == "fit-team"
    assert payload["summary"]["success_probability"] >= rankings["overloaded-team"]["delivery_success_probability"]
    assert any(item["category"] in {"routing", "timeline", "burnout", "skills"} for item in payload["recommendations"])
    assert any(point["metric"] == "Risk-analysis heatmaps" for point in payload["risk_heatmap"])
    assert payload["timeline_forecast"][-1]["completion_probability"] >= payload["timeline_forecast"][0]["completion_probability"]

    with client.stream("GET", "/api/v1/decisions/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: decision_assistant" in first_chunk
        assert "rankings" in first_chunk


def test_predictive_client_satisfaction_ai_forecasts_churn_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/clients/satisfaction/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["model"] == "RandomForest Client Health + GradientBoosting Churn Risk Forecaster"
    assert baseline_payload["predictions"]
    assert baseline_payload["heatmap"]
    assert baseline_payload["communication_sentiment"]
    assert baseline_payload["delivery_risks"]
    assert baseline_payload["payment_risks"]
    assert baseline_payload["project_risks"]
    assert baseline_payload["engagement_analytics"]
    assert baseline_payload["opportunity_pipeline"]
    assert baseline_payload["recommendations"]
    assert baseline_payload["alerts"]
    assert baseline_payload["executive_insights"]
    assert "client_satisfaction_history.jsonl" in baseline_payload["storage"]
    assert {
        "client_health_engine",
        "churn_prediction_engine",
        "payment_risk_engine",
        "project_risk_engine",
        "communication_intelligence_engine",
        "ai_client_assistant",
        "opportunity_detection_engine",
        "communication_quality_analyzer",
        "project_failure_prediction",
        "gradient_boosting_churn_forecaster",
    }.issubset(set(baseline_payload["source_systems"]))

    custom = client.post(
        "/api/v1/clients/satisfaction/predict",
        headers=headers,
        json={
            "cycle_name": "Strategic Client Satisfaction Test",
            "horizon_days": 60,
            "realtime": True,
            "clients": [
                {
                    "client_id": "client-stable",
                    "client_name": "Stable Bank",
                    "industry": "Financial Services",
                    "account_tier": "global",
                    "project_name": "Risk Data Platform",
                    "contract_value": 6200000,
                    "renewal_days": 160,
                    "delivery_delay_days": 1,
                    "missed_milestones": 0,
                    "sla_breach_count": 0,
                    "bug_frequency": 0.08,
                    "production_incidents": 0,
                    "qa_pass_rate": 0.94,
                    "rework_ratio": 0.06,
                    "issue_resolution_hours": 12,
                    "escalation_count": 0,
                    "communication_sentiment": 0.52,
                    "interaction_frequency": 0.86,
                    "feedback_score": 0.9,
                    "nps_delta": 10,
                    "delivery_consistency": 0.91,
                    "relationship_tenure_months": 48,
                    "executive_sponsor_engagement": 0.88,
                    "open_critical_issues": 0,
                    "average_payment_delay_days": 2,
                    "overdue_invoice_amount": 0,
                    "invoice_dispute_count": 0,
                    "meeting_attendance_rate": 0.92,
                    "email_response_hours": 8,
                    "platform_usage_score": 0.9,
                    "feature_adoption_score": 0.86,
                    "support_ticket_count": 2,
                    "upsell_signal_score": 0.86,
                    "expansion_budget_signal": 0.78,
                    "meeting_transcripts": ["The release is stable, communication is clear, and our team is confident in the migration plan."],
                    "email_threads": ["Thanks for resolving questions quickly and keeping the roadmap predictable."],
                },
                {
                    "client_id": "client-crisis",
                    "client_name": "Crisis Retail",
                    "industry": "Retail",
                    "account_tier": "enterprise",
                    "project_name": "Commerce Replatform",
                    "contract_value": 3600000,
                    "renewal_days": 45,
                    "delivery_delay_days": 21,
                    "missed_milestones": 6,
                    "sla_breach_count": 5,
                    "bug_frequency": 0.58,
                    "production_incidents": 5,
                    "qa_pass_rate": 0.55,
                    "rework_ratio": 0.48,
                    "issue_resolution_hours": 144,
                    "escalation_count": 6,
                    "communication_sentiment": -0.44,
                    "interaction_frequency": 0.32,
                    "feedback_score": 0.34,
                    "nps_delta": -35,
                    "delivery_consistency": 0.42,
                    "relationship_tenure_months": 16,
                    "executive_sponsor_engagement": 0.28,
                    "open_critical_issues": 5,
                    "average_payment_delay_days": 32,
                    "overdue_invoice_amount": 540000,
                    "invoice_dispute_count": 4,
                    "meeting_attendance_rate": 0.38,
                    "email_response_hours": 108,
                    "platform_usage_score": 0.36,
                    "feature_adoption_score": 0.28,
                    "support_ticket_count": 32,
                    "upsell_signal_score": 0.12,
                    "expansion_budget_signal": 0.08,
                    "stakeholder_change_count": 3,
                    "meeting_transcripts": [
                        "The client is frustrated because the deployment was delayed again and the checkout defect remains unresolved.",
                        "This requires executive escalation. Trust is dropping and the same SLA breach keeps repeating.",
                    ],
                    "email_threads": ["We are disappointed with the missed milestone and need an immediate recovery plan."],
                },
            ],
        },
    )
    assert custom.status_code == 200
    payload = custom.json()
    predictions = {item["client_id"]: item for item in payload["predictions"]}
    assert predictions["client-crisis"]["client_health_score"] < predictions["client-stable"]["client_health_score"]
    assert predictions["client-crisis"]["churn_risk"] > predictions["client-stable"]["churn_risk"]
    assert predictions["client-crisis"]["escalation_probability"] > predictions["client-stable"]["escalation_probability"]
    assert predictions["client-crisis"]["communication_health"] < predictions["client-stable"]["communication_health"]
    assert predictions["client-crisis"]["delivery_health"] < predictions["client-stable"]["delivery_health"]
    assert predictions["client-crisis"]["payment_delay_risk"] > predictions["client-stable"]["payment_delay_risk"]
    assert predictions["client-crisis"]["project_failure_risk"] > predictions["client-stable"]["project_failure_risk"]
    assert predictions["client-crisis"]["engagement_score"] < predictions["client-stable"]["engagement_score"]
    assert predictions["client-stable"]["upsell_opportunity_score"] > predictions["client-crisis"]["upsell_opportunity_score"]
    assert payload["summary"]["highest_risk_client"] == "Crisis Retail"
    assert payload["summary"]["best_upsell_client"] == "Stable Bank"
    assert payload["summary"]["payment_risk_accounts"] >= 1
    assert payload["summary"]["project_risk_accounts"] >= 1
    assert payload["summary"]["opportunity_revenue"] > 0
    assert payload["summary"]["revenue_at_risk"] > predictions["client-stable"]["revenue_at_risk"]
    assert any(item["client_name"] == "Crisis Retail" and item["metric"] == "Churn-risk visualizations" for item in payload["heatmap"])
    assert any(item["client_name"] == "Crisis Retail" and item["negativity_risk"] > 50 for item in payload["communication_sentiment"])
    assert any(item["client_name"] == "Crisis Retail" and item["payment_delay_risk"] > 50 for item in payload["payment_risks"])
    assert any(item["client_name"] == "Crisis Retail" and item["project_failure_risk"] > 50 for item in payload["project_risks"])
    assert any(item["client_name"] == "Stable Bank" and item["probability"] > 50 for item in payload["opportunity_pipeline"])
    assert any(item["category"] in {"executive", "communication", "delivery", "quality", "payment", "opportunity"} for item in payload["recommendations"])
    assert any("Crisis Retail" in alert["title"] for alert in payload["alerts"])
    assert payload["predictions"][0]["forecast"][-1]["churn_risk"] >= payload["predictions"][0]["forecast"][0]["churn_risk"]

    alias = client.get("/api/v1/clients/relationship/default", headers=headers)
    assert alias.status_code == 200
    assert alias.json()["opportunity_pipeline"]

    payment_assistant = client.post(
        "/api/v1/clients/relationship/assistant",
        headers=headers,
        json={"question": "Which clients may pay late?"},
    )
    assert payment_assistant.status_code == 200
    assistant_payload = payment_assistant.json()
    assert assistant_payload["intent"] == "payment"
    assert assistant_payload["cited_clients"]
    assert "payment" in assistant_payload["answer"].lower()

    with client.stream("GET", "/api/v1/clients/satisfaction/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: client_satisfaction" in first_chunk
        assert "predictions" in first_chunk
  
  
def test_ai_knowledge_loss_prevention_builds_dynamic_graph_docs_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/knowledge/loss/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["model"] == "TF-IDF Knowledge Graph + RandomForest Knowledge Loss Forecaster"
    assert baseline_payload["expertise_profiles"]
    assert baseline_payload["graph_nodes"]
    assert baseline_payload["graph_edges"]
    assert baseline_payload["generated_documents"]
    assert baseline_payload["memory_heatmap"]
    assert baseline_payload["onboarding_roadmaps"]
    assert baseline_payload["recommendations"]
    assert baseline_payload["alerts"]
    assert "knowledge_loss_history.jsonl" in baseline_payload["storage"]
    assert "knowledge_graph_neo4j_export.json" in baseline_payload["graph_store"]
    assert {"tfidf_expertise_extraction", "networkx_knowledge_graph", "random_forest_knowledge_loss_forecaster"}.issubset(set(baseline_payload["source_systems"]))

    custom = client.post(
        "/api/v1/knowledge/loss/analyze",
        headers=headers,
        json={
            "cycle_name": "Strategic Knowledge Loss Test",
            "horizon_days": 75,
            "target_role": "Platform Engineer",
            "realtime": True,
            "sources": [
                {
                    "source_id": "critical-k8s",
                    "title": "Kubernetes Disaster Recovery Review",
                    "source_type": "meeting",
                    "employee_id": "emp-critical",
                    "employee_name": "Critical Engineer",
                    "department": "Platform",
                    "team": "Infrastructure Reliability",
                    "role": "Senior DevOps Engineer",
                    "content": "Critical Engineer owns Kubernetes cluster rollback, Helm release recovery, ingress failover, Redis stream replay, deployment pipeline recovery, and production incident triage.",
                    "systems": ["Kubernetes Platform", "Deployment Pipeline"],
                    "skills": ["kubernetes", "deployment", "incident response", "redis"],
                    "contribution_count": 28,
                    "incident_resolutions": 10,
                    "docs_authored": 0,
                    "commit_count": 95,
                    "meeting_mentions": 14,
                    "attrition_risk": 0.92,
                    "seniority": 0.96,
                    "documentation_quality": 0.18,
                    "last_updated_days": 86,
                    "business_criticality": 0.99,
                    "redundancy_count": 0,
                    "handoff_readiness": 0.12,
                    "onboarding_relevance": 0.9,
                },
                {
                    "source_id": "stable-docs",
                    "title": "Analytics Onboarding Wiki",
                    "source_type": "documentation",
                    "employee_id": "emp-stable",
                    "employee_name": "Stable Documenter",
                    "department": "Analytics",
                    "team": "Data Products",
                    "role": "Analytics Lead",
                    "content": "Stable Documenter maintains a complete analytics onboarding wiki, SQL dashboard guide, rollback checklist, and cross-trained support process.",
                    "systems": ["Analytics Dashboard"],
                    "skills": ["documentation", "postgresql", "frontend"],
                    "contribution_count": 10,
                    "incident_resolutions": 1,
                    "docs_authored": 8,
                    "commit_count": 22,
                    "meeting_mentions": 2,
                    "attrition_risk": 0.08,
                    "seniority": 0.7,
                    "documentation_quality": 0.94,
                    "last_updated_days": 3,
                    "business_criticality": 0.55,
                    "redundancy_count": 4,
                    "handoff_readiness": 0.88,
                    "onboarding_relevance": 0.82,
                },
            ],
        },
    )
    assert custom.status_code == 200
    payload = custom.json()
    profiles = {item["employee_id"]: item for item in payload["expertise_profiles"]}
    assert profiles["emp-critical"]["knowledge_loss_probability"] > profiles["emp-stable"]["knowledge_loss_probability"]
    assert profiles["emp-critical"]["operational_disruption_risk"] > profiles["emp-stable"]["operational_disruption_risk"]
    assert profiles["emp-critical"]["documentation_coverage"] < profiles["emp-stable"]["documentation_coverage"]
    assert payload["summary"]["top_risk_owner"] == "Critical Engineer"
    assert any("Kubernetes" in document["title"] and "SOP" in document["title"] for document in payload["generated_documents"])
    assert any("kubernetes" in edge["source"].lower() or "kubernetes" in edge["target"].lower() for edge in payload["graph_edges"])
    assert any("Critical Engineer" in recommendation["title"] or "Kubernetes Platform" in recommendation["target_systems"] for recommendation in payload["recommendations"])
    assert any("Critical Engineer" in alert["title"] for alert in payload["alerts"])
    critical_forecast = [point for point in payload["forecasts"] if point["employee_name"] == "Critical Engineer"]
    assert critical_forecast[-1]["knowledge_loss_probability"] >= critical_forecast[0]["knowledge_loss_probability"]

    with client.stream("GET", "/api/v1/knowledge/loss/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: knowledge_loss" in first_chunk
        assert "expertise_profiles" in first_chunk


def test_enterprise_knowledge_company_brain_ingests_searches_answers_graphs_and_streams() -> None:
    headers = auth_headers()
    suffix = uuid4().hex

    baseline = client.get("/api/v1/knowledge/brain/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["summary"]["documents_indexed"] >= 4
    assert baseline_payload["summary"]["chunks_indexed"] >= 4
    assert baseline_payload["summary"]["graph_nodes"] > 0
    assert baseline_payload["summary"]["graph_edges"] > 0
    assert baseline_payload["final_verdict"] == "AI MEMORY SYSTEM COMPLETE"
    assert "qdrant_adapter_with_local_fallback" in baseline_payload["source_systems"]
    assert {
        "document_ingestion_engine",
        "document_processing_engine",
        "semantic_search_engine",
        "rag_answer_synthesizer",
        "expertise_detection_engine",
        "lessons_learned_engine",
        "organizational_memory_timeline_engine",
        "rbac_document_permission_engine",
        "employee_digital_twin",
        "project_digital_twin",
        "company_digital_twin",
        "knowledge_agent_council",
    }.issubset(set(baseline_payload["source_systems"]))
    assert "using_local_dense_embedding_fallback" in baseline_payload["summary"]["qdrant_status"]
    assert "using_json_graph_fallback" in baseline_payload["summary"]["neo4j_status"]
    assert baseline_payload["lessons_learned"]
    assert baseline_payload["organizational_memory_timeline"]
    assert baseline_payload["security_controls"]
    assert baseline_payload["digital_twin_sync"]
    assert baseline_payload["agent_council"]
    assert baseline_payload["status_report"]["knowledge_ingestion_status"] == "ready"
    assert baseline_payload["status_report"]["document_intelligence_status"] == "ready"
    assert baseline_payload["status_report"]["vector_database_status"].startswith("ready")
    assert baseline_payload["status_report"]["knowledge_graph_status"].startswith("ready")
    assert baseline_payload["status_report"]["rag_status"] == "ready"
    assert baseline_payload["status_report"]["expertise_discovery_status"] == "ready"
    assert baseline_payload["status_report"]["security_status"] == "ready"
    assert baseline_payload["status_report"]["digital_twin_integration_status"] == "synced"
    assert baseline_payload["status_report"]["multi_agent_integration_status"] == "ready"
    assert baseline_payload["status_report"]["missing_components"] == []
    assert baseline_payload["status_report"]["production_readiness_score"] >= 95
    assert baseline_payload["status_report"]["innovation_score"] >= 95
    assert baseline_payload["status_report"]["business_value_score"] >= 95
    assert baseline_payload["status_report"]["final_verdict"] == "AI MEMORY SYSTEM COMPLETE"
    assert any(control["control"] == "JWT authentication" and control["status"] == "enforced" for control in baseline_payload["security_controls"])
    assert {"Employee Twin", "Team Twin", "Project Twin", "Company Twin"}.issubset(
        {item["system"] for item in baseline_payload["digital_twin_sync"]}
    )
    assert {"Knowledge Agent", "HR Agent", "Project Agent", "Executive Agent"}.issubset(
        {item["agent"] for item in baseline_payload["agent_council"]}
    )
    for storage_path in baseline_payload["storage"].values():
        assert Path(storage_path).parent.exists()

    ingest = client.post(
        "/api/v1/knowledge/brain/ingest",
        headers=headers,
        json={
            "source_system": "pytest_fixtures",
            "documents": [
                {
                    "document_id": f"fixture-kubernetes-{suffix}",
                    "title": "Fixture Kubernetes Runbook",
                    "source_type": "text",
                    "file_name": "fixture-kubernetes-runbook.txt",
                    "content": f"Nina solved the Zephyr Kubernetes outage marker {suffix} with node recovery, Helm rollback validation, ingress failover, and a documented disaster recovery SOP.",
                    "metadata": {
                        "employee_id": f"emp-nina-{suffix}",
                        "employee_name": "Nina",
                        "department": "Platform",
                        "team": "Reliability",
                        "systems": ["Kubernetes Platform"],
                        "skills": ["kubernetes", "node recovery", "rollback", "incident response"],
                        "business_criticality": 0.99,
                        "documentation_quality": 0.88,
                    },
                },
                {
                    "document_id": f"fixture-pdf-{suffix}",
                    "title": "Fixture PDF Payment Failure",
                    "source_type": "pdf",
                    "file_name": "payment-failure.pdf",
                    "content": "Priya fixed a payment failure by replaying Kafka events and clearing Redis locks.",
                    "metadata": {"employee_name": "Priya", "skills": ["payment failure"], "systems": ["Payment API"]},
                },
                {
                    "document_id": f"fixture-docx-{suffix}",
                    "title": "Fixture DOCX Database Outage",
                    "source_type": "docx",
                    "file_name": "database-outage.docx",
                    "content": "Sarah restored PostgreSQL after a database outage by promoting a replica and rebuilding indexes.",
                    "metadata": {"employee_name": "Sarah", "skills": ["postgresql", "database recovery"], "systems": ["PostgreSQL Cluster"]},
                },
                {
                    "document_id": f"fixture-pptx-{suffix}",
                    "title": "Fixture PPTX Project Beta",
                    "source_type": "pptx",
                    "file_name": "project-beta.pptx",
                    "content": "Project Beta architecture used FastAPI, Next.js, Qdrant, Neo4j, Kafka, and Spark.",
                    "metadata": {"employee_name": "David", "projects": ["Project Beta"], "skills": ["architecture decision"]},
                },
                {
                    "document_id": f"fixture-xlsx-{suffix}",
                    "title": "Fixture XLSX Expertise Matrix",
                    "source_type": "xlsx",
                    "file_name": "expertise-matrix.xlsx",
                    "content": "Asha owns Qdrant vector search and RAG embedding recovery for Company Brain.",
                    "metadata": {"employee_name": "Asha", "skills": ["qdrant", "vector search", "rag"], "systems": ["Qdrant"]},
                },
            ],
        },
    )
    assert ingest.status_code == 200
    ingest_payload = ingest.json()
    assert len(ingest_payload["ingested_documents"]) == 5
    parsers = {document["parser"] for document in ingest_payload["ingested_documents"]}
    assert "plain_text_parser" in parsers
    assert any("pdf" in parser for parser in parsers)
    assert any("docx" in parser for parser in parsers)
    assert any("pptx" in parser for parser in parsers)
    assert any("xlsx" in parser for parser in parsers)

    upload = client.post(
        "/api/v1/knowledge/brain/upload",
        headers=headers,
        files={"file": ("uploaded-kubernetes-note.txt", b"Uploaded note: Omar documented Kubernetes pod eviction recovery and Helm rollback verification.", "text/plain")},
        data={
            "title": "Uploaded Kubernetes Note",
            "metadata": json.dumps(
                {
                    "employee_id": f"emp-omar-{suffix}",
                    "employee_name": "Omar",
                    "department": "Platform",
                    "team": "Reliability",
                    "skills": ["kubernetes", "rollback"],
                    "systems": ["Kubernetes Platform"],
                }
            ),
        },
    )
    assert upload.status_code == 200
    upload_payload = upload.json()
    assert upload_payload["ingested_documents"][0]["title"] == "Uploaded Kubernetes Note"
    assert upload_payload["ingested_documents"][0]["parser"] == "plain_text_parser"

    search = client.post(
        "/api/v1/knowledge/brain/search",
        headers=headers,
        json={"query": f"Zephyr Kubernetes outage marker {suffix} node recovery strategy", "top_k": 4},
    )
    assert search.status_code == 200
    search_payload = search.json()
    assert search_payload["results"]
    assert search_payload["results"][0]["document_id"] == f"fixture-kubernetes-{suffix}"
    assert search_payload["results"][0]["matched_chunks"]
    assert search_payload["results"][0]["citations"]

    experts = client.get("/api/v1/knowledge/brain/experts?skill=kubernetes", headers=headers)
    assert experts.status_code == 200
    experts_payload = experts.json()
    assert experts_payload["experts"]
    assert experts_payload["experts"][0]["employee_name"] == "Nina"

    answer = client.post(
        "/api/v1/knowledge/brain/ask",
        headers=headers,
        json={"question": "Who knows Kubernetes best?", "top_k": 6, "session_id": f"test-{suffix}"},
    )
    assert answer.status_code == 200
    answer_payload = answer.json()
    assert "Nina" in answer_payload["answer"]
    assert answer_payload["citations"]
    assert answer_payload["retrieved_chunks"]
    assert answer_payload["graph_evidence"]
    assert answer_payload["final_verdict"] == "AI MEMORY SYSTEM COMPLETE"
    assert "enterprise_knowledge_memory.jsonl" in answer_payload["storage"]["memory_history"]
    assert Path(answer_payload["storage"]["memory_history"]).exists()

    database_answer = client.post(
        "/api/v1/knowledge/brain/ask",
        headers=headers,
        json={"question": "What was done during the database outage?", "top_k": 6, "session_id": f"test-{suffix}"},
    )
    assert database_answer.status_code == 200
    assert "warm PostgreSQL replica" in database_answer.json()["answer"]

    graph = client.get("/api/v1/knowledge/brain/graph", headers=headers)
    assert graph.status_code == 200
    graph_payload = graph.json()
    node_types = {node["type"] for node in graph_payload["nodes"]}
    assert {"Employee", "Skill", "Technology", "Project", "Document", "Incident", "Solution"}.issubset(node_types)
    assert graph_payload["edges"]

    graph_query = client.get("/api/v1/knowledge/brain/graph/query?node_type=Employee&q=Nina", headers=headers)
    assert graph_query.status_code == 200
    graph_query_payload = graph_query.json()
    assert any(node["label"] == "Nina" and node["type"] == "Employee" for node in graph_query_payload["nodes"])

    with client.stream("GET", "/api/v1/knowledge/brain/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: enterprise_knowledge" in first_chunk
        assert "top_experts" in first_chunk
        assert "lessons_learned" in first_chunk
        assert "AI MEMORY SYSTEM COMPLETE" in first_chunk

    readiness = client.get("/api/v1/system/readiness")
    assert readiness.status_code == 200
    readiness_services = readiness.json()["services"]
    assert readiness_services["ai_memory_system"] is True
    assert readiness_services["enterprise_knowledge_brain"] is True
    assert readiness_services["enterprise_rag_system"] is True
    assert readiness_services["knowledge_graph_engine"] is True
    assert readiness_services["expertise_discovery_engine"] is True


def test_multi_company_benchmarking_scores_anonymous_dynamic_industry_intelligence() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/benchmarks/companies/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["model"] == "RandomForest Benchmark Intelligence + KMeans Anonymous Cohort Forecaster"
    assert baseline_payload["benchmark_scores"]
    assert baseline_payload["kpi_comparisons"]
    assert baseline_payload["heatmap"]
    assert baseline_payload["maturity_scorecards"]
    assert baseline_payload["recommendations"]
    assert "benchmarking_history.jsonl" in baseline_payload["storage"]
    assert {"anonymous_company_aggregation", "kmeans_peer_cohort_clustering", "privacy_noise_secure_aggregation"}.issubset(
        set(baseline_payload["source_systems"])
    )
    assert all(item["anonymized_company_id"].startswith("anon-") for item in baseline_payload["benchmark_scores"])
    assert not any("peer-ai" in item["anonymized_company_id"] for item in baseline_payload["benchmark_scores"])

    peer_companies = [
        {
            "company_id": "peer-top-1",
            "industry": "ai_saas",
            "company_stage": "scaleup",
            "employee_count": 850,
            "productivity_score": 0.86,
            "burnout_index": 0.24,
            "attrition_rate": 0.08,
            "retention_rate": 0.92,
            "team_efficiency": 0.84,
            "delivery_stability": 0.87,
            "workforce_happiness": 0.83,
            "innovation_output": 0.86,
            "collaboration_quality": 0.84,
            "project_success_rate": 0.88,
            "communication_health": 0.82,
            "learning_growth": 0.81,
            "operational_stability": 0.87,
            "sprint_velocity": 0.86,
            "overtime_intensity": 0.22,
            "incident_rate": 0.09,
            "ai_adoption": 0.9,
            "data_confidence": 0.9,
        },
        {
            "company_id": "peer-top-2",
            "industry": "ai_saas",
            "company_stage": "scaleup",
            "employee_count": 1150,
            "productivity_score": 0.81,
            "burnout_index": 0.29,
            "attrition_rate": 0.11,
            "retention_rate": 0.89,
            "team_efficiency": 0.8,
            "delivery_stability": 0.82,
            "workforce_happiness": 0.78,
            "innovation_output": 0.83,
            "collaboration_quality": 0.79,
            "project_success_rate": 0.82,
            "communication_health": 0.78,
            "learning_growth": 0.77,
            "operational_stability": 0.82,
            "sprint_velocity": 0.8,
            "overtime_intensity": 0.27,
            "incident_rate": 0.14,
            "ai_adoption": 0.84,
            "data_confidence": 0.9,
        },
    ]
    weak_target = {
        "company_id": "target-company",
        "industry": "ai_saas",
        "company_stage": "scaleup",
        "employee_count": 620,
        "productivity_score": 0.58,
        "burnout_index": 0.66,
        "attrition_rate": 0.28,
        "retention_rate": 0.72,
        "team_efficiency": 0.55,
        "delivery_stability": 0.57,
        "workforce_happiness": 0.5,
        "innovation_output": 0.58,
        "collaboration_quality": 0.52,
        "project_success_rate": 0.56,
        "communication_health": 0.49,
        "learning_growth": 0.54,
        "operational_stability": 0.55,
        "sprint_velocity": 0.56,
        "overtime_intensity": 0.61,
        "incident_rate": 0.34,
        "ai_adoption": 0.62,
        "data_confidence": 0.88,
    }
    strong_target = {
        **weak_target,
        "productivity_score": 0.9,
        "burnout_index": 0.18,
        "attrition_rate": 0.07,
        "retention_rate": 0.93,
        "team_efficiency": 0.88,
        "delivery_stability": 0.9,
        "workforce_happiness": 0.86,
        "innovation_output": 0.91,
        "collaboration_quality": 0.88,
        "project_success_rate": 0.91,
        "communication_health": 0.86,
        "learning_growth": 0.88,
        "operational_stability": 0.9,
        "sprint_velocity": 0.89,
        "overtime_intensity": 0.18,
        "incident_rate": 0.07,
        "ai_adoption": 0.94,
    }
    weak = client.post(
        "/api/v1/benchmarks/companies/analyze",
        headers=headers,
        json={
            "cycle_name": "Benchmark Weak Target Test",
            "target_company_id": "target-company",
            "industry": "ai_saas",
            "company_stage": "scaleup",
            "horizon_days": 120,
            "privacy_epsilon": 2.2,
            "companies": [weak_target, *peer_companies],
        },
    )
    strong = client.post(
        "/api/v1/benchmarks/companies/analyze",
        headers=headers,
        json={
            "cycle_name": "Benchmark Strong Target Test",
            "target_company_id": "target-company",
            "industry": "ai_saas",
            "company_stage": "scaleup",
            "horizon_days": 120,
            "privacy_epsilon": 2.2,
            "companies": [strong_target, *peer_companies],
        },
    )
    assert weak.status_code == 200
    assert strong.status_code == 200
    weak_payload = weak.json()
    strong_payload = strong.json()
    assert weak_payload["summary"]["productivity_vs_industry"] < 0
    assert weak_payload["summary"]["burnout_vs_industry"] < 0
    assert weak_payload["summary"]["retention_vs_industry"] < 0
    assert strong_payload["summary"]["target_benchmark_score"] > weak_payload["summary"]["target_benchmark_score"]
    assert strong_payload["summary"]["productivity_vs_industry"] > weak_payload["summary"]["productivity_vs_industry"]
    assert strong_payload["summary"]["high_priority_gaps"] <= weak_payload["summary"]["high_priority_gaps"]
    assert weak_payload["alerts"]
    assert any(item["category"] in {"burnout", "retention", "collaboration", "maturity"} for item in weak_payload["recommendations"])
    assert weak_payload["benchmark_scores"][0]["anonymized_company_id"].startswith("anon-")
    assert weak_payload["benchmark_scores"][0]["anonymized_company_id"] != "target-company"

    with client.stream("GET", "/api/v1/benchmarks/companies/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: benchmarking" in first_chunk
        assert "benchmark_scores" in first_chunk


def test_work_life_balance_optimizer_is_dynamic_forecasting_and_recommendation_system() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/work-life/balance/default", headers=headers)
    assert baseline.status_code == 200
    baseline_payload = baseline.json()
    assert baseline_payload["model"] == "AI Work-Life Balance Optimizer"
    assert baseline_payload["employee_plans"]
    assert baseline_payload["team_balance"]
    assert baseline_payload["focus_blocks"]
    assert baseline_payload["meeting_plan"]
    assert baseline_payload["recommendations"]
    assert baseline_payload["forecast"]
    assert baseline_payload["heatmap"]
    assert "work_life_balance_history.jsonl" in baseline_payload["storage"]
    assert {"random_forest_work_life_model", "gradient_boosting_burnout_forecaster", "kmeans_energy_schedule_segmenter"}.issubset(
        set(baseline_payload["source_systems"])
    )

    healthy_employees = [
        {
            "employee_id": "healthy-engineer",
            "name": "Healthy Engineer",
            "department": "Engineering",
            "team": "Platform",
            "role": "Backend Engineer",
            "meeting_hours_per_week": 7,
            "recurring_meeting_hours": 3,
            "async_candidate_hours": 1,
            "overtime_hours_30d": 6,
            "after_hours_messages_30d": 8,
            "focus_hours_per_day": 5.8,
            "context_switches_per_hour": 8,
            "task_load_hours": 32,
            "capacity_hours": 40,
            "deadline_pressure": 0.22,
            "collaboration_dependency": 0.35,
            "burnout_risk": 0.14,
            "stress_score": 0.18,
            "wellness_score": 0.88,
            "productivity_score": 0.91,
            "energy_morning": 0.82,
            "energy_afternoon": 0.68,
            "flexibility_fit": 0.83,
            "manager_support": 0.86,
        },
        {
            "employee_id": "healthy-peer",
            "name": "Healthy Peer",
            "department": "Engineering",
            "team": "Platform",
            "role": "Frontend Engineer",
            "meeting_hours_per_week": 6,
            "recurring_meeting_hours": 3,
            "async_candidate_hours": 1,
            "overtime_hours_30d": 5,
            "after_hours_messages_30d": 7,
            "focus_hours_per_day": 5.3,
            "context_switches_per_hour": 9,
            "task_load_hours": 31,
            "capacity_hours": 40,
            "deadline_pressure": 0.26,
            "collaboration_dependency": 0.38,
            "burnout_risk": 0.16,
            "stress_score": 0.2,
            "wellness_score": 0.84,
            "productivity_score": 0.88,
            "energy_morning": 0.7,
            "energy_afternoon": 0.76,
            "flexibility_fit": 0.8,
            "manager_support": 0.82,
        },
    ]
    overloaded_employees = [
        {
            **healthy_employees[0],
            "employee_id": "overloaded-owner",
            "name": "Overloaded Owner",
            "meeting_hours_per_week": 24,
            "recurring_meeting_hours": 15,
            "async_candidate_hours": 8,
            "overtime_hours_30d": 76,
            "after_hours_messages_30d": 180,
            "focus_hours_per_day": 1.4,
            "context_switches_per_hour": 42,
            "task_load_hours": 66,
            "deadline_pressure": 0.9,
            "collaboration_dependency": 0.82,
            "burnout_risk": 0.86,
            "stress_score": 0.84,
            "wellness_score": 0.32,
            "productivity_score": 0.75,
        },
        {
            **healthy_employees[1],
            "employee_id": "underloaded-peer",
            "name": "Underloaded Peer",
            "task_load_hours": 26,
            "burnout_risk": 0.18,
            "stress_score": 0.21,
            "wellness_score": 0.86,
        },
    ]
    healthy = client.post(
        "/api/v1/work-life/balance/optimize",
        headers=headers,
        json={
            "cycle_name": "Healthy Balance Test",
            "target_department": "Engineering",
            "horizon_days": 45,
            "employees": healthy_employees,
        },
    )
    overloaded = client.post(
        "/api/v1/work-life/balance/optimize",
        headers=headers,
        json={
            "cycle_name": "Overloaded Balance Test",
            "target_department": "Engineering",
            "horizon_days": 45,
            "employees": overloaded_employees,
        },
    )
    assert healthy.status_code == 200
    assert overloaded.status_code == 200
    healthy_payload = healthy.json()
    overloaded_payload = overloaded.json()
    assert overloaded_payload["summary"]["burnout_risk"] > healthy_payload["summary"]["burnout_risk"]
    assert overloaded_payload["summary"]["meeting_reduction_percent"] > healthy_payload["summary"]["meeting_reduction_percent"]
    assert overloaded_payload["summary"]["task_redistribution_hours"] > healthy_payload["summary"]["task_redistribution_hours"]
    assert overloaded_payload["summary"]["projected_burnout_reduction"] > 0
    assert any(item["category"] in {"meeting_reduction", "task_redistribution", "burnout_prevention", "focus_time"} for item in overloaded_payload["recommendations"])
    assert any("10:00" in plan["focus_block"] or "14:00" in plan["focus_block"] for plan in overloaded_payload["employee_plans"])
    assert overloaded_payload["risk_alerts"]

    with client.stream("GET", "/api/v1/work-life/balance/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: work_life_balance" in first_chunk
        assert "employee_plans" in first_chunk


def test_enterprise_model_suite_is_real_and_dynamic() -> None:
    headers = auth_headers()
    validation = client.get("/api/v1/intelligence/models/validation", headers=headers)
    assert validation.status_code == 200
    payload = validation.json()
    model_names = {metric["model"] for metric in payload["metrics"]}
    assert {"Random Forest", "XGBoost", "PyTorch Neural Network"}.issubset(model_names)
    assert all(metric["roc_auc"] >= 0.9 for metric in payload["metrics"])

    low_risk = client.post(
        "/api/v1/intelligence/burnout/predict",
        headers=headers,
        json={
            "department": "Finance",
            "overtime_hours": 2,
            "meeting_hours": 4,
            "sentiment_score": 0.7,
            "task_completion_ratio": 0.96,
            "absence_days": 0,
        },
    ).json()
    high_risk = client.post(
        "/api/v1/intelligence/burnout/predict",
        headers=headers,
        json={
            "department": "Engineering",
            "overtime_hours": 25,
            "meeting_hours": 31,
            "sentiment_score": -0.8,
            "task_completion_ratio": 0.48,
            "absence_days": 7,
        },
    ).json()
    assert high_risk["model_probabilities"]["ensemble"] > low_risk["model_probabilities"]["ensemble"]
    assert {"random_forest", "xgboost", "neural_network", "ensemble"}.issubset(high_risk["model_probabilities"])


def test_nlp_sentiment_pipeline_is_real_and_dynamic() -> None:
    headers = auth_headers()
    positive = client.post(
        "/api/v1/nlp/analyze",
        headers=headers,
        json={
            "employee_id": "emp-positive",
            "department": "Engineering",
            "channel": "chat",
            "text": "The launch went well and I feel motivated by the team progress",
        },
    )
    burnout = client.post(
        "/api/v1/nlp/analyze",
        headers=headers,
        json={
            "employee_id": "emp-burnout",
            "department": "Engineering",
            "channel": "chat",
            "text": "I am exhausted, overloaded, and working late every night on weekend incidents",
        },
    )
    toxic = client.post(
        "/api/v1/nlp/analyze",
        headers=headers,
        json={
            "employee_id": "emp-toxic",
            "department": "Operations",
            "channel": "chat",
            "text": "This conversation is hostile and people are blaming each other aggressively",
        },
    )
    assert positive.status_code == 200
    assert burnout.status_code == 200
    assert toxic.status_code == 200
    positive_payload = positive.json()
    burnout_payload = burnout.json()
    toxic_payload = toxic.json()
    assert positive_payload["sentiment"] == "positive"
    assert burnout_payload["emotion_scores"]["burnout"] > positive_payload["emotion_scores"]["burnout"]
    assert burnout_payload["emotion_scores"]["stress"] > positive_payload["emotion_scores"]["stress"]
    assert toxic_payload["emotion_scores"]["toxicity"] > positive_payload["emotion_scores"]["toxicity"]
    assert burnout_payload["tokens"]
    assert burnout_payload["model"] == "PyTorch TextEmotionNet"


def test_nlp_batch_and_trends() -> None:
    headers = auth_headers()
    response = client.post(
        "/api/v1/nlp/batch",
        headers=headers,
        json={
            "messages": [
                {"employee_id": "emp-1", "department": "Sales", "channel": "email", "text": "The customer feedback is positive"},
                {"employee_id": "emp-2", "department": "Sales", "channel": "chat", "text": "I am frustrated by repeated rework"},
            ]
        },
    )
    assert response.status_code == 200
    assert len(response.json()["results"]) == 2
    trends = client.get("/api/v1/nlp/trends", headers=headers)
    assert trends.status_code == 200
    assert "trends" in trends.json()


def test_time_series_forecasting_pipeline_is_real_and_dynamic() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/forecasting/workload/default", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "PyTorch WorkloadLSTM"
    assert len(payload["history"]) >= 14
    assert len(payload["forecast"]) == 14
    assert payload["confidence"] > 0.6
    assert payload["forecast"][0]["lower_bound"] <= payload["forecast"][0]["workload"] <= payload["forecast"][0]["upper_bound"]

    overloaded_history = []
    for index in range(21):
        overloaded_history.append(
            {
                "date": f"2026-05-{index + 1:02d}",
                "workload": min(100, 74 + index * 0.8),
                "productivity": max(45, 82 - index * 0.7),
                "overtime_hours": min(18, 7 + index * 0.25),
                "attendance_rate": max(0.8, 0.96 - index * 0.004),
                "task_completion_rate": max(0.5, 0.88 - index * 0.01),
                "burnout_risk": min(0.95, 0.34 + index * 0.02),
                "delay_probability": min(0.9, 0.22 + index * 0.018),
            }
        )
    overloaded = client.post(
        "/api/v1/forecasting/workload",
        headers=headers,
        json={"department": "Engineering", "horizon_days": 10, "history": overloaded_history},
    )
    assert overloaded.status_code == 200
    overloaded_payload = overloaded.json()
    assert len(overloaded_payload["forecast"]) == 10
    assert overloaded_payload["team_collapse_probability"] >= 0.3
    assert any(signal["metric"] == "burnout" for signal in overloaded_payload["trend_signals"])


def test_recommendation_ai_pipeline_is_real_and_dynamic() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/recommendations/default", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "Hybrid RandomForest Enterprise Recommender"
    assert payload["employees_analyzed"] >= 4
    categories = {item["category"] for item in payload["recommendations"]}
    assert {"work_redistribution", "break", "team_balancing"}.issubset(categories)
    assert all(0 <= item["confidence"] <= 1 for item in payload["recommendations"])
    assert all(item["impact_score"] > 0 for item in payload["recommendations"])

    custom = client.post(
        "/api/v1/recommendations/generate",
        headers=headers,
        json={
            "employees": [
                {
                    "employee_id": "emp-over",
                    "name": "Employee A",
                    "role": "Backend Lead",
                    "team": "Core",
                    "skills": ["python", "api"],
                    "current_tasks": 13,
                    "capacity_hours": 40,
                    "allocated_hours": 62,
                    "productivity": 0.68,
                    "overtime_hours": 16,
                    "stress_score": 0.88,
                    "burnout_risk": 0.82,
                    "collaboration_score": 0.7,
                },
                {
                    "employee_id": "emp-ready",
                    "name": "Employee B",
                    "role": "Backend Engineer",
                    "team": "Enablement",
                    "skills": ["python", "api"],
                    "current_tasks": 3,
                    "capacity_hours": 40,
                    "allocated_hours": 22,
                    "productivity": 0.92,
                    "overtime_hours": 1,
                    "stress_score": 0.18,
                    "burnout_risk": 0.12,
                    "collaboration_score": 0.91,
                },
            ],
            "tasks": [
                {
                    "task_id": "task-api",
                    "title": "payments API hardening",
                    "required_skill": "python",
                    "effort_hours": 9,
                    "priority": 5,
                    "project": "Revenue Platform",
                }
            ],
        },
    )
    assert custom.status_code == 200
    custom_payload = custom.json()
    redistribution = [item for item in custom_payload["recommendations"] if item["category"] == "work_redistribution"]
    assert redistribution
    assert "Employee A" in redistribution[0]["rationale"]
    assert "Employee B" in redistribution[0]["action"]

    feedback = client.post(
        "/api/v1/recommendations/feedback",
        headers=headers,
        json={"recommendation_id": redistribution[0]["recommendation_id"], "accepted": True, "usefulness_score": 5},
    )
    assert feedback.status_code == 200
    assert feedback.json()["learning_signal"] == 1.0


def test_resource_allocation_optimizer_is_real_dynamic_and_streamed() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/resources/allocation/default", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "AI Resource Allocation System"
    assert "RandomForest Resource Allocation" in payload["ml_model"]
    assert payload["assignments"]
    assert payload["dependency_graph"]
    assert payload["capacity_forecast"]
    assert payload["sprint_plan"]
    assert payload["summary"]["assignments_generated"] == len(payload["assignments"])

    custom = client.post(
        "/api/v1/resources/allocation/optimize",
        headers=headers,
        json={
            "department": "Engineering",
            "sprint_name": "Emergency Resource Rebalance",
            "objective": "burnout_safe",
            "employees": [
                {
                    "employee_id": "over",
                    "name": "Employee A",
                    "role": "Backend Lead",
                    "team": "Core",
                    "department": "Engineering",
                    "skills": ["python", "api architecture", "incident response"],
                    "capacity_hours": 40,
                    "current_hours": 62,
                    "availability": 0.78,
                    "productivity": 0.68,
                    "historical_delivery_speed": 0.62,
                    "collaboration_score": 0.72,
                    "learning_agility": 0.58,
                    "burnout_risk": 0.9,
                    "stress_score": 0.88,
                    "focus_score": 0.34,
                    "hourly_cost": 112,
                },
                {
                    "employee_id": "ready",
                    "name": "Employee B",
                    "role": "DevOps Engineer",
                    "team": "Enablement",
                    "department": "Engineering",
                    "skills": ["kubernetes", "automation", "incident response", "terraform"],
                    "capacity_hours": 40,
                    "current_hours": 23,
                    "availability": 0.96,
                    "productivity": 0.91,
                    "historical_delivery_speed": 0.89,
                    "collaboration_score": 0.9,
                    "learning_agility": 0.74,
                    "burnout_risk": 0.18,
                    "stress_score": 0.22,
                    "focus_score": 0.76,
                    "hourly_cost": 94,
                },
                {
                    "employee_id": "ml",
                    "name": "Employee C",
                    "role": "ML Engineer",
                    "team": "AI",
                    "department": "AI",
                    "skills": ["mlops", "python", "forecasting"],
                    "capacity_hours": 40,
                    "current_hours": 26,
                    "availability": 0.92,
                    "productivity": 0.9,
                    "historical_delivery_speed": 0.88,
                    "collaboration_score": 0.84,
                    "learning_agility": 0.9,
                    "burnout_risk": 0.24,
                    "stress_score": 0.28,
                    "focus_score": 0.78,
                    "hourly_cost": 105,
                },
                {
                    "employee_id": "qa",
                    "name": "Employee D",
                    "role": "QA Engineer",
                    "team": "Quality",
                    "department": "Engineering",
                    "skills": ["testing", "automation", "api testing"],
                    "capacity_hours": 38,
                    "current_hours": 22,
                    "availability": 0.95,
                    "productivity": 0.87,
                    "historical_delivery_speed": 0.9,
                    "collaboration_score": 0.83,
                    "learning_agility": 0.72,
                    "burnout_risk": 0.2,
                    "stress_score": 0.25,
                    "focus_score": 0.82,
                    "hourly_cost": 78,
                },
            ],
            "tasks": [
                {
                    "task_id": "api",
                    "title": "API recovery lane",
                    "project": "Reliability",
                    "description": "Critical FastAPI recovery lane",
                    "required_skills": ["python", "api architecture", "incident response"],
                    "effort_hours": 15,
                    "complexity": 0.78,
                    "priority": 5,
                    "deadline_days": 3,
                    "revenue_impact": 1800000,
                    "dependency_task_ids": ["runbook"],
                    "preferred_team": "Core",
                    "cognitive_load": 0.75,
                },
                {
                    "task_id": "k8s",
                    "title": "Kubernetes rollback automation",
                    "project": "Reliability",
                    "description": "Deployment guardrails",
                    "required_skills": ["kubernetes", "automation", "terraform"],
                    "effort_hours": 12,
                    "complexity": 0.66,
                    "priority": 5,
                    "deadline_days": 4,
                    "revenue_impact": 1600000,
                    "preferred_team": "Enablement",
                    "cognitive_load": 0.62,
                },
                {
                    "task_id": "mlops",
                    "title": "Forecast drift monitor",
                    "project": "AI Stability",
                    "description": "Model drift monitoring",
                    "required_skills": ["mlops", "python", "forecasting"],
                    "effort_hours": 10,
                    "complexity": 0.62,
                    "priority": 4,
                    "deadline_days": 6,
                    "revenue_impact": 900000,
                    "dependency_task_ids": ["api"],
                    "preferred_team": "AI",
                    "cognitive_load": 0.58,
                },
                {
                    "task_id": "qa",
                    "title": "Regression stream suite",
                    "project": "Reliability",
                    "description": "Realtime stream regression coverage",
                    "required_skills": ["testing", "automation", "api testing"],
                    "effort_hours": 9,
                    "complexity": 0.5,
                    "priority": 4,
                    "deadline_days": 5,
                    "revenue_impact": 750000,
                    "dependency_task_ids": ["api"],
                    "preferred_team": "Quality",
                    "cognitive_load": 0.43,
                },
            ],
            "dependencies": [
                {"source_task_id": "api", "target_task_id": "runbook", "blocker_type": "incident_dependency", "risk_weight": 0.82},
                {"source_task_id": "mlops", "target_task_id": "api", "blocker_type": "platform_dependency", "risk_weight": 0.55},
                {"source_task_id": "qa", "target_task_id": "api", "blocker_type": "test_dependency", "risk_weight": 0.46},
            ],
        },
    )
    assert custom.status_code == 200
    custom_payload = custom.json()
    assigned_ids = {item["employee_id"] for item in custom_payload["assignments"]}
    assert "over" not in assigned_ids
    assert {"ready", "ml", "qa"}.intersection(assigned_ids)
    overloaded_balance = next(item for item in custom_payload["workload_balance"] if item["employee_id"] == "over")
    assert overloaded_balance["action"] == "Reduce allocation"
    assert overloaded_balance["overload_risk"] >= 90
    assert custom_payload["summary"]["capacity_utilization"] > payload["summary"]["capacity_utilization"]
    assert custom_payload["summary"]["sprint_completion_probability"] < payload["summary"]["sprint_completion_probability"]
    assert any(alert["title"] == "Burnout-safe allocation breach" for alert in custom_payload["risk_alerts"])

    stream = client.get("/api/v1/resources/allocation/stream", headers=headers)
    assert stream.status_code == 200
    assert "event: resource_allocation" in stream.text
    assert "sprint_completion_probability" in stream.text


def test_autonomous_workflow_automation_assigns_approves_schedules_balances_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/workflows/autonomous/default", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "Virtual Operations Manager AI - Autonomous Workflow Automation System"
    assert payload["task_assignments"]
    assert payload["approval_decisions"]
    assert payload["meeting_schedules"]
    assert payload["reminders"]
    assert payload["workload_balancing"]
    assert payload["automation_events"]
    assert payload["agent_actions"]
    assert payload["escalations"]
    assert payload["recommendations"]
    assert payload["summary"]["active_workflows"] >= len(payload["task_assignments"])
    assert payload["summary"]["scheduled_meetings"] >= 1
    assert payload["summary"]["policy_automation_rate"] > 0
    assert payload["summary"]["average_assignment_confidence"] > 0.5
    assert payload["workload_balancing"][0]["hours"] > 0
    assert {"workflow_engine", "automation_engine", "approval_engine", "task_assignment_engine", "scheduling_engine", "notification_engine", "multi_agent_orchestrator"}.issubset(
        set(payload["source_systems"])
    )
    agents = {item["agent"] for item in payload["agent_actions"]}
    assert {"HR Agent", "Project Agent", "Productivity Agent", "Security Agent", "Executive Agent"}.issubset(agents)
    assert any(item["decision"] == "approved" for item in payload["approval_decisions"])

    custom = client.post(
        "/api/v1/workflows/autonomous/run",
        headers=headers,
        json={
            "mode": "pressure",
            "approval_requests": [
                {
                    "request_id": "approval-admin-access-test",
                    "request_type": "access",
                    "requester_id": "res-backend",
                    "requester_name": "Aarav Mehta",
                    "team": "Platform",
                    "requested_access_level": "permanent-admin",
                    "business_impact": 0.55,
                    "urgency": "high",
                    "justification": "Need broad production access for incident review.",
                }
            ],
            "completed_task_ids": ["task-observability"],
        },
    )
    assert custom.status_code == 200
    custom_payload = custom.json()
    decision = custom_payload["approval_decisions"][0]
    assert decision["request_id"] == "approval-admin-access-test"
    assert decision["decision"] in {"rejected", "needs_review"}
    assert decision["risk_score"] >= 50
    assert any(event["trigger"] == "task_completed" for event in custom_payload["automation_events"])

    assistant = client.post(
        "/api/v1/workflows/autonomous/assistant",
        headers=headers,
        json={"question": "Assign this task."},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["intent"] == "assignment"
    assert assistant_payload["triggered_actions"]
    assert "Assign" in assistant_payload["answer"]

    stream = client.get("/api/v1/workflows/autonomous/stream", headers=headers)
    assert stream.status_code == 200
    assert "event: autonomous_workflow" in stream.text
    assert "task_assignments" in stream.text

    platform = client.get("/api/v1/platform/operating-system", headers=headers)
    assert platform.status_code == 200
    names = {capability["name"]: capability for capability in platform.json()["capabilities"]}
    workflow = names["Autonomous Workflow Automation System"]
    assert workflow["status"] == "ready"
    assert {"workflow_engine", "automation_engine", "approval_engine", "task_assignment_engine", "scheduling_engine", "multi_agent_orchestrator"}.issubset(
        set(workflow["source_systems"])
    )


def test_anomaly_detection_pipeline_is_real_and_dynamic() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/anomalies/default", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "IsolationForest + LOF Behavioral Anomaly Detector"
    assert payload["events_analyzed"] >= 5
    assert payload["adaptive_threshold"] > 0
    assert payload["alerts"]
    assert payload["summary"]["insider_threats"] >= 1
    assert payload["summary"]["data_leakage_alerts"] >= 1
    assert payload["user_risk_heatmap"]
    assert payload["security_recommendations"]
    assert payload["executive_insights"]
    assert all(0 <= alert["anomaly_score"] <= 100 for alert in payload["alerts"])
    assert all(0 <= alert["data_leakage_probability"] <= 100 for alert in payload["alerts"])

    normal = client.post(
        "/api/v1/anomalies/detect",
        headers=headers,
        json={
            "sensitivity": 0.45,
            "events": [
                {
                    "employee_id": "emp-normal",
                    "employee_name": "Normal Employee",
                    "department": "Operations",
                    "role": "Program Manager",
                    "timestamp": "2026-05-28T09:00:00Z",
                    "login_count": 7,
                    "failed_logins": 0,
                    "off_hours_logins": 0,
                    "inactive_hours": 1.0,
                    "productivity_score": 0.91,
                    "overtime_hours": 1,
                    "messages_sent": 35,
                    "negative_sentiment_ratio": 0.08,
                    "toxic_message_count": 0,
                    "data_download_mb": 120,
                    "privileged_actions": 1,
                    "project_commits": 6,
                    "meeting_hours": 4,
                    "stress_score": 0.22,
                    "access_scope_changes": 0,
                }
            ],
        },
    )
    insider = client.post(
        "/api/v1/anomalies/detect",
        headers=headers,
        json={
            "sensitivity": 0.65,
            "events": [
                {
                    "employee_id": "emp-threat",
                    "employee_name": "Threat Employee",
                    "department": "Finance",
                    "role": "Systems Admin",
                    "timestamp": "2026-05-28T09:05:00Z",
                    "login_count": 22,
                    "failed_logins": 15,
                    "off_hours_logins": 11,
                    "inactive_hours": 0.5,
                    "productivity_score": 0.8,
                    "overtime_hours": 3,
                    "messages_sent": 18,
                    "negative_sentiment_ratio": 0.2,
                    "toxic_message_count": 0,
                    "data_download_mb": 8200,
                    "privileged_actions": 34,
                    "project_commits": 2,
                    "meeting_hours": 3,
                    "stress_score": 0.42,
                    "access_scope_changes": 10,
                    "device_change_count": 4,
                    "unusual_location_count": 3,
                    "impossible_travel_events": 1,
                    "browser_fingerprint_changes": 4,
                    "sensitive_file_accesses": 970,
                    "external_transfer_mb": 2400,
                    "cloud_upload_mb": 3100,
                    "usb_write_mb": 1200,
                    "policy_violation_count": 9,
                    "admin_role_changes": 3,
                    "privileged_session_minutes": 260,
                    "baseline_deviation": 0.93,
                }
            ],
        },
    )
    assert normal.status_code == 200
    assert insider.status_code == 200
    normal_payload = normal.json()
    insider_payload = insider.json()
    normal_top = normal_payload["alerts"][0]["anomaly_score"] if normal_payload["alerts"] else 0
    insider_top = insider_payload["alerts"][0]
    assert insider_top["anomaly_score"] > normal_top
    assert insider_top["insider_threat_score"] >= 80
    assert insider_top["data_leakage_probability"] >= 80
    assert insider_top["access_anomaly_score"] >= 70
    assert insider_top["privilege_misuse_score"] >= 70
    assert insider_top["fraud_likelihood"] >= 70
    assert any(token in insider_top["anomaly_type"].lower() for token in ["insider", "leakage", "access", "privilege", "fraud"])
    assert any("downloaded" in evidence for evidence in insider_top["evidence"])
    assert insider_top["mitigation_actions"]
    assert insider_payload["summary"]["data_leakage_alerts"] >= 1
    assert insider_payload["summary"]["access_anomaly_alerts"] >= 1
    assert insider_payload["summary"]["privilege_misuse_alerts"] >= 1
    assert any(item["department"] == "Finance" for item in insider_payload["user_risk_heatmap"])
    assert any("DLP" in item["title"] or "privileged" in item["action"].lower() or "authentication" in item["title"].lower() for item in insider_payload["security_recommendations"])

    feedback = client.post(
        "/api/v1/anomalies/feedback",
        headers=headers,
        json={"alert_id": insider_top["alert_id"], "confirmed": True, "severity_adjustment": 1},
    )
    assert feedback.status_code == 200
    assert feedback.json()["learning_signal"] > 0.8

    with client.stream("GET", "/api/v1/anomalies/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: anomaly" in first_chunk
        assert "data_leakage_probability" in first_chunk


def test_employee_dashboard_pipeline_is_real_and_dynamic() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/employees/dashboard/default", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "RandomForest Employee Analytics + Burnout Ensemble"
    assert len(payload["history"]) >= 14
    assert 0 <= payload["stress"]["value"] <= 100
    assert 0 <= payload["productivity"]["value"] <= 100
    assert 0 <= payload["burnout_probability"]["value"] <= 100
    assert {"random_forest", "xgboost", "neural_network", "ensemble", "employee_burnout"}.issubset(payload["model_probabilities"])

    calm = client.post(
        "/api/v1/employees/dashboard/analyze",
        headers=headers,
        json={
            "employee_id": "emp-calm",
            "employee_name": "Calm Employee",
            "department": "Operations",
            "role": "Program Manager",
            "current": {
                "timestamp": "2026-05-28T10:00:00Z",
                "overtime_hours": 1,
                "workload_intensity": 42,
                "meeting_hours": 3,
                "sentiment_score": 0.62,
                "task_completion_ratio": 0.94,
                "attendance_rate": 0.99,
                "focus_hours": 7,
                "collaboration_score": 0.91,
                "activity_variance": 0.16,
                "negative_message_ratio": 0.05,
                "toxic_message_count": 0,
                "absence_days": 0,
            },
        },
    )
    overloaded = client.post(
        "/api/v1/employees/dashboard/analyze",
        headers=headers,
        json={
            "employee_id": "emp-overloaded",
            "employee_name": "Overloaded Employee",
            "department": "Engineering",
            "role": "Incident Lead",
            "current": {
                "timestamp": "2026-05-28T10:05:00Z",
                "overtime_hours": 21,
                "workload_intensity": 93,
                "meeting_hours": 15,
                "sentiment_score": -0.72,
                "task_completion_ratio": 0.48,
                "attendance_rate": 0.82,
                "focus_hours": 1.8,
                "collaboration_score": 0.52,
                "activity_variance": 0.86,
                "negative_message_ratio": 0.67,
                "toxic_message_count": 4,
                "absence_days": 6,
            },
        },
    )
    assert calm.status_code == 200
    assert overloaded.status_code == 200
    calm_payload = calm.json()
    overloaded_payload = overloaded.json()
    assert overloaded_payload["stress"]["value"] > calm_payload["stress"]["value"]
    assert overloaded_payload["burnout_probability"]["value"] > calm_payload["burnout_probability"]["value"]
    assert overloaded_payload["productivity"]["value"] < calm_payload["productivity"]["value"]
    assert overloaded_payload["recommendations"]


def test_manager_dashboard_pipeline_is_real_and_dynamic() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/managers/dashboard/default", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "RandomForest/XGBoost Manager Risk Intelligence"
    assert payload["risky_teams"]
    assert payload["overloaded_employees"]
    assert payload["delay_predictions"]
    assert len(payload["trend"]) >= 10
    assert 0 <= payload["summary"]["average_team_risk"] <= 100

    stable = client.post(
        "/api/v1/managers/dashboard/analyze",
        headers=headers,
        json={
            "manager_id": "mgr-stable",
            "manager_name": "Stable Manager",
            "teams": [
                {
                    "team_id": "team-stable",
                    "team_name": "Stable Team",
                    "department": "Operations",
                    "member_count": 10,
                    "burnout_probability": 0.12,
                    "productivity_decline": 0.04,
                    "average_stress": 0.22,
                    "toxicity_ratio": 0.02,
                    "overload_ratio": 0.12,
                    "missed_deadlines": 0,
                    "attendance_rate": 0.98,
                    "collaboration_score": 0.92,
                    "overtime_escalation": 0.08,
                    "dependency_bottlenecks": 0,
                }
            ],
            "employees": [
                {
                    "employee_id": "emp-stable",
                    "employee_name": "Stable Employee",
                    "team_name": "Stable Team",
                    "role": "Coordinator",
                    "active_tasks": 5,
                    "overtime_hours": 1,
                    "meeting_hours": 3,
                    "productivity_score": 0.92,
                    "work_intensity": 0.32,
                    "deadline_pressure": 0.24,
                    "multi_project_allocation": 1,
                    "stress_score": 0.18,
                    "task_completion_ratio": 0.94,
                }
            ],
            "projects": [
                {
                    "project_id": "project-stable",
                    "project_name": "Stable Project",
                    "team_name": "Stable Team",
                    "task_completion_speed": 0.92,
                    "team_productivity_trend": 0.22,
                    "historical_delivery_rate": 0.95,
                    "burnout_growth": 0.08,
                    "team_overload": 0.12,
                    "dependency_bottlenecks": 0,
                    "resource_shortage": 0.04,
                    "communication_efficiency": 0.93,
                    "scope_change_rate": 0.05,
                    "days_to_deadline": 45,
                }
            ],
        },
    )
    crisis = client.post(
        "/api/v1/managers/dashboard/analyze",
        headers=headers,
        json={
            "manager_id": "mgr-crisis",
            "manager_name": "Crisis Manager",
            "sensitivity": 0.72,
            "teams": [
                {
                    "team_id": "team-crisis",
                    "team_name": "Development Team",
                    "department": "Engineering",
                    "member_count": 22,
                    "burnout_probability": 0.92,
                    "productivity_decline": 0.74,
                    "average_stress": 0.9,
                    "toxicity_ratio": 0.31,
                    "overload_ratio": 0.88,
                    "missed_deadlines": 11,
                    "attendance_rate": 0.78,
                    "collaboration_score": 0.49,
                    "overtime_escalation": 0.88,
                    "dependency_bottlenecks": 12,
                }
            ],
            "employees": [
                {
                    "employee_id": "emp-john",
                    "employee_name": "Employee John",
                    "team_name": "Development Team",
                    "role": "Backend Lead",
                    "active_tasks": 24,
                    "overtime_hours": 22,
                    "meeting_hours": 16,
                    "productivity_score": 0.44,
                    "work_intensity": 0.96,
                    "deadline_pressure": 0.94,
                    "multi_project_allocation": 7,
                    "stress_score": 0.93,
                    "task_completion_ratio": 0.43,
                }
            ],
            "projects": [
                {
                    "project_id": "project-alpha",
                    "project_name": "Project Alpha",
                    "team_name": "Development Team",
                    "task_completion_speed": 0.31,
                    "team_productivity_trend": -0.72,
                    "historical_delivery_rate": 0.48,
                    "burnout_growth": 0.86,
                    "team_overload": 0.91,
                    "dependency_bottlenecks": 13,
                    "resource_shortage": 0.72,
                    "communication_efficiency": 0.38,
                    "scope_change_rate": 0.66,
                    "days_to_deadline": 9,
                }
            ],
        },
    )
    assert stable.status_code == 200
    assert crisis.status_code == 200
    stable_payload = stable.json()
    crisis_payload = crisis.json()
    assert crisis_payload["risky_teams"][0]["risk_score"] > stable_payload["risky_teams"][0]["risk_score"]
    assert crisis_payload["overloaded_employees"][0]["overload_score"] > stable_payload["overloaded_employees"][0]["overload_score"]
    assert crisis_payload["delay_predictions"][0]["delay_probability"] > stable_payload["delay_predictions"][0]["delay_probability"]
    assert "Development Team" in crisis_payload["risky_teams"][0]["team_name"]


def test_ai_alert_system_correlates_models_and_streams() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/alerts/feed", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "Cross-System AI Alert Correlator"
    assert payload["alerts"]
    categories = {alert["category"] for alert in payload["alerts"]}
    assert {"burnout", "overload", "delay", "security", "toxicity"}.intersection(categories)
    assert all(0 <= alert["risk_score"] <= 100 for alert in payload["alerts"])
    assert any("manager_dashboard" in alert["source_systems"] for alert in payload["alerts"])
    assert any("anomaly_detection" in alert["source_systems"] for alert in payload["alerts"])

    crisis = client.post(
        "/api/v1/alerts/detect",
        headers=headers,
        json={"scenario": "crisis", "sensitivity": 0.78},
    )
    assert crisis.status_code == 200
    crisis_payload = crisis.json()
    crisis_categories = {alert["category"] for alert in crisis_payload["alerts"]}
    assert {"burnout", "productivity", "overload", "delay", "security", "operations"}.issubset(crisis_categories)
    assert crisis_payload["summary"]["critical"] >= payload["summary"]["critical"]
    assert crisis_payload["summary"]["average_risk"] >= payload["summary"]["average_risk"]

    top_alert = crisis_payload["alerts"][0]
    acknowledgement = client.post(
        "/api/v1/alerts/acknowledge",
        headers=headers,
        json={"alert_id": top_alert["alert_id"], "acknowledged": True, "notes": "Validated by test operator."},
    )
    assert acknowledgement.status_code == 200
    assert acknowledgement.json()["acknowledged"] is True

    with client.stream("GET", "/api/v1/alerts/stream", headers=headers) as response:
        assert response.status_code == 200
        first_chunk = next(response.iter_text())
        assert "event: alerts" in first_chunk
        assert "Cross-System AI Alert Correlator" in first_chunk


def test_smart_suggestion_engine_is_dynamic_and_streamed() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/suggestions/feed", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "Smart Decision Intelligence Engine"
    categories = {suggestion["category"] for suggestion in payload["suggestions"]}
    assert {
        "meeting_reduction",
        "workload_redistribution",
        "wellness_break",
        "team_optimization",
        "productivity_improvement",
    }.issubset(categories)
    assert all(0 <= suggestion["impact_score"] <= 100 for suggestion in payload["suggestions"])
    assert all(0 <= suggestion["confidence"] <= 1 for suggestion in payload["suggestions"])
    assert any("employee_dashboard" in suggestion["source_systems"] for suggestion in payload["suggestions"])
    assert any("recommendation_engine" in suggestion["source_systems"] for suggestion in payload["suggestions"])
    meeting = [suggestion for suggestion in payload["suggestions"] if suggestion["category"] == "meeting_reduction"][0]
    assert "Reduce meetings" in meeting["title"]
    assert "meeting" in meeting["action"].lower()

    crisis = client.post(
        "/api/v1/suggestions/generate",
        headers=headers,
        json={"scenario": "crisis", "sensitivity": 0.78, "feedback_weight": 0.4},
    )
    assert crisis.status_code == 200
    crisis_payload = crisis.json()
    assert crisis_payload["summary"]["average_impact"] >= payload["summary"]["average_impact"]
    assert crisis_payload["summary"]["critical"] >= payload["summary"]["critical"]
    crisis_titles = " ".join(suggestion["title"] for suggestion in crisis_payload["suggestions"])
    assert "Employee John" in crisis_titles
    assert "Reduce multitasking" in crisis_titles

    feedback = client.post(
        "/api/v1/suggestions/feedback",
        headers=headers,
        json={"suggestion_id": crisis_payload["suggestions"][0]["suggestion_id"], "accepted": True, "usefulness_score": 5},
    )
    assert feedback.status_code == 200
    assert feedback.json()["learning_signal"] == 1.0

    with client.stream("GET", "/api/v1/suggestions/stream", headers=headers) as response:
        assert response.status_code == 200
        first_chunk = next(response.iter_text())
        assert "event: suggestions" in first_chunk
        assert "Smart Decision Intelligence Engine" in first_chunk


def test_ai_business_prediction_engine_forecasts_scenarios_assistant_and_platform_audit() -> None:
    headers = auth_headers()
    baseline = client.get("/api/v1/business/prediction/default", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "Company Future Prediction AI - Business Forecast Ensemble"
    assert len(payload["revenue_forecast"]) == 12
    assert len(payload["churn_predictions"]) >= 3
    assert len(payload["employee_growth_forecast"]) >= 3
    assert len(payload["hiring_demand"]) >= 3
    assert len(payload["project_profitability"]) >= 3
    assert payload["summary"]["predicted_next_quarter_revenue"] > payload["summary"]["current_revenue"]
    assert payload["summary"]["annual_revenue_forecast"] > payload["summary"]["predicted_next_quarter_revenue"]
    assert 0 <= payload["summary"]["average_churn_probability"] <= 100
    assert 0 <= payload["company_health_forecast"]["score"] <= 100
    assert {"revenue_forecast_service", "client_churn_prediction_service", "scenario_simulation_engine", "ai_business_assistant"}.issubset(
        set(payload["source_systems"])
    )
    model_names = {item["model"] for item in payload["model_status"]}
    assert {"RandomForestRegressor", "XGBoost adapter", "Prophet adapter", "LSTM adapter"}.issubset(model_names)

    scenario = client.post(
        "/api/v1/business/prediction/forecast",
        headers=headers,
        json={
            "horizon_months": 12,
            "scenario": {
                "scenario_id": "test-revenue-drop",
                "scenario": "What happens if revenue drops by 20%?",
                "revenue_delta_percent": -20,
            },
        },
    )
    assert scenario.status_code == 200
    scenario_payload = scenario.json()
    assert scenario_payload["scenario_simulations"][0]["scenario_id"] == "test-revenue-drop"
    assert scenario_payload["scenario_simulations"][0]["financial_impact"] < 0
    assert scenario_payload["scenario_simulations"][0]["risk_impact"] > 0
    assert scenario_payload["revenue_forecast"][0]["revenue"] < payload["revenue_forecast"][0]["revenue"]

    assistant = client.post(
        "/api/v1/business/prediction/ask",
        headers=headers,
        json={"question": "Forecast next quarter revenue.", "horizon_months": 12},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["intent"] == "revenue"
    assert "Next-quarter revenue" in assistant_payload["answer"]
    assert assistant_payload["confidence"] > 0.7
    assert assistant_payload["cited_evidence"]

    with client.stream("GET", "/api/v1/business/prediction/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: business_prediction" in first_chunk
        assert "Company Future Prediction AI" in first_chunk

    platform = client.get("/api/v1/platform/operating-system", headers=headers)
    assert platform.status_code == 200
    platform_payload = platform.json()
    capabilities = {item["name"]: item for item in platform_payload["capabilities"]}
    assert "AI Business Prediction Engine" in capabilities
    assert "revenue_forecast_service" in capabilities["AI Business Prediction Engine"]["source_systems"]
    assert any(item == "Executive Forecast Command Center" for item in platform_payload["dashboards"])


def test_ai_shadow_company_mirrors_simulates_assists_and_streams() -> None:
    headers = auth_headers()

    baseline = client.get("/api/v1/shadow-company/default", headers=headers)
    assert baseline.status_code == 200
    payload = baseline.json()
    assert payload["model"] == "NEXUSMIND AI Shadow Company - Parallel Virtual Enterprise"
    assert payload["final_verdict"] == "AI SHADOW COMPANY COMPLETE"
    assert payload["summary"]["sync_completeness"] >= 95
    assert payload["summary"]["production_readiness_score"] >= 95
    assert payload["summary"]["innovation_score"] >= 95
    assert payload["summary"]["judge_wow_factor_score"] >= 95
    assert payload["real_company_state"]["employees"] > 0
    assert payload["shadow_company_state"]["employees"] == payload["real_company_state"]["employees"]
    assert payload["shadow_employees"]
    assert payload["shadow_projects"]
    assert payload["shadow_departments"]
    assert len(payload["future_states"]) == 4
    assert {item["case_name"] for item in payload["multi_reality_simulations"]} == {
        "best_case",
        "expected_case",
        "worst_case",
        "optimistic_case",
        "pessimistic_case",
        "ai_recommended_case",
    }
    assert payload["shadow_reality_visualization"]["status"] == "ready"
    assert payload["status_report"]["final_verdict"] == "AI SHADOW COMPANY COMPLETE"
    assert {"shadow_company_engine", "synchronization_engine", "enterprise_knowledge_brain", "organizational_brain"}.issubset(
        set(payload["source_systems"])
    )

    simulation = client.post(
        "/api/v1/shadow-company/simulate",
        headers=headers,
        json={
            "scenario_id": "test-shadow-client-loss",
            "scenario_name": "Top client leaves",
            "question": "What happens if we lose our top client?",
            "scenario_type": "client_loss",
            "horizon_months": 12,
            "employee_delta": 0,
            "workload_delta_percent": 8,
            "budget_delta_percent": -6,
            "revenue_delta_percent": -18,
            "client_loss_percent": 24,
            "target_department": "Customer Success",
            "target_market": "Global",
            "security_incident": False,
            "notes": "Integration test branch",
        },
    )
    assert simulation.status_code == 200
    simulation_payload = simulation.json()
    assert simulation_payload["final_verdict"] == "AI SHADOW COMPANY COMPLETE"
    assert simulation_payload["simulated_outcome"]["revenue"] < simulation_payload["baseline_outcome"]["revenue"]
    assert simulation_payload["simulated_outcome"]["risk_score"] > simulation_payload["baseline_outcome"]["risk_score"]
    assert len(simulation_payload["agent_contributions"]) >= 5
    assert len(simulation_payload["future_states"]) == 4
    assert len(simulation_payload["multi_reality_simulations"]) == 6
    assert any(signal["system"] == "Knowledge Brain Integration" for signal in simulation_payload["integration_signals"])
    assert any(signal["system"] == "Organizational Brain Integration" for signal in simulation_payload["integration_signals"])

    assistant = client.post(
        "/api/v1/shadow-company/assistant",
        headers=headers,
        json={"question": "Which decision produces the best outcome?", "horizon_months": 12},
    )
    assert assistant.status_code == 200
    assistant_payload = assistant.json()
    assert assistant_payload["final_verdict"] == "AI SHADOW COMPANY COMPLETE"
    assert "Shadow Company" in assistant_payload["answer"]
    assert assistant_payload["recommended_actions"]
    assert assistant_payload["cited_evidence"]

    workforce_reduction = client.post(
        "/api/v1/shadow-company/assistant",
        headers=headers,
        json={"question": "Should we reduce workforce by 20%?", "horizon_months": 12},
    )
    assert workforce_reduction.status_code == 200
    workforce_payload = workforce_reduction.json()
    workforce_simulation = workforce_payload["simulation"]
    assert workforce_simulation["scenario"]["scenario_type"] == "budget_reduction"
    assert workforce_simulation["scenario"]["employee_delta"] < 0
    assert workforce_simulation["simulated_outcome"]["employees"] < workforce_simulation["baseline_outcome"]["employees"]
    assert workforce_simulation["simulated_outcome"]["costs"] < workforce_simulation["baseline_outcome"]["costs"]
    assert workforce_simulation["simulated_outcome"]["risk_score"] > workforce_simulation["baseline_outcome"]["risk_score"]
    assert len(workforce_simulation["multi_reality_simulations"]) == 6

    with client.stream("GET", "/api/v1/shadow-company/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: ai_shadow_company" in first_chunk
        assert "AI SHADOW COMPANY COMPLETE" in first_chunk

    readiness = client.get("/api/v1/system/readiness")
    assert readiness.status_code == 200
    readiness_services = readiness.json()["services"]
    assert readiness_services["ai_shadow_company"] is True
    assert readiness_services["parallel_virtual_enterprise"] is True
    assert readiness_services["future_reality_simulation_engine"] is True
    assert readiness_services["shadow_company_synchronization_engine"] is True


def test_virtual_enterprise_universe_master_audit_connects_competition_platform() -> None:
    headers = auth_headers()

    response = client.get("/api/v1/virtual-enterprise-universe/verification", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "NEXUSMIND AI-Powered Virtual Enterprise Universe Master Auditor"
    assert payload["final_verdict"] == "AI-POWERED VIRTUAL ENTERPRISE UNIVERSE COMPLETE"
    assert payload["production_readiness_score"] >= 90
    assert payload["competition_readiness_score"] >= 90
    assert payload["judge_wow_factor_score"] >= 90
    assert payload["scorecard"]["minimum_score"] >= 90
    assert not payload["missing_features"]
    assert not payload["errors_found"]

    modules = {item["module"]: item for item in payload["module_audit"]}
    for module in [
        "AI CEO Assistant",
        "AI Memory System",
        "AI Organizational Brain",
        "AI Shadow Company",
        "AI Emotion Radar",
        "AI Crisis Simulator",
        "What-If Decision Engine",
        "Hidden Leader Detection",
        "Future Conflict Detection",
        "Real-Time Global Risk Scanner",
        "Autonomous AI Managers",
        "Enterprise Metaverse Control Room",
        "Digital Twins",
        "Knowledge Graph",
        "RAG System",
        "Forecasting Engine",
        "Simulation Engine",
        "Executive Dashboard",
    ]:
        assert modules[module]["status"] in {"complete", "working"}
        assert modules[module]["production_ready"] is True
        assert modules[module]["api_routes"]

    workflows = {item["name"]: item for item in payload["connectivity_workflows"]}
    assert "Global risk to executive decision loop" in workflows
    assert workflows["Global risk to executive decision loop"]["status"] == "connected"
    assert "Shadow Company" in workflows["Global risk to executive decision loop"]["chain"]
    assert "Shadow Company decision testing loop" in workflows
    assert all(item["status"] == "connected" for item in payload["digital_twin_audit"])
    assert {item["twin"] for item in payload["digital_twin_audit"]} == {"employee", "team", "department", "project", "client", "company"}
    assert len(payload["agent_ecosystem"]) >= 8
    assert len(payload["dashboard_audit"]) >= 8
    assert all(item["status"] in {"complete", "working"} for item in payload["security_audit"])
    assert all(item["status"] in {"complete", "working"} for item in payload["performance_audit"])

    with client.stream("GET", "/api/v1/virtual-enterprise-universe/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: virtual_enterprise_universe" in first_chunk
        assert "AI-POWERED VIRTUAL ENTERPRISE UNIVERSE COMPLETE" in first_chunk

    readiness = client.get("/api/v1/system/readiness")
    assert readiness.status_code == 200
    readiness_services = readiness.json()["services"]
    assert readiness_services["ai_powered_virtual_enterprise_universe"] is True
    assert readiness_services["virtual_enterprise_universe_master_auditor"] is True
    assert readiness_services["competition_readiness_auditor"] is True


def test_judge_winning_innovation_stack_verifies_integrated_competition_claims() -> None:
    headers = auth_headers()

    response = client.get("/api/v1/judge-winning-innovation-stack/verification", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "NEXUSMIND Judge-Winning Innovation Stack Verifier"
    assert payload["final_verdict"] == "JUDGE-WINNING INNOVATION STACK COMPLETE"
    assert payload["production_readiness_score"] >= 90
    assert payload["innovation_score"] >= 90
    assert payload["research_score"] >= 90
    assert payload["startup_potential_score"] >= 90
    assert payload["judge_wow_factor_score"] >= 90
    assert payload["scorecard"]["minimum_score"] >= 90
    assert not payload["missing_components"]
    assert not payload["errors_found"]

    expected_pillars = {
        "Artificial Intelligence",
        "Predictive Analytics",
        "Enterprise Simulations",
        "Multi-Agent Systems",
        "Digital Twin Technology",
        "Self-Learning Intelligence",
        "Real-Time Analytics",
        "Futuristic User Experience",
        "Enterprise Problem Solving",
        "Connected Ecosystem Integration",
    }
    pillars = {item["capability"]: item for item in payload["capability_audit"]}
    assert expected_pillars == set(pillars)
    for item in pillars.values():
        assert item["status"] in {"complete", "working"}
        assert item["score"] >= 90
        assert item["production_ready"] is True
        assert item["dynamic_outputs"] is True
        assert item["api_routes"]

    assert all(item["status"] == "connected" for item in payload["integration_workflows"])
    assert all(item["status"] in {"complete", "working"} for item in payload["enterprise_problem_solving"])
    assert len(payload["competition_comparison"]) == 5
    assert all(item["status"] in {"complete", "working"} for item in payload["performance_metrics"])
    assert "Autonomous Enterprise Intelligence Platform" in payload["final_answer"]

    with client.stream("GET", "/api/v1/judge-winning-innovation-stack/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: judge_winning_innovation_stack" in first_chunk
        assert "JUDGE-WINNING INNOVATION STACK COMPLETE" in first_chunk

    readiness = client.get("/api/v1/system/readiness")
    assert readiness.status_code == 200
    readiness_services = readiness.json()["services"]
    assert readiness_services["judge_winning_innovation_stack"] is True
    assert readiness_services["innovation_stack_verifier"] is True
    assert readiness_services["competition_innovation_stack_auditor"] is True


def test_judge_demo_mode_executes_cinematic_competition_sequence() -> None:
    headers = auth_headers()

    response = client.get("/api/v1/judge-demo-mode/default", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "NEXUSMIND Judge Demo Mode - Cinematic Enterprise Simulation OS"
    assert payload["headline"] == "Ask The Future Of The Company"
    assert payload["final_verdict"] == "NEXUSMIND AI COMPLETE"
    assert payload["production_readiness_score"] >= 90
    assert payload["innovation_score"] >= 90
    assert payload["judge_wow_factor_score"] >= 90
    assert payload["demo_readiness_score"] >= 90
    assert not payload["errors_found"]
    impossible = payload["impossible_moment"]
    assert impossible["scenario_question"] == "What happens if 30 engineers resign tomorrow?"
    assert impossible["one_button_label"] == "Show The Future"
    assert impossible["judge_understands_in_seconds"] <= 30
    assert len(impossible["visual_transformations"]) >= 4
    assert any(item["severity"] == "critical" for item in impossible["visual_transformations"])
    assert len(impossible["agent_council"]) >= 4
    assert {stage["title"] for stage in impossible["shadow_company"]} == {"Real Company", "Shadow Company", "Future Company"}
    assert impossible["executive_recommendations"]

    steps = {step["title"]: step for step in payload["demo_sequence"]}
    for title in [
        "Ask The Future Of The Company",
        "Update Company Digital Twin",
        "Run Resignation Shock Simulation",
        "Show Emotion Radar",
        "Show AI Agent Council",
        "Run Workforce Crisis Simulation",
        "Show Shadow Company Branch",
        "Show AI Memory and Organizational Brain",
        "Show Final AI Recommendation",
    ]:
        assert steps[title]["status"] == "complete"
        assert steps[title]["api_routes"]
        assert steps[title]["output"]

    features = {item["feature"]: item for item in payload["feature_status"]}
    for feature in [
        "Live AI CEO Assistant",
        "Live Company Digital Twin",
        "Shadow Company AI",
        "What-If AI Engine",
        "AI Emotion Radar",
        "Multi-Agent AI Managers",
        "AI Memory System",
        "Organizational Brain",
        "Crisis Simulator",
        "Global Risk Scanner",
        "Self-Learning AI",
        "Metaverse Control Room",
        "Final Demo Mode",
    ]:
        assert features[feature]["status"] == "complete"

    with client.stream("GET", "/api/v1/judge-demo-mode/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: judge_demo_mode" in first_chunk
        assert "NEXUSMIND AI COMPLETE" in first_chunk

    readiness = client.get("/api/v1/system/readiness")
    assert readiness.status_code == 200
    readiness_services = readiness.json()["services"]
    assert readiness_services["judge_demo_mode"] is True
    assert readiness_services["cinematic_competition_demo"] is True
    assert readiness_services["ai_powered_enterprise_simulation_os"] is True


def test_ultimate_feature_coverage_audits_groups_a_to_p_and_integrations() -> None:
    headers = auth_headers()

    response = client.get("/api/v1/ultimate-feature-coverage/audit", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "NEXUSMIND Ultimate Feature Coverage Auditor - A-P"
    assert payload["platform_positioning"] == "Autonomous Enterprise Intelligence & Digital Twin Platform"
    assert payload["final_verdict"] == "NEXUSMIND AI COMPLETE"
    assert payload["overall_coverage_percent"] >= 95
    assert payload["ai_innovation_score"] >= 90
    assert payload["technical_complexity_score"] >= 90
    assert payload["research_score"] >= 90
    assert payload["startup_potential_score"] >= 90
    assert payload["enterprise_readiness_score"] >= 90
    assert payload["judge_wow_factor_score"] >= 90
    assert not payload["missing_components"]
    assert not payload["integration_issues_found"]

    groups = {item["group_key"]: item for item in payload["feature_status_table"]}
    assert set(groups) == set("ABCDEFGHIJKLMNOP")
    expected_groups = {
        "A": "Live AI Digital CEO",
        "B": "Live Company Simulation",
        "C": "What If AI Engine",
        "D": "Shadow Company AI",
        "E": "Digital Twin Platform",
        "F": "AI Emotion Radar",
        "G": "Future Conflict Prediction",
        "H": "Hidden Leader Detection",
        "I": "Multi Agent AI Managers",
        "J": "AI Memory System",
        "K": "Organizational Brain",
        "L": "Crisis Simulator",
        "M": "Global Risk Scanner",
        "N": "Self Learning AI",
        "O": "Metaverse Control Room",
        "P": "Cinematic Executive UI",
    }
    for key, feature_group in expected_groups.items():
        item = groups[key]
        assert item["feature_group"] == feature_group
        assert item["status"] in {"present", "fixed"}
        assert item["present"] is True
        assert item["coverage_percent"] >= 95
        assert item["production_ready"] is True
        assert item["required_capabilities"]
        assert item["backend_systems"]
        assert item["frontend_surfaces"]
        assert item["api_routes"]
        assert item["integration_links"]
        assert item["evidence"]

    workflows = {item["name"]: item for item in payload["integration_workflows"]}
    assert "Global risk to executive command loop" in workflows
    assert "Strategic what-if to Shadow Company loop" in workflows
    assert "Metaverse visualization loop" in workflows
    assert all(item["status"] == "connected" for item in workflows.values())
    assert all(item["chain"] for item in workflows.values())
    assert payload["new_components_added"]
    assert payload["fixed_components"]
    assert "30 seconds" in payload["demo_wow_factor_assessment"]

    with client.stream("GET", "/api/v1/ultimate-feature-coverage/stream", headers=headers) as stream:
        assert stream.status_code == 200
        first_chunk = next(stream.iter_text())
        assert "event: ultimate_feature_coverage" in first_chunk
        assert "NEXUSMIND AI COMPLETE" in first_chunk

    readiness = client.get("/api/v1/system/readiness")
    assert readiness.status_code == 200
    readiness_services = readiness.json()["services"]
    assert readiness_services["ultimate_feature_coverage_auditor"] is True
    assert readiness_services["feature_groups_a_to_p_auditor"] is True
    assert readiness_services["autonomous_enterprise_intelligence_digital_twin_platform"] is True
