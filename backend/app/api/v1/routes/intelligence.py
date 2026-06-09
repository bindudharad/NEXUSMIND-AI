from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.intelligence import (
    AgentCouncilResponse,
    BurnoutPredictionRequest,
    BurnoutPredictionResponse,
    DigitalTwinSnapshotResponse,
    IntelligenceOverview,
    KnowledgeAnswer,
    KnowledgeQueryRequest,
    ModelValidationResponse,
    OrgBrainResponse,
    SecurityAnalysisRequest,
    SecurityAnalysisResponse,
    ScenarioDecisionSuiteResponse,
    ScenarioSimulationRequest,
    ScenarioSimulationResponse,
    SimulationRequest,
    SimulationResponse,
    WorkflowOptimizationRequest,
    WorkflowOptimizationResponse,
)
from app.services.intelligence_service import intelligence_service

router = APIRouter()


@router.get("/overview", response_model=IntelligenceOverview)
def intelligence_overview(_: EnterpriseUser = Depends(get_current_user)) -> IntelligenceOverview:
    return intelligence_service.get_overview()


@router.post("/burnout/predict", response_model=BurnoutPredictionResponse)
def predict_burnout(
    payload: BurnoutPredictionRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> BurnoutPredictionResponse:
    return intelligence_service.predict_burnout(payload)


@router.get("/models/validation", response_model=ModelValidationResponse)
def validate_models(_: EnterpriseUser = Depends(get_current_user)) -> ModelValidationResponse:
    return intelligence_service.validate_models()


@router.post("/digital-twin/simulate", response_model=SimulationResponse)
def simulate_digital_twin(
    payload: SimulationRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> SimulationResponse:
    return intelligence_service.simulate(payload)


@router.get("/digital-twin/company", response_model=DigitalTwinSnapshotResponse)
def digital_twin_company(
    _: EnterpriseUser = Depends(get_current_user),
) -> DigitalTwinSnapshotResponse:
    return intelligence_service.digital_twin_snapshot()


@router.post("/scenario/simulate", response_model=ScenarioSimulationResponse)
def simulate_enterprise_scenario(
    payload: ScenarioSimulationRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> ScenarioSimulationResponse:
    return intelligence_service.simulate_enterprise_scenario(payload)


@router.get("/scenario/decision-suite", response_model=ScenarioDecisionSuiteResponse)
def scenario_decision_suite(
    _: EnterpriseUser = Depends(get_current_user),
) -> ScenarioDecisionSuiteResponse:
    return intelligence_service.scenario_decision_suite()


@router.get("/agents/council", response_model=AgentCouncilResponse)
def agent_council(_: EnterpriseUser = Depends(get_current_user)) -> AgentCouncilResponse:
    return intelligence_service.run_agent_council("enterprise risk")


@router.post("/knowledge/query", response_model=KnowledgeAnswer)
def query_knowledge(
    payload: KnowledgeQueryRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> KnowledgeAnswer:
    return intelligence_service.query_knowledge(payload.question)


@router.post("/security/analyze", response_model=SecurityAnalysisResponse)
def analyze_security(
    payload: SecurityAnalysisRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> SecurityAnalysisResponse:
    return intelligence_service.analyze_security(payload)


@router.post("/workflow/optimize", response_model=WorkflowOptimizationResponse)
def optimize_workflow(
    payload: WorkflowOptimizationRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> WorkflowOptimizationResponse:
    return intelligence_service.optimize_workflow(payload)


@router.get("/org-brain", response_model=OrgBrainResponse)
def org_brain(_: EnterpriseUser = Depends(get_current_user)) -> OrgBrainResponse:
    return intelligence_service.get_org_brain()
