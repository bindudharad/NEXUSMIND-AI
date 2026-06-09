from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.roi import RoiResponse, RoiScenarioRequest
from app.services.roi_service import roi_intelligence_service

router = APIRouter()


@router.get("/default", response_model=RoiResponse)
def default_roi(_: EnterpriseUser = Depends(get_current_user)) -> RoiResponse:
    return roi_intelligence_service.analyze()


@router.post("/analyze", response_model=RoiResponse)
def analyze_roi(
    payload: RoiScenarioRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> RoiResponse:
    return roi_intelligence_service.analyze(payload)


@router.get("/stream")
def stream_roi(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(roi_intelligence_service.stream(), media_type="text/event-stream")
