from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.platform import CompletePlatformResponse, EcosystemAuditResponse
from app.services.platform_service import platform_service

router = APIRouter()


@router.get("/operating-system", response_model=CompletePlatformResponse)
def complete_operating_system(_: EnterpriseUser = Depends(get_current_user)) -> CompletePlatformResponse:
    return platform_service.operating_system()


@router.get("/ecosystem-audit", response_model=EcosystemAuditResponse)
def ecosystem_audit(_: EnterpriseUser = Depends(get_current_user)) -> EcosystemAuditResponse:
    return platform_service.ecosystem_audit()
