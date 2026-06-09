from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.autonomous_workflow import (
    AutonomousWorkflowRequest,
    AutonomousWorkflowResponse,
    OperationsAssistantRequest,
    OperationsAssistantResponse,
)
from app.services.autonomous_workflow_service import autonomous_workflow_service

router = APIRouter()


@router.get("/default", response_model=AutonomousWorkflowResponse)
def default_autonomous_workflow(_: EnterpriseUser = Depends(get_current_user)) -> AutonomousWorkflowResponse:
    return autonomous_workflow_service.run()


@router.post("/run", response_model=AutonomousWorkflowResponse)
def run_autonomous_workflow(
    payload: AutonomousWorkflowRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> AutonomousWorkflowResponse:
    return autonomous_workflow_service.run(payload)


@router.post("/assistant", response_model=OperationsAssistantResponse)
def ask_operations_assistant(
    payload: OperationsAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> OperationsAssistantResponse:
    return autonomous_workflow_service.ask(payload)


@router.get("/stream")
def stream_autonomous_workflow(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(autonomous_workflow_service.stream(), media_type="text/event-stream")
