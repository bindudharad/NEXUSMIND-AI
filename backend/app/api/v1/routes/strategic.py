from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.strategic import StrategicDecisionRequest, StrategicDecisionResponse, StrategicIntelligenceRequest, StrategicIntelligenceResponse
from app.services.strategic_intelligence_service import strategic_intelligence_service

router = APIRouter()


@router.get("/enterprise", response_model=StrategicIntelligenceResponse)
def enterprise_strategic_intelligence(_: EnterpriseUser = Depends(get_current_user)) -> StrategicIntelligenceResponse:
    return strategic_intelligence_service.analyze()


@router.post("/enterprise", response_model=StrategicIntelligenceResponse)
def analyze_strategic_intelligence(
    payload: StrategicIntelligenceRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> StrategicIntelligenceResponse:
    return strategic_intelligence_service.analyze(payload)


@router.get("/decision-engine/default", response_model=StrategicDecisionResponse)
def default_strategic_decision_engine(_: EnterpriseUser = Depends(get_current_user)) -> StrategicDecisionResponse:
    return strategic_intelligence_service.decide()


@router.post("/decision-engine/ask", response_model=StrategicDecisionResponse)
def ask_strategic_decision_engine(
    payload: StrategicDecisionRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> StrategicDecisionResponse:
    return strategic_intelligence_service.decide(payload)


@router.get("/stream")
def stream_strategic_intelligence(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(strategic_intelligence_service.stream(), media_type="text/event-stream")


@router.get("/decision-engine/stream")
def stream_strategic_decision_engine(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(strategic_intelligence_service.decision_stream(), media_type="text/event-stream")
