from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.decision_assistant import DecisionAssistantRequest, DecisionAssistantResponse
from app.services.decision_assistant_service import decision_assistant_service

router = APIRouter()


@router.get("/default", response_model=DecisionAssistantResponse)
def default_decision_assistant(_: EnterpriseUser = Depends(get_current_user)) -> DecisionAssistantResponse:
    return decision_assistant_service.recommend()


@router.post("/recommend", response_model=DecisionAssistantResponse)
def recommend_decision_route(
    payload: DecisionAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> DecisionAssistantResponse:
    return decision_assistant_service.recommend(payload)


@router.get("/stream")
def stream_decision_assistant(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(decision_assistant_service.stream(), media_type="text/event-stream")
