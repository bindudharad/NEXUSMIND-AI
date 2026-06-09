from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.unified_enterprise import UnifiedEnterpriseResponse
from app.services.unified_enterprise_service import unified_enterprise_service

router = APIRouter()


@router.get("/verification", response_model=UnifiedEnterpriseResponse)
def unified_enterprise_verification(_: EnterpriseUser = Depends(get_current_user)) -> UnifiedEnterpriseResponse:
    return unified_enterprise_service.verify()


@router.get("/stream")
def unified_enterprise_stream(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(unified_enterprise_service.stream(), media_type="text/event-stream")
