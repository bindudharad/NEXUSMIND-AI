from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.research_grade import ResearchGradePlatformResponse
from app.services.research_grade_service import research_grade_platform_service

router = APIRouter()


@router.get("/verification", response_model=ResearchGradePlatformResponse)
def research_grade_verification(_: EnterpriseUser = Depends(get_current_user)) -> ResearchGradePlatformResponse:
    return research_grade_platform_service.verify()


@router.get("/stream")
def research_grade_stream(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(research_grade_platform_service.stream(), media_type="text/event-stream")
