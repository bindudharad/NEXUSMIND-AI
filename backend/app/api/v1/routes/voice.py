from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.voice import VoiceCommandRequest, VoiceCommandResponse, VoiceStressAnalyzeRequest, VoiceStressResponse
from app.services.voice_service import voice_stress_service

router = APIRouter()


@router.get("/default", response_model=VoiceStressResponse)
def default_voice_stress(_: EnterpriseUser = Depends(get_current_user)) -> VoiceStressResponse:
    return voice_stress_service.analyze()


@router.post("/analyze", response_model=VoiceStressResponse)
def analyze_voice_stress(
    payload: VoiceStressAnalyzeRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> VoiceStressResponse:
    try:
        return voice_stress_service.analyze(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/command", response_model=VoiceCommandResponse)
def execute_voice_command(
    payload: VoiceCommandRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> VoiceCommandResponse:
    return voice_stress_service.execute_command(payload)


@router.get("/copilot/default", response_model=VoiceCommandResponse)
def default_voice_copilot(_: EnterpriseUser = Depends(get_current_user)) -> VoiceCommandResponse:
    return voice_stress_service.execute_command(
        VoiceCommandRequest(transcript="Show biggest company threat.", speaker="CEO", department="Executive")
    )


@router.get("/stream")
def stream_voice_stress(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(voice_stress_service.stream(), media_type="text/event-stream")


@router.get("/copilot/stream")
def stream_voice_copilot(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(voice_stress_service.copilot_stream(), media_type="text/event-stream")
