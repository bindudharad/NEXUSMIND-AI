from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.forecasting import ForecastRequest, ForecastResponse
from app.services.forecasting_service import forecasting_service

router = APIRouter()


@router.post("/workload", response_model=ForecastResponse)
def forecast_workload(payload: ForecastRequest, _: EnterpriseUser = Depends(get_current_user)) -> ForecastResponse:
    return forecasting_service.forecast(payload)


@router.get("/workload/default", response_model=ForecastResponse)
def default_workload_forecast(_: EnterpriseUser = Depends(get_current_user)) -> ForecastResponse:
    return forecasting_service.forecast(ForecastRequest())
