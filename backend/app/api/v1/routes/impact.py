from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.impact import EnterpriseImpactResponse
from app.services.impact_service import enterprise_impact_service

router = APIRouter()


@router.get("/summary", response_model=EnterpriseImpactResponse)
def enterprise_impact_summary(_: EnterpriseUser = Depends(get_current_user)) -> EnterpriseImpactResponse:
    return enterprise_impact_service.summary()
