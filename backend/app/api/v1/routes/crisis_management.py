from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.crisis_management import (
    CrisisAssistantRequest,
    CrisisAssistantResponse,
    CrisisCommandCenterRequest,
    CrisisCommandCenterResponse,
    CrisisScenarioBuilderRequest,
    CrisisScenarioBuilderResponse,
    CrisisSimulationRequest,
)
from app.services.crisis_management_service import crisis_management_service

router = APIRouter()


@router.get("/default", response_model=CrisisCommandCenterResponse)
def default_crisis_command_center(_: EnterpriseUser = Depends(get_current_user)) -> CrisisCommandCenterResponse:
    return crisis_management_service.default()


@router.post("/analyze", response_model=CrisisCommandCenterResponse)
def analyze_crisis_command_center(
    payload: CrisisCommandCenterRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> CrisisCommandCenterResponse:
    return crisis_management_service.analyze(payload)


@router.post("/simulate", response_model=CrisisCommandCenterResponse)
def simulate_crisis_command_center(
    payload: CrisisSimulationRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> CrisisCommandCenterResponse:
    return crisis_management_service.simulate(payload)


@router.post("/scenarios", response_model=CrisisScenarioBuilderResponse)
def build_crisis_scenario(
    payload: CrisisScenarioBuilderRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> CrisisScenarioBuilderResponse:
    return crisis_management_service.build_scenario(payload)


@router.post("/assistant", response_model=CrisisAssistantResponse)
def ask_crisis_assistant(
    payload: CrisisAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> CrisisAssistantResponse:
    return crisis_management_service.ask(payload)


@router.get("/stream")
async def stream_crisis_command_center(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(crisis_management_service.stream(), media_type="text/event-stream")
