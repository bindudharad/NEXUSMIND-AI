from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.company_health import CompanyHealthRequest, CompanyHealthResponse
from app.services.company_health_service import company_health_service

router = APIRouter()


@router.get("/default", response_model=CompanyHealthResponse)
def default_company_health(_: EnterpriseUser = Depends(get_current_user)) -> CompanyHealthResponse:
    return company_health_service.analyze()


@router.post("/analyze", response_model=CompanyHealthResponse)
def analyze_company_health(
    payload: CompanyHealthRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> CompanyHealthResponse:
    return company_health_service.analyze(payload)


@router.get("/stream")
def stream_company_health(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(company_health_service.stream(), media_type="text/event-stream")
