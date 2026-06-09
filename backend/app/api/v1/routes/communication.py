from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.communication import CommunicationRequest, CommunicationResponse
from app.services.communication_service import communication_quality_service

router = APIRouter()


@router.get("/default", response_model=CommunicationResponse)
def default_communication_quality(_: EnterpriseUser = Depends(get_current_user)) -> CommunicationResponse:
    return communication_quality_service.analyze()


@router.post("/analyze", response_model=CommunicationResponse)
def analyze_communication_quality(
    payload: CommunicationRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> CommunicationResponse:
    return communication_quality_service.analyze(payload)


@router.get("/stream")
def stream_communication_quality(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(communication_quality_service.stream(), media_type="text/event-stream")
