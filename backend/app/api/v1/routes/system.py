from fastapi import APIRouter

from app.ai.anomaly_detector import anomaly_detector
from app.ai.employee_analytics_engine import employee_analytics_engine
from app.ai.manager_analytics_engine import manager_analytics_engine
from app.ai.model_registry import model_registry
from app.ai.enterprise_models import enterprise_model_registry
from app.ai.graph_relation_engine import graph_relation_engine
from app.ai.hiring_engine import hiring_intelligence_engine
from app.ai.nlp_engine import nlp_emotion_engine
from app.ai.project_failure_engine import project_failure_engine
from app.ai.recommendation_engine import recommendation_engine
from app.ai.roi_engine import roi_intelligence_engine
from app.ai.time_series_engine import time_series_forecaster
from app.ai.team_compatibility_engine import team_compatibility_engine
from app.ai.voice_stress_engine import voice_stress_engine
from app.core.config import settings
from app.schemas.feature_coverage import FeatureCoverageResponse
from app.schemas.technology_stack import TechnologyStackResponse
from app.services.advanced_feature_service import advanced_feature_service
from app.services.boardroom_service import boardroom_dashboard_service
from app.services.company_emotion_map_service import company_emotion_map_service
from app.services.crisis_management_service import crisis_management_service
from app.services.enterprise_os_service import enterprise_os_service
from app.services.enterprise_metaverse_service import enterprise_metaverse_service
from app.services.enterprise_knowledge_service import enterprise_knowledge_service
from app.services.feature_coverage_service import feature_coverage_service
from app.services.global_risk_service import global_risk_scanner_service
from app.services.hidden_leader_service import hidden_leader_detection_service
from app.services.innovation_service import innovation_scoring_service
from app.services.judge_impact_service import judge_impact_service
from app.services.judge_demo_mode_service import judge_demo_mode_service
from app.services.judge_innovation_stack_service import judge_winning_innovation_stack_service
from app.services.living_company_brain_service import living_company_brain_service
from app.services.multi_agent_workforce_service import multi_agent_workforce_service
from app.services.organizational_brain_service import organizational_brain_service
from app.services.organizational_optimizer_service import organizational_optimizer_service
from app.services.power_feature_service import power_feature_service
from app.services.platform_service import platform_service
from app.services.recruiter_impression_service import recruiter_impression_service
from app.services.research_grade_service import research_grade_platform_service
from app.services.self_learning_ai_service import self_learning_ai_service
from app.services.shadow_company_service import ai_shadow_company_service
from app.services.strategic_intelligence_service import strategic_intelligence_service
from app.services.team_builder_service import team_builder_service
from app.services.technology_stack_service import technology_stack_service
from app.services.time_machine_service import company_time_machine_service
from app.services.ultimate_feature_coverage_service import ultimate_feature_coverage_service
from app.services.ultimate_platform_service import ultimate_platform_service
from app.services.unified_enterprise_service import unified_enterprise_service
from app.services.virtual_employee_service import virtual_employee_workforce_service
from app.services.virtual_enterprise_universe_service import virtual_enterprise_universe_service
from app.services.voice_service import voice_stress_service
from app.services.what_if_decision_service import what_if_decision_engine_service

router = APIRouter()


