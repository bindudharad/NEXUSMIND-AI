from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.genai_hr_assistant import GenAIHRAssistantRequest, GenAIHRAssistantResponse
from app.services.genai_hr_assistant_service import genai_hr_assistant_service


router = APIRouter()


@router.get("/default", response_model=GenAIHRAssistantResponse)
def default_genai_hr_assistant(_: EnterpriseUser = Depends(get_current_user)) -> GenAIHRAssistantResponse:
    return genai_hr_assistant_service.default()


@router.post("/ask", response_model=GenAIHRAssistantResponse)
def ask_genai_hr_assistant(
    payload: GenAIHRAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> GenAIHRAssistantResponse:
    return genai_hr_assistant_service.ask(payload)


@router.post("/report", response_model=GenAIHRAssistantResponse)
def generate_genai_hr_report(
    payload: GenAIHRAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> GenAIHRAssistantResponse:
    report_payload = payload.model_copy(update={"question": payload.question or "Generate executive workforce report."})
    return genai_hr_assistant_service.ask(report_payload)


@router.post("/stream")
def stream_genai_hr_assistant(
    payload: GenAIHRAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> StreamingResponse:
    return StreamingResponse(genai_hr_assistant_service.stream(payload), media_type="text/event-stream")
