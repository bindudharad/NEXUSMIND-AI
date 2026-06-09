from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.team_compatibility import TeamCompatibilityRequest, TeamCompatibilityResponse
from app.services.team_compatibility_service import team_compatibility_service

router = APIRouter()


@router.get("/default", response_model=TeamCompatibilityResponse)
def default_team_compatibility(_: EnterpriseUser = Depends(get_current_user)) -> TeamCompatibilityResponse:
    return team_compatibility_service.analyze()


@router.post("/analyze", response_model=TeamCompatibilityResponse)
def analyze_team_compatibility(
    payload: TeamCompatibilityRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> TeamCompatibilityResponse:
    return team_compatibility_service.analyze(payload)


@router.get("/stream")
def stream_team_compatibility(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(team_compatibility_service.stream(), media_type="text/event-stream")
