from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.company_emotion_map import (
    CompanyEmotionMapRequest,
    CompanyEmotionMapResponse,
    EmotionAssistantRequest,
    EmotionAssistantResponse,
)
from app.services.company_emotion_map_service import company_emotion_map_service

router = APIRouter()


@router.get("/default", response_model=CompanyEmotionMapResponse)
def default_company_emotion_map(_: EnterpriseUser = Depends(get_current_user)) -> CompanyEmotionMapResponse:
    return company_emotion_map_service.default()


@router.post("/analyze", response_model=CompanyEmotionMapResponse)
def analyze_company_emotion_map(
    payload: CompanyEmotionMapRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> CompanyEmotionMapResponse:
    return company_emotion_map_service.analyze(payload)


@router.post("/assistant", response_model=EmotionAssistantResponse)
def ask_company_emotion_map(
    payload: EmotionAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> EmotionAssistantResponse:
    return company_emotion_map_service.ask(payload)


@router.get("/stream")
def stream_company_emotion_map(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(company_emotion_map_service.stream(), media_type="text/event-stream")
