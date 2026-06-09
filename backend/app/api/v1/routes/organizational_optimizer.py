from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.organizational_optimizer import (
    OrganizationalAssistantRequest,
    OrganizationalAssistantResponse,
    OrganizationalOptimizerRequest,
    OrganizationalOptimizerResponse,
    OrganizationalSimulationRequest,
)
from app.services.organizational_optimizer_service import organizational_optimizer_service

router = APIRouter()


@router.get("/default", response_model=OrganizationalOptimizerResponse)
def default_organizational_optimizer(_: EnterpriseUser = Depends(get_current_user)) -> OrganizationalOptimizerResponse:
    return organizational_optimizer_service.default()


@router.post("/analyze", response_model=OrganizationalOptimizerResponse)
def analyze_organizational_optimizer(
    payload: OrganizationalOptimizerRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> OrganizationalOptimizerResponse:
    return organizational_optimizer_service.analyze(payload)


@router.post("/simulate", response_model=OrganizationalOptimizerResponse)
def simulate_organizational_design(
    payload: OrganizationalSimulationRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> OrganizationalOptimizerResponse:
    return organizational_optimizer_service.simulate(payload)


@router.post("/assistant", response_model=OrganizationalAssistantResponse)
def ask_organizational_optimizer(
    payload: OrganizationalAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> OrganizationalAssistantResponse:
    return organizational_optimizer_service.ask(payload)


@router.get("/stream")
def stream_organizational_optimizer(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(organizational_optimizer_service.stream(), media_type="text/event-stream")
