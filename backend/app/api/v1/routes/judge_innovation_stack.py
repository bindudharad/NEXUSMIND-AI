from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.judge_innovation_stack import JudgeWinningInnovationStackResponse
from app.services.judge_innovation_stack_service import judge_winning_innovation_stack_service

router = APIRouter()


@router.get("/verification", response_model=JudgeWinningInnovationStackResponse)
def verify_judge_winning_innovation_stack(_: EnterpriseUser = Depends(get_current_user)) -> JudgeWinningInnovationStackResponse:
    return judge_winning_innovation_stack_service.verify()


@router.get("/stream")
def stream_judge_winning_innovation_stack(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(judge_winning_innovation_stack_service.stream(), media_type="text/event-stream")
