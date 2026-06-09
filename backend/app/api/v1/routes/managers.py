from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.manager_dashboard import ManagerDashboardRequest, ManagerDashboardResponse
from app.services.manager_dashboard_service import manager_dashboard_service

router = APIRouter()


@router.get("/dashboard/default", response_model=ManagerDashboardResponse)
def default_manager_dashboard(_: EnterpriseUser = Depends(get_current_user)) -> ManagerDashboardResponse:
    return manager_dashboard_service.analyze()


@router.post("/dashboard/analyze", response_model=ManagerDashboardResponse)
def analyze_manager_dashboard(
    payload: ManagerDashboardRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> ManagerDashboardResponse:
    return manager_dashboard_service.analyze(payload)
