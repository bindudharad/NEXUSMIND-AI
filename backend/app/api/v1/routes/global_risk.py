from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.global_risk import (
    GlobalRiskAssistantRequest,
    GlobalRiskAssistantResponse,
    GlobalRiskScannerRequest,
    GlobalRiskScannerResponse,
)
from app.services.global_risk_service import global_risk_scanner_service

router = APIRouter()


@router.get("/default", response_model=GlobalRiskScannerResponse)
def default_global_risk_scanner(_: EnterpriseUser = Depends(get_current_user)) -> GlobalRiskScannerResponse:
    return global_risk_scanner_service.default()


@router.post("/scan", response_model=GlobalRiskScannerResponse)
def scan_global_risks(
    payload: GlobalRiskScannerRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> GlobalRiskScannerResponse:
    return global_risk_scanner_service.analyze(payload)


@router.post("/assistant", response_model=GlobalRiskAssistantResponse)
def ask_global_risk_assistant(
    payload: GlobalRiskAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> GlobalRiskAssistantResponse:
    return global_risk_scanner_service.ask(payload)


@router.get("/stream")
def stream_global_risk_scanner(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(global_risk_scanner_service.stream(), media_type="text/event-stream")
