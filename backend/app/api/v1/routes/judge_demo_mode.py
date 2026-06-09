from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.judge_demo_mode import JudgeDemoModeResponse
from app.services.judge_demo_mode_service import judge_demo_mode_service

router = APIRouter()


@router.get("/default", response_model=JudgeDemoModeResponse)
def judge_demo_mode_default(_: EnterpriseUser = Depends(get_current_user)) -> JudgeDemoModeResponse:
    return judge_demo_mode_service.default()


@router.get("/stream")
def judge_demo_mode_stream(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(judge_demo_mode_service.stream(), media_type="text/event-stream")
