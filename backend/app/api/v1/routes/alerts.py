from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.alerts import AlertAckRequest, AlertAckResponse, AlertDetectionRequest, AlertFeedResponse
from app.services.alert_service import alert_service

router = APIRouter()


@router.get("/feed", response_model=AlertFeedResponse)
def alert_feed(_: EnterpriseUser = Depends(get_current_user)) -> AlertFeedResponse:
    return alert_service.feed()


@router.post("/detect", response_model=AlertFeedResponse)
def detect_alerts(
    payload: AlertDetectionRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> AlertFeedResponse:
    return alert_service.feed(payload)


@router.post("/acknowledge", response_model=AlertAckResponse)
def acknowledge_alert(
    payload: AlertAckRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> AlertAckResponse:
    return alert_service.acknowledge(payload)


@router.get("/stream")
def stream_alerts(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(alert_service.stream(), media_type="text/event-stream")
