from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.living_company_brain import (
    LivingCompanyBrainAnswerResponse,
    LivingCompanyBrainAskRequest,
    LivingCompanyBrainResponse,
)
from app.services.living_company_brain_service import living_company_brain_service

router = APIRouter()


@router.get("/default", response_model=LivingCompanyBrainResponse)
def default_living_company_brain(_: EnterpriseUser = Depends(get_current_user)) -> LivingCompanyBrainResponse:
    return living_company_brain_service.default()


@router.post("/ask", response_model=LivingCompanyBrainAnswerResponse)
def ask_living_company_brain(
    payload: LivingCompanyBrainAskRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> LivingCompanyBrainAnswerResponse:
    return living_company_brain_service.ask(payload)


@router.get("/stream")
def stream_living_company_brain(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(living_company_brain_service.stream(), media_type="text/event-stream")
