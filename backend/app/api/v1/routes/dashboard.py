from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.dashboard import DashboardOverview
from app.services.dashboard_service import dashboard_service

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
def overview(_: EnterpriseUser = Depends(get_current_user)) -> DashboardOverview:
    return dashboard_service.get_overview()
