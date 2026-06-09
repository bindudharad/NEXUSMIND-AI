from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.smart_interviewer import (
    SmartInterviewAssistantRequest,
    SmartInterviewAssistantResponse,
    SmartInterviewRequest,
    SmartInterviewerResponse,
)
from app.services.smart_interviewer_service import smart_interviewer_service

router = APIRouter()


@router.get("/default", response_model=SmartInterviewerResponse)
def default_smart_interviewer(_: EnterpriseUser = Depends(get_current_user)) -> SmartInterviewerResponse:
    return smart_interviewer_service.run()


@router.post("/run", response_model=SmartInterviewerResponse)
def run_smart_interviewer(
    payload: SmartInterviewRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> SmartInterviewerResponse:
    return smart_interviewer_service.run(payload)


@router.post("/assistant", response_model=SmartInterviewAssistantResponse)
def ask_smart_interviewer(
    payload: SmartInterviewAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> SmartInterviewAssistantResponse:
    return smart_interviewer_service.ask(payload)


@router.get("/stream")
def stream_smart_interviewer(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(smart_interviewer_service.stream(), media_type="text/event-stream")
