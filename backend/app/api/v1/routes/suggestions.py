from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.suggestions import (
    SmartSuggestionFeedbackRequest,
    SmartSuggestionFeedbackResponse,
    SmartSuggestionRequest,
    SmartSuggestionResponse,
)
from app.services.suggestion_service import smart_suggestion_service

router = APIRouter()


@router.get("/feed", response_model=SmartSuggestionResponse)
def suggestion_feed(_: EnterpriseUser = Depends(get_current_user)) -> SmartSuggestionResponse:
    return smart_suggestion_service.generate()


@router.post("/generate", response_model=SmartSuggestionResponse)
def generate_suggestions(
    payload: SmartSuggestionRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> SmartSuggestionResponse:
    return smart_suggestion_service.generate(payload)


@router.post("/feedback", response_model=SmartSuggestionFeedbackResponse)
def suggestion_feedback(
    payload: SmartSuggestionFeedbackRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> SmartSuggestionFeedbackResponse:
    return smart_suggestion_service.record_feedback(payload)


@router.get("/stream")
def stream_suggestions(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(smart_suggestion_service.stream(), media_type="text/event-stream")
