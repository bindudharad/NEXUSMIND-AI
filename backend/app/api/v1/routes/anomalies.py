from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.anomaly import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    AnomalyFeedbackRequest,
    AnomalyFeedbackResponse,
)
from app.services.anomaly_service import anomaly_service

router = APIRouter()


@router.post("/detect", response_model=AnomalyDetectionResponse)
def detect_anomalies(
    payload: AnomalyDetectionRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> AnomalyDetectionResponse:
    return anomaly_service.detect(payload)


@router.get("/default", response_model=AnomalyDetectionResponse)
def default_anomalies(_: EnterpriseUser = Depends(get_current_user)) -> AnomalyDetectionResponse:
    return anomaly_service.detect()


@router.post("/feedback", response_model=AnomalyFeedbackResponse)
def anomaly_feedback(
    payload: AnomalyFeedbackRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> AnomalyFeedbackResponse:
    return anomaly_service.record_feedback(payload)


@router.get("/stream")
def anomaly_stream(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(anomaly_service.stream(), media_type="text/event-stream")
