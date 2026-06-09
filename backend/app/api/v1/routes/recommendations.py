from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.recommendations import (
    RecommendationFeedbackRequest,
    RecommendationFeedbackResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.recommendation_service import recommendation_service

router = APIRouter()


@router.post("/generate", response_model=RecommendationResponse)
def generate_recommendations(
    payload: RecommendationRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> RecommendationResponse:
    return recommendation_service.generate(payload)


@router.get("/default", response_model=RecommendationResponse)
def default_recommendations(_: EnterpriseUser = Depends(get_current_user)) -> RecommendationResponse:
    return recommendation_service.generate()


@router.post("/feedback", response_model=RecommendationFeedbackResponse)
def recommendation_feedback(
    payload: RecommendationFeedbackRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> RecommendationFeedbackResponse:
    return recommendation_service.record_feedback(payload)
