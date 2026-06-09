from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.recruiter_impression import RecruiterImpressionResponse
from app.services.recruiter_impression_service import recruiter_impression_service

router = APIRouter()


@router.get("/summary", response_model=RecruiterImpressionResponse)
def recruiter_impression_summary(_: EnterpriseUser = Depends(get_current_user)) -> RecruiterImpressionResponse:
    return recruiter_impression_service.verify()


@router.get("/stream")
def recruiter_impression_stream(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(recruiter_impression_service.stream(), media_type="text/event-stream")
