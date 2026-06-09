from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.hiring import HiringAnalyzeRequest, HiringResponse
from app.services.hiring_service import hiring_intelligence_service

router = APIRouter()


@router.get("/default", response_model=HiringResponse)
def default_hiring(_: EnterpriseUser = Depends(get_current_user)) -> HiringResponse:
    return hiring_intelligence_service.analyze()


@router.post("/analyze", response_model=HiringResponse)
def analyze_hiring(
    payload: HiringAnalyzeRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> HiringResponse:
    return hiring_intelligence_service.analyze(payload)


@router.get("/stream")
def stream_hiring(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(hiring_intelligence_service.stream(), media_type="text/event-stream")
