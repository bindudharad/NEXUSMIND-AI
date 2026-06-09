from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.compensation import CompensationRequest, CompensationResponse
from app.services.compensation_service import compensation_service

router = APIRouter()


@router.get("/default", response_model=CompensationResponse)
def default_compensation(_: EnterpriseUser = Depends(get_current_user)) -> CompensationResponse:
    return compensation_service.analyze()


@router.post("/recommend", response_model=CompensationResponse)
def recommend_compensation(
    payload: CompensationRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> CompensationResponse:
    return compensation_service.analyze(payload)


@router.get("/stream")
def stream_compensation(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(compensation_service.stream(), media_type="text/event-stream")