@router.get("/readiness")
def readiness() -> dict[str, object]:
    return {
        "status": "ready",
        "environment": settings.environment,
        "services": {
            "postgres_configured": bool(settings.postgres_dsn),
            "mongo_configured": bool(settings.mongo_uri),
            "redis_configured": bool(settings.redis_url),
            "qdrant_configured": bool(settings.qdrant_url),
            "burnout_model_artifact": model_registry.burnout_classifier_available,
            "enterprise_model_suite": enterprise_model_registry.available,
            "nlp_emotion_model": nlp_emotion_engine.available,
            "time_series_forecaster": time_series_forecaster.available,
            "recommendation_engine": recommendation_engine.available,
            "anomaly_detector": anomaly_detector.available,
            "employee_analytics_engine": employee_analytics_engine.available,
            "smart_hiring_ai": hiring_intelligence_engine.available,
            "manager_analytics_engine": manager_analytics_engine.available,
            "ai_alert_correlator": True,
            "smart_suggestion_engine": True,
            "advanced_feature_auditor": True,
            "meeting_analyzer": True,
            "voice_stress_detector": voice_stress_engine.available,
            "voice_controlled_enterprise_ai": bool(voice_stress_service.command_model_name),
            "team_compatibility_ai": team_compatibility_engine.available,
            "ai_team_builder": bool(team_builder_service.model_name) and team_compatibility_engine.available and graph_relation_engine.available,
            "project_failure_predictor": project_failure_engine.available,
            "roi_intelligence_engine": roi_intelligence_engine.available,
            "recruiter_impression_auditor": bool(recruiter_impression_service.model_name),
            "realtime_power_analytics": bool(power_feature_service.realtime_model),
            "explainable_ai_engine": bool(power_feature_service.xai_model),
            "graph_neural_network_team_relations": graph_relation_engine.available,
            "generative_manager_assistant": bool(power_feature_service.assistant_model),
            "enterprise_os_auditor": bool(enterprise_os_service.model_name),
            "complete_platform_operating_system": bool(platform_service.model_name),
            "strategic_intelligence_system": bool(strategic_intelligence_service.model_name),
            "ai_company_time_machine": bool(company_time_machine_service.model_name),
            "what_if_decision_engine": bool(what_if_decision_engine_service.model_name),
            "enterprise_strategy_simulator": bool(what_if_decision_engine_service.model_name),
            "virtual_employee_generator": bool(virtual_employee_workforce_service.model_name),
            "enterprise_metaverse_control_room": bool(enterprise_metaverse_service.model_name),
            "ai_shadow_company": bool(ai_shadow_company_service.model_name),
            "parallel_virtual_enterprise": bool(ai_shadow_company_service.model_name),
            "future_reality_simulation_engine": bool(ai_shadow_company_service.model_name),
            "shadow_company_synchronization_engine": bool(ai_shadow_company_service.model_name),
            "company_emotion_map": bool(company_emotion_map_service.model_name),
            "ai_innovation_detector": bool(innovation_scoring_service.model_name),
            "hidden_leader_detection_system": bool(hidden_leader_detection_service.model_name),
            "talent_intelligence_system": bool(hidden_leader_detection_service.model_name),
            "ai_that_finds_hidden_leaders": bool(hidden_leader_detection_service.model_name),
            "realtime_global_risk_scanner": bool(global_risk_scanner_service.model_name),
            "enterprise_external_intelligence_platform": bool(global_risk_scanner_service.model_name),
            "global_risk_alerting_engine": bool(global_risk_scanner_service.model_name),
            "ai_memory_system": bool(enterprise_knowledge_service.model_name),
            "enterprise_knowledge_brain": bool(enterprise_knowledge_service.model_name),
            "enterprise_rag_system": bool(enterprise_knowledge_service.model_name),
            "knowledge_graph_engine": bool(enterprise_knowledge_service.model_name),
            "expertise_discovery_engine": bool(enterprise_knowledge_service.model_name),
            "ai_boardroom_dashboard": bool(boardroom_dashboard_service.model_name),
            "ai_organizational_structure_optimizer": bool(organizational_optimizer_service.model_name),
            "ai_organizational_brain": bool(organizational_brain_service.model_name),
            "gnn_based_organizational_intelligence": bool(organizational_brain_service.model_name),
            "realtime_crisis_management_ai": bool(crisis_management_service.model_name),
            "multi_agent_ai_workforce": bool(multi_agent_workforce_service.model_name),
            "judge_impact_validation": bool(judge_impact_service.model_name),
            "judge_demo_mode": bool(judge_demo_mode_service.model_name),
            "cinematic_competition_demo": bool(judge_demo_mode_service.model_name),
            "ai_powered_enterprise_simulation_os": bool(judge_demo_mode_service.model_name),
            "judge_winning_innovation_stack": bool(judge_winning_innovation_stack_service.model_name),
            "innovation_stack_verifier": bool(judge_winning_innovation_stack_service.model_name),
            "competition_innovation_stack_auditor": bool(judge_winning_innovation_stack_service.model_name),
            "ultimate_feature_coverage_auditor": bool(ultimate_feature_coverage_service.model_name),
            "feature_groups_a_to_p_auditor": bool(ultimate_feature_coverage_service.model_name),
            "autonomous_enterprise_intelligence_digital_twin_platform": bool(ultimate_feature_coverage_service.model_name),
            "living_ai_company_brain": bool(living_company_brain_service.model_name),
            "living_company_brain_integration_layer": bool(living_company_brain_service.model_name),
            "unified_autonomous_enterprise_system": bool(unified_enterprise_service.model_name),
            "ai_powered_virtual_enterprise_universe": bool(virtual_enterprise_universe_service.model_name),
            "virtual_enterprise_universe_master_auditor": bool(virtual_enterprise_universe_service.model_name),
            "competition_readiness_auditor": bool(virtual_enterprise_universe_service.model_name),
            "self_learning_company_ai": bool(self_learning_ai_service.model_name),
            "self_evolving_ai_system": bool(self_learning_ai_service.model_name),
            "ultimate_autonomous_enterprise_platform": bool(ultimate_platform_service.model_name),
            "research_grade_autonomous_enterprise_platform": bool(research_grade_platform_service.model_name),
        },
    }


@router.get("/technology-stack", response_model=TechnologyStackResponse)
def technology_stack() -> TechnologyStackResponse:
    return technology_stack_service.verify()


@router.get("/feature-coverage", response_model=FeatureCoverageResponse)
def feature_coverage() -> FeatureCoverageResponse:
    return feature_coverage_service.verify()


@router.get("/advanced-features", response_model=FeatureCoverageResponse)
def advanced_features() -> FeatureCoverageResponse:
    return advanced_feature_service.verify()


@router.get("/enterprise-ai-features", response_model=FeatureCoverageResponse)
def enterprise_ai_features() -> FeatureCoverageResponse:
    return enterprise_os_service.verify()
