from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.boardroom import (
    BoardroomAssistantRequest,
    BoardroomAssistantResponse,
    BoardroomDashboardResponse,
)
from app.services.boardroom_service import boardroom_dashboard_service


router = APIRouter()


@router.get("/default", response_model=BoardroomDashboardResponse)
def boardroom_dashboard(_: EnterpriseUser = Depends(get_current_user)) -> BoardroomDashboardResponse:
    return boardroom_dashboard_service.default()


@router.post("/assistant", response_model=BoardroomAssistantResponse)
def boardroom_assistant(
    payload: BoardroomAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> BoardroomAssistantResponse:
    return boardroom_dashboard_service.ask(payload)


@router.get("/stream")
def boardroom_stream(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(boardroom_dashboard_service.stream(), media_type="text/event-stream")
