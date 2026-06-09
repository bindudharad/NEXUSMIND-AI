import json

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user, get_user_from_token
from app.models.user import EnterpriseUser
from app.schemas.power_features import (
    GNNTeamRelationResponse,
    ManagerAssistantRequest,
    ManagerAssistantResponse,
    PowerFeatureAuditResponse,
    RealtimeAnalyticsResponse,
    XAIExplanationRequest,
    XAIExplanationResponse,
)
from app.services.power_feature_service import power_feature_service

router = APIRouter()


@router.get("/audit", response_model=PowerFeatureAuditResponse)
def power_feature_audit(_: EnterpriseUser = Depends(get_current_user)) -> PowerFeatureAuditResponse:
    return power_feature_service.audit()


@router.get("/realtime/snapshot", response_model=RealtimeAnalyticsResponse)
def realtime_snapshot(_: EnterpriseUser = Depends(get_current_user)) -> RealtimeAnalyticsResponse:
    return power_feature_service.realtime_snapshot()


@router.get("/realtime/stream")
def realtime_stream(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(power_feature_service.realtime_stream(), media_type="text/event-stream")


@router.websocket("/realtime/ws")
async def realtime_websocket(websocket: WebSocket, token: str | None = Query(default=None)) -> None:
    await websocket.accept()
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return
    try:
        get_user_from_token(token)
    except HTTPException:
        await websocket.close(code=1008, reason="Invalid authentication token")
        return
    try:
        for sequence, mode in enumerate(["default", "pressure", "crisis"], start=1):
            snapshot = power_feature_service.realtime_snapshot(sequence=sequence, mode=mode)
            await websocket.send_text(json.dumps(snapshot.model_dump(mode="json")))
        await websocket.close()
    except WebSocketDisconnect:
        return


@router.post("/xai/explain", response_model=XAIExplanationResponse)
def explain_prediction(
    payload: XAIExplanationRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> XAIExplanationResponse:
    return power_feature_service.explain(payload)


@router.get("/gnn/team-relations", response_model=GNNTeamRelationResponse)
def graph_team_relations(_: EnterpriseUser = Depends(get_current_user)) -> GNNTeamRelationResponse:
    return power_feature_service.graph_relations()


@router.post("/assistant/ask", response_model=ManagerAssistantResponse)
def ask_manager_assistant(
    payload: ManagerAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> ManagerAssistantResponse:
    return power_feature_service.ask_manager(payload)
