from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.team_builder import TeamBuilderRequest, TeamBuilderResponse
from app.services.team_builder_service import team_builder_service

router = APIRouter()


@router.get("/default", response_model=TeamBuilderResponse)
def default_team_builder(_: EnterpriseUser = Depends(get_current_user)) -> TeamBuilderResponse:
    return team_builder_service.build()


@router.post("/generate", response_model=TeamBuilderResponse)
def generate_team_builder(
    payload: TeamBuilderRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> TeamBuilderResponse:
    return team_builder_service.build(payload)


@router.get("/stream")
def stream_team_builder(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(team_builder_service.stream(), media_type="text/event-stream")
