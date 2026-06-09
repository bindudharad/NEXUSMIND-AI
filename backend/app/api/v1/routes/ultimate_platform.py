from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.ultimate_platform import UltimatePlatformResponse
from app.services.ultimate_platform_service import ultimate_platform_service

router = APIRouter()


@router.get("/verification", response_model=UltimatePlatformResponse)
def ultimate_platform_verification(_: EnterpriseUser = Depends(get_current_user)) -> UltimatePlatformResponse:
    return ultimate_platform_service.verify()


@router.get("/stream")
def ultimate_platform_stream(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(ultimate_platform_service.stream(), media_type="text/event-stream")
