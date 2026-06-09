from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.employee_dashboard import EmployeeDashboardRequest, EmployeeDashboardResponse
from app.services.employee_dashboard_service import employee_dashboard_service

router = APIRouter()


@router.get("/dashboard/default", response_model=EmployeeDashboardResponse)
def default_employee_dashboard(_: EnterpriseUser = Depends(get_current_user)) -> EmployeeDashboardResponse:
    return employee_dashboard_service.analyze()


@router.post("/dashboard/analyze", response_model=EmployeeDashboardResponse)
def analyze_employee_dashboard(
    payload: EmployeeDashboardRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> EmployeeDashboardResponse:
    return employee_dashboard_service.analyze(payload)
