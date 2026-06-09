from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.organizational_brain import (
    OrganizationalBrainAssistantRequest,
    OrganizationalBrainAssistantResponse,
    OrganizationalBrainRequest,
    OrganizationalBrainResponse,
)
from app.services.organizational_brain_service import organizational_brain_service

router = APIRouter()


@router.get("/default", response_model=OrganizationalBrainResponse)
def default_organizational_brain(_: EnterpriseUser = Depends(get_current_user)) -> OrganizationalBrainResponse:
    return organizational_brain_service.default()


@router.post("/analyze", response_model=OrganizationalBrainResponse)
def analyze_organizational_brain(
    payload: OrganizationalBrainRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> OrganizationalBrainResponse:
    return organizational_brain_service.analyze(payload)


@router.post("/assistant", response_model=OrganizationalBrainAssistantResponse)
def ask_organizational_brain(
    payload: OrganizationalBrainAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> OrganizationalBrainAssistantResponse:
    return organizational_brain_service.ask(payload)


@router.get("/stream")
def stream_organizational_brain(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(organizational_brain_service.stream(), media_type="text/event-stream")
