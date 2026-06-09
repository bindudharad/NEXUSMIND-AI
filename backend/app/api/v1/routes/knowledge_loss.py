from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.knowledge_loss import KnowledgeLossRequest, KnowledgeLossResponse
from app.services.knowledge_loss_service import knowledge_loss_service

router = APIRouter()


@router.get("/default", response_model=KnowledgeLossResponse)
def default_knowledge_loss(_: EnterpriseUser = Depends(get_current_user)) -> KnowledgeLossResponse:
    return knowledge_loss_service.analyze()


@router.post("/analyze", response_model=KnowledgeLossResponse)
def analyze_knowledge_loss(
    payload: KnowledgeLossRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> KnowledgeLossResponse:
    return knowledge_loss_service.analyze(payload)


@router.get("/stream")
def stream_knowledge_loss(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(knowledge_loss_service.stream(), media_type="text/event-stream")
