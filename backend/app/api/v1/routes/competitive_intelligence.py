from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.competitive_intelligence import (
    CompetitiveAssistantRequest,
    CompetitiveAssistantResponse,
    CompetitiveIntelligenceRequest,
    CompetitiveIntelligenceResponse,
)
from app.services.competitive_intelligence_service import competitive_intelligence_service

router = APIRouter()


@router.get("/default", response_model=CompetitiveIntelligenceResponse)
def default_competitive_intelligence(_: EnterpriseUser = Depends(get_current_user)) -> CompetitiveIntelligenceResponse:
    return competitive_intelligence_service.analyze()


@router.post("/analyze", response_model=CompetitiveIntelligenceResponse)
def analyze_competitive_intelligence(
    payload: CompetitiveIntelligenceRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> CompetitiveIntelligenceResponse:
    return competitive_intelligence_service.analyze(payload)


@router.post("/assistant", response_model=CompetitiveAssistantResponse)
def ask_competitive_assistant(
    payload: CompetitiveAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> CompetitiveAssistantResponse:
    return competitive_intelligence_service.ask(payload)


@router.get("/stream")
def stream_competitive_intelligence(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(competitive_intelligence_service.stream(), media_type="text/event-stream")
