from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.judge_impact import JudgeImpactValidationResponse
from app.services.judge_impact_service import judge_impact_service

router = APIRouter()


@router.get("/validation", response_model=JudgeImpactValidationResponse)
def judge_impact_validation(_: EnterpriseUser = Depends(get_current_user)) -> JudgeImpactValidationResponse:
    return judge_impact_service.validate()


@router.get("/stream")
def judge_impact_stream(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(judge_impact_service.stream(), media_type="text/event-stream")
