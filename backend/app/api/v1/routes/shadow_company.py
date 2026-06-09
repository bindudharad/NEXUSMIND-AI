from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.shadow_company import (
    ShadowCompanyAssistantRequest,
    ShadowCompanyAssistantResponse,
    ShadowCompanyDashboardResponse,
    ShadowDecisionSimulationRequest,
    ShadowDecisionSimulationResponse,
)
from app.services.shadow_company_service import ai_shadow_company_service

router = APIRouter()


@router.get("/default", response_model=ShadowCompanyDashboardResponse)
def default_shadow_company(_: EnterpriseUser = Depends(get_current_user)) -> ShadowCompanyDashboardResponse:
    return ai_shadow_company_service.default()


@router.post("/simulate", response_model=ShadowDecisionSimulationResponse)
def simulate_shadow_company(
    payload: ShadowDecisionSimulationRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> ShadowDecisionSimulationResponse:
    return ai_shadow_company_service.simulate(payload)


@router.post("/assistant", response_model=ShadowCompanyAssistantResponse)
def ask_shadow_company_assistant(
    payload: ShadowCompanyAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> ShadowCompanyAssistantResponse:
    return ai_shadow_company_service.ask(payload)


@router.get("/stream")
def stream_shadow_company(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(ai_shadow_company_service.stream(), media_type="text/event-stream")
