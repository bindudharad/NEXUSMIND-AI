from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.multi_agent_workforce import (
    AgentCouncilRequest,
    AgentCouncilResponseV2,
    AgentProfile,
    AgentSimulationRequest,
    AgentWorkforceRequest,
    MultiAgentWorkforceResponse,
)
from app.services.multi_agent_workforce_service import multi_agent_workforce_service

router = APIRouter()


@router.get("/default", response_model=MultiAgentWorkforceResponse)
def default_multi_agent_workforce(_: EnterpriseUser = Depends(get_current_user)) -> MultiAgentWorkforceResponse:
    return multi_agent_workforce_service.default()


@router.post("/run", response_model=MultiAgentWorkforceResponse)
def run_multi_agent_workforce(
    payload: AgentWorkforceRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> MultiAgentWorkforceResponse:
    return multi_agent_workforce_service.run(payload)


@router.post("/ask", response_model=AgentCouncilResponseV2)
def ask_multi_agent_council(
    payload: AgentCouncilRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> AgentCouncilResponseV2:
    return multi_agent_workforce_service.ask(payload)


@router.post("/simulate", response_model=MultiAgentWorkforceResponse)
def simulate_multi_agent_workforce(
    payload: AgentSimulationRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> MultiAgentWorkforceResponse:
    return multi_agent_workforce_service.simulate(payload)


@router.get("/stream")
async def stream_multi_agent_workforce(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(multi_agent_workforce_service.stream(), media_type="text/event-stream")


@router.get("/{agent_slug}", response_model=AgentProfile)
def get_agent_profile(
    agent_slug: str,
    _: EnterpriseUser = Depends(get_current_user),
) -> AgentProfile:
    normalized = agent_slug.strip().lower()
    for agent in multi_agent_workforce_service.default().agents:
        if agent.name.lower().split()[0] == normalized or agent.agent_id.removeprefix("agent-") == normalized:
            return agent
    raise HTTPException(status_code=404, detail="Agent profile not found")
