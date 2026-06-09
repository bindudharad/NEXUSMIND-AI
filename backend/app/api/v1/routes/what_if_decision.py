from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.what_if_decision import (
    WhatIfAssistantRequest,
    WhatIfAssistantResponse,
    WhatIfDecisionDashboardResponse,
    WhatIfScenarioRecord,
    WhatIfScenarioRequest,
    WhatIfSimulationResponse,
)
from app.services.what_if_decision_service import what_if_decision_engine_service

router = APIRouter()


@router.get("/default", response_model=WhatIfDecisionDashboardResponse)
def default_what_if_decision_engine(
    _: EnterpriseUser = Depends(get_current_user),
) -> WhatIfDecisionDashboardResponse:
    return what_if_decision_engine_service.default()


@router.get("/scenarios", response_model=list[WhatIfScenarioRequest])
def list_what_if_scenarios(_: EnterpriseUser = Depends(get_current_user)) -> list[WhatIfScenarioRequest]:
    return what_if_decision_engine_service.scenarios()


@router.post("/scenarios", response_model=WhatIfScenarioRecord)
def create_what_if_scenario(
    payload: WhatIfScenarioRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> WhatIfScenarioRecord:
    return what_if_decision_engine_service.create_scenario(payload)


@router.post("/simulate", response_model=WhatIfSimulationResponse)
def simulate_what_if_scenario(
    payload: WhatIfScenarioRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> WhatIfSimulationResponse:
    return what_if_decision_engine_service.simulate(payload)


@router.post("/ask", response_model=WhatIfAssistantResponse)
def ask_what_if_assistant(
    payload: WhatIfAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> WhatIfAssistantResponse:
    return what_if_decision_engine_service.ask(payload)


@router.get("/stream")
def stream_what_if_decision_engine(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(what_if_decision_engine_service.stream(), media_type="text/event-stream")
