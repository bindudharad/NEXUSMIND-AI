from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.virtual_employee import (
    VirtualEmployeeAssistantRequest,
    VirtualEmployeeGenerationRequest,
    VirtualWorkforceAssistantResponse,
    VirtualWorkforceResponse,
    WorkforceSimulationRequest,
)
from app.services.virtual_employee_service import virtual_employee_workforce_service

router = APIRouter()


@router.get("/default", response_model=VirtualWorkforceResponse)
def default_virtual_workforce(_: EnterpriseUser = Depends(get_current_user)) -> VirtualWorkforceResponse:
    return virtual_employee_workforce_service.default()


@router.post("/generate", response_model=VirtualWorkforceResponse)
def generate_virtual_employees(
    payload: VirtualEmployeeGenerationRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> VirtualWorkforceResponse:
    return virtual_employee_workforce_service.generate(payload)


@router.post("/simulate", response_model=VirtualWorkforceResponse)
def simulate_virtual_workforce(
    payload: WorkforceSimulationRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> VirtualWorkforceResponse:
    return virtual_employee_workforce_service.simulate(payload)


@router.post("/ask", response_model=VirtualWorkforceAssistantResponse)
def ask_virtual_workforce(
    payload: VirtualEmployeeAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> VirtualWorkforceAssistantResponse:
    return virtual_employee_workforce_service.ask(payload)


@router.get("/stream")
async def stream_virtual_workforce(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(virtual_employee_workforce_service.stream(), media_type="text/event-stream")
