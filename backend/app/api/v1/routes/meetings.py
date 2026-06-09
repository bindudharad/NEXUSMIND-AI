from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.meetings import MeetingAnalysisResponse, MeetingAnalyzeRequest
from app.services.meeting_service import meeting_analyzer_service

router = APIRouter()


@router.get("/default", response_model=MeetingAnalysisResponse)
def default_meeting_analysis(_: EnterpriseUser = Depends(get_current_user)) -> MeetingAnalysisResponse:
    return meeting_analyzer_service.analyze()


@router.post("/analyze", response_model=MeetingAnalysisResponse)
def analyze_meeting(
    payload: MeetingAnalyzeRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> MeetingAnalysisResponse:
    return meeting_analyzer_service.analyze(payload)


@router.get("/stream")
def stream_meeting_analysis(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(meeting_analyzer_service.stream(), media_type="text/event-stream")
