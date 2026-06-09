from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.self_learning_ai import (
    SelfLearningAIResponse,
    SelfLearningAssistantRequest,
    SelfLearningAssistantResponse,
    SelfLearningFeedbackRequest,
    SelfLearningFeedbackResponse,
)
from app.services.self_learning_ai_service import self_learning_ai_service

router = APIRouter()


@router.get("/verification", response_model=SelfLearningAIResponse)
def self_learning_verification(_: EnterpriseUser = Depends(get_current_user)) -> SelfLearningAIResponse:
    return self_learning_ai_service.verify()


@router.post("/feedback", response_model=SelfLearningFeedbackResponse)
def self_learning_feedback(
    payload: SelfLearningFeedbackRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> SelfLearningFeedbackResponse:
    return self_learning_ai_service.record_feedback(payload)


@router.post("/demo", response_model=SelfLearningAIResponse)
def self_learning_demo(_: EnterpriseUser = Depends(get_current_user)) -> SelfLearningAIResponse:
    return self_learning_ai_service.run_demo()


@router.post("/assistant", response_model=SelfLearningAssistantResponse)
def self_learning_assistant(
    payload: SelfLearningAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> SelfLearningAssistantResponse:
    return self_learning_ai_service.ask(payload)


@router.get("/stream")
def self_learning_stream(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(self_learning_ai_service.stream(), media_type="text/event-stream")
