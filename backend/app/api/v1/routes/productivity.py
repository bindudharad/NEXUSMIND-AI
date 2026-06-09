from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.productivity import ProductivityAnalysisResponse, ProductivityAnalyzeRequest
from app.services.productivity_service import productivity_leakage_service

router = APIRouter()


@router.get("/default", response_model=ProductivityAnalysisResponse)
def default_productivity_leakage(_: EnterpriseUser = Depends(get_current_user)) -> ProductivityAnalysisResponse:
    return productivity_leakage_service.analyze()


@router.post("/analyze", response_model=ProductivityAnalysisResponse)
def analyze_productivity_leakage(
    payload: ProductivityAnalyzeRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> ProductivityAnalysisResponse:
    return productivity_leakage_service.analyze(payload)


@router.get("/stream")
def stream_productivity_leakage(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(productivity_leakage_service.stream(), media_type="text/event-stream")
