from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.learning import LearningRequest, LearningResponse
from app.services.learning_service import learning_service

router = APIRouter()


@router.get("/default", response_model=LearningResponse)
def default_learning(_: EnterpriseUser = Depends(get_current_user)) -> LearningResponse:
    return learning_service.recommend()


@router.post("/recommend", response_model=LearningResponse)
def recommend_learning(
    payload: LearningRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> LearningResponse:
    return learning_service.recommend(payload)


@router.get("/stream")
def stream_learning(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(learning_service.stream(), media_type="text/event-stream")
