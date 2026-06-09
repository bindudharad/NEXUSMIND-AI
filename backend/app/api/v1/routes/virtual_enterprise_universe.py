from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.virtual_enterprise_universe import VirtualEnterpriseUniverseResponse
from app.services.virtual_enterprise_universe_service import virtual_enterprise_universe_service

router = APIRouter()


@router.get("/verification", response_model=VirtualEnterpriseUniverseResponse)
def virtual_enterprise_universe_verification(
    _: EnterpriseUser = Depends(get_current_user),
) -> VirtualEnterpriseUniverseResponse:
    return virtual_enterprise_universe_service.verify()


@router.get("/stream")
def virtual_enterprise_universe_stream(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(virtual_enterprise_universe_service.stream(), media_type="text/event-stream")
