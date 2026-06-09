from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.company_simulation_lab import (
    CompanySimulationAssistantRequest,
    CompanySimulationAssistantResponse,
    CompanySimulationLabRequest,
    CompanySimulationLabResponse,
    CompanySimulationScenarioRequest,
)
from app.services.company_simulation_lab_service import company_simulation_lab_service

router = APIRouter()


@router.get("/default", response_model=CompanySimulationLabResponse)
def default_company_simulation_lab(_: EnterpriseUser = Depends(get_current_user)) -> CompanySimulationLabResponse:
    return company_simulation_lab_service.run()


@router.post("/run", response_model=CompanySimulationLabResponse)
def run_company_simulation_lab(
    payload: CompanySimulationLabRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> CompanySimulationLabResponse:
    return company_simulation_lab_service.run(payload)


@router.post("/simulate", response_model=CompanySimulationLabResponse)
def simulate_company_decision(
    payload: CompanySimulationScenarioRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> CompanySimulationLabResponse:
    return company_simulation_lab_service.simulate(payload)


@router.post("/assistant", response_model=CompanySimulationAssistantResponse)
def ask_company_simulation_assistant(
    payload: CompanySimulationAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> CompanySimulationAssistantResponse:
    return company_simulation_lab_service.ask(payload)


@router.get("/stream")
def stream_company_simulation_lab(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(company_simulation_lab_service.stream(), media_type="text/event-stream")
