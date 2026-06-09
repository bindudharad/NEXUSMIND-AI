from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.time_machine import (
    TimeMachineAssistantRequest,
    TimeMachineAssistantResponse,
    TimeMachineDashboardResponse,
    TimeMachineScenarioRecord,
    TimeMachineScenarioRequest,
    TimeMachineSimulationResponse,
)
from app.services.time_machine_service import company_time_machine_service

router = APIRouter()


@router.get("/default", response_model=TimeMachineDashboardResponse)
def default_time_machine(_: EnterpriseUser = Depends(get_current_user)) -> TimeMachineDashboardResponse:
    return company_time_machine_service.default()


@router.get("/scenarios", response_model=list[TimeMachineScenarioRequest])
def list_time_machine_scenarios(_: EnterpriseUser = Depends(get_current_user)) -> list[TimeMachineScenarioRequest]:
    return company_time_machine_service.scenarios()


@router.post("/scenarios", response_model=TimeMachineScenarioRecord)
def create_time_machine_scenario(
    payload: TimeMachineScenarioRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> TimeMachineScenarioRecord:
    return company_time_machine_service.create_scenario(payload)


@router.post("/simulate", response_model=TimeMachineSimulationResponse)
def simulate_time_machine(
    payload: TimeMachineScenarioRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> TimeMachineSimulationResponse:
    return company_time_machine_service.simulate(payload)


@router.post("/ask", response_model=TimeMachineAssistantResponse)
def ask_time_machine(
    payload: TimeMachineAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> TimeMachineAssistantResponse:
    return company_time_machine_service.ask(payload)


@router.get("/stream")
def stream_time_machine(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(company_time_machine_service.stream(), media_type="text/event-stream")
