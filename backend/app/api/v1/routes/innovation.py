from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.innovation import InnovationAssistantRequest, InnovationAssistantResponse, InnovationRequest, InnovationResponse
from app.services.innovation_service import innovation_scoring_service

router = APIRouter()


@router.get("/default", response_model=InnovationResponse)
def default_innovation_scoring(_: EnterpriseUser = Depends(get_current_user)) -> InnovationResponse:
    return innovation_scoring_service.score()


@router.post("/score", response_model=InnovationResponse)
def score_innovation(
    payload: InnovationRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> InnovationResponse:
    return innovation_scoring_service.score(payload)


@router.post("/assistant", response_model=InnovationAssistantResponse)
def ask_innovation_detector(
    payload: InnovationAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> InnovationAssistantResponse:
    return innovation_scoring_service.ask(payload)


@router.get("/stream")
def stream_innovation(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(innovation_scoring_service.stream(), media_type="text/event-stream")
