from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.client_satisfaction import ClientAssistantRequest, ClientAssistantResponse, ClientSatisfactionRequest, ClientSatisfactionResponse
from app.services.client_satisfaction_service import client_satisfaction_service

router = APIRouter()


@router.get("/default", response_model=ClientSatisfactionResponse)
def default_client_satisfaction(_: EnterpriseUser = Depends(get_current_user)) -> ClientSatisfactionResponse:
    return client_satisfaction_service.predict()


@router.post("/predict", response_model=ClientSatisfactionResponse)
def predict_client_satisfaction(
    payload: ClientSatisfactionRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> ClientSatisfactionResponse:
    return client_satisfaction_service.predict(payload)


@router.post("/assistant", response_model=ClientAssistantResponse)
def ask_client_relationship_assistant(
    payload: ClientAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> ClientAssistantResponse:
    return client_satisfaction_service.ask(payload)


@router.get("/stream")
def stream_client_satisfaction(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(client_satisfaction_service.stream(), media_type="text/event-stream")
