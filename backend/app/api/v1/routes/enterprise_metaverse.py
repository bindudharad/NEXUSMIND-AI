from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.enterprise_metaverse import (
    EnterpriseMetaverseControlRoomResponse,
    MetaverseControlRoomRequest,
    MetaverseSimulationRequest,
    MetaverseVoiceCommandRequest,
    MetaverseVoiceNavigationResponse,
)
from app.services.enterprise_metaverse_service import enterprise_metaverse_service

router = APIRouter()


@router.get("/default", response_model=EnterpriseMetaverseControlRoomResponse)
def default_enterprise_metaverse(_: EnterpriseUser = Depends(get_current_user)) -> EnterpriseMetaverseControlRoomResponse:
    return enterprise_metaverse_service.default()


@router.post("/run", response_model=EnterpriseMetaverseControlRoomResponse)
def run_enterprise_metaverse(
    payload: MetaverseControlRoomRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> EnterpriseMetaverseControlRoomResponse:
    return enterprise_metaverse_service.run(payload)


@router.post("/simulate", response_model=EnterpriseMetaverseControlRoomResponse)
def simulate_enterprise_metaverse(
    payload: MetaverseSimulationRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> EnterpriseMetaverseControlRoomResponse:
    return enterprise_metaverse_service.simulate(payload)


@router.post("/voice", response_model=MetaverseVoiceNavigationResponse)
def navigate_enterprise_metaverse(
    payload: MetaverseVoiceCommandRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> MetaverseVoiceNavigationResponse:
    return enterprise_metaverse_service.navigate(payload)


@router.get("/stream")
def stream_enterprise_metaverse(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(enterprise_metaverse_service.stream(), media_type="text/event-stream")
