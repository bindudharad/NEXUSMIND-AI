from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.wellness import WellnessAnalysisResponse, WellnessAnalyzeRequest
from app.services.wellness_service import wellness_intelligence_service

router = APIRouter()


@router.get("/default", response_model=WellnessAnalysisResponse)
def default_wellness_analysis(_: EnterpriseUser = Depends(get_current_user)) -> WellnessAnalysisResponse:
    return wellness_intelligence_service.analyze()


@router.post("/analyze", response_model=WellnessAnalysisResponse)
def analyze_wellness(
    payload: WellnessAnalyzeRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> WellnessAnalysisResponse:
    return wellness_intelligence_service.analyze(payload)


@router.get("/stream")
def stream_wellness_analysis(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(wellness_intelligence_service.stream(), media_type="text/event-stream")
