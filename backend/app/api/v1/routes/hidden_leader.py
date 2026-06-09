from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.hidden_leader import (
    HiddenLeaderAssistantRequest,
    HiddenLeaderAssistantResponse,
    HiddenLeaderDetectionResponse,
    HiddenLeaderRequest,
)
from app.services.hidden_leader_service import hidden_leader_detection_service

router = APIRouter()


@router.get("/default", response_model=HiddenLeaderDetectionResponse)
def default_hidden_leader_detection(_: EnterpriseUser = Depends(get_current_user)) -> HiddenLeaderDetectionResponse:
    return hidden_leader_detection_service.default()


@router.post("/analyze", response_model=HiddenLeaderDetectionResponse)
def analyze_hidden_leaders(
    payload: HiddenLeaderRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> HiddenLeaderDetectionResponse:
    return hidden_leader_detection_service.analyze(payload)


@router.post("/assistant", response_model=HiddenLeaderAssistantResponse)
def ask_hidden_leader_assistant(
    payload: HiddenLeaderAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> HiddenLeaderAssistantResponse:
    return hidden_leader_detection_service.ask(payload)


@router.get("/stream")
def stream_hidden_leader_detection(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(hidden_leader_detection_service.stream(), media_type="text/event-stream")
