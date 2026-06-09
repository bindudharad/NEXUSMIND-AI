from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.business_prediction import (
    BusinessAssistantRequest,
    BusinessAssistantResponse,
    BusinessPredictionRequest,
    BusinessPredictionResponse,
)
from app.services.business_prediction_service import business_prediction_service

router = APIRouter()


@router.get("/default", response_model=BusinessPredictionResponse)
def default_business_prediction(_: EnterpriseUser = Depends(get_current_user)) -> BusinessPredictionResponse:
    return business_prediction_service.analyze()


@router.post("/forecast", response_model=BusinessPredictionResponse)
def forecast_business_future(
    payload: BusinessPredictionRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> BusinessPredictionResponse:
    return business_prediction_service.analyze(payload)


@router.post("/ask", response_model=BusinessAssistantResponse)
def ask_business_assistant(
    payload: BusinessAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> BusinessAssistantResponse:
    return business_prediction_service.ask(payload)


@router.get("/stream")
def stream_business_prediction(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(business_prediction_service.stream(), media_type="text/event-stream")
