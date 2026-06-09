import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.enterprise_knowledge import (
    EnterpriseKnowledgeAskRequest,
    EnterpriseKnowledgeAskResponse,
    EnterpriseKnowledgeDefaultResponse,
    EnterpriseKnowledgeExpertsResponse,
    EnterpriseKnowledgeGraphResponse,
    EnterpriseKnowledgeIngestRequest,
    EnterpriseKnowledgeIngestResponse,
    EnterpriseKnowledgeSearchRequest,
    EnterpriseKnowledgeSearchResponse,
)
from app.services.enterprise_knowledge_service import enterprise_knowledge_service

router = APIRouter()


@router.get("/default", response_model=EnterpriseKnowledgeDefaultResponse)
def default_company_brain(_: EnterpriseUser = Depends(get_current_user)) -> EnterpriseKnowledgeDefaultResponse:
    return enterprise_knowledge_service.default()


@router.post("/ingest", response_model=EnterpriseKnowledgeIngestResponse)
def ingest_company_knowledge(
    payload: EnterpriseKnowledgeIngestRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> EnterpriseKnowledgeIngestResponse:
    return enterprise_knowledge_service.ingest(payload)


@router.post("/upload", response_model=EnterpriseKnowledgeIngestResponse)
async def upload_company_knowledge(
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form()] = None,
    source_type: Annotated[str | None, Form()] = None,
    metadata: Annotated[str | None, Form()] = None,
    persist: Annotated[bool, Form()] = True,
    _: EnterpriseUser = Depends(get_current_user),
) -> EnterpriseKnowledgeIngestResponse:
    metadata_payload = {}
    if metadata:
        try:
            loaded = json.loads(metadata)
            metadata_payload = loaded if isinstance(loaded, dict) else {}
        except json.JSONDecodeError:
            metadata_payload = {}
    raw_bytes = await file.read()
    return enterprise_knowledge_service.ingest_upload(
        file_name=file.filename or "uploaded-document.txt",
        raw_bytes=raw_bytes,
        title=title,
        source_type=source_type,
        metadata=metadata_payload,
        persist=persist,
    )


@router.post("/search", response_model=EnterpriseKnowledgeSearchResponse)
def search_company_brain(
    payload: EnterpriseKnowledgeSearchRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> EnterpriseKnowledgeSearchResponse:
    return enterprise_knowledge_service.search(payload)


@router.post("/ask", response_model=EnterpriseKnowledgeAskResponse)
def ask_company_brain(
    payload: EnterpriseKnowledgeAskRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> EnterpriseKnowledgeAskResponse:
    return enterprise_knowledge_service.ask(payload)


@router.get("/graph", response_model=EnterpriseKnowledgeGraphResponse)
def graph_company_brain(_: EnterpriseUser = Depends(get_current_user)) -> EnterpriseKnowledgeGraphResponse:
    return enterprise_knowledge_service.graph()


@router.get("/graph/query", response_model=EnterpriseKnowledgeGraphResponse)
def query_company_brain_graph(
    q: str | None = Query(default=None),
    node_type: str | None = Query(default=None),
    _: EnterpriseUser = Depends(get_current_user),
) -> EnterpriseKnowledgeGraphResponse:
    return enterprise_knowledge_service.query_graph(q, node_type)


@router.get("/experts", response_model=EnterpriseKnowledgeExpertsResponse)
def expert_rankings(
    skill: str | None = Query(default=None),
    _: EnterpriseUser = Depends(get_current_user),
) -> EnterpriseKnowledgeExpertsResponse:
    return enterprise_knowledge_service.experts(skill)


@router.get("/stream")
def stream_company_brain(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(enterprise_knowledge_service.stream(), media_type="text/event-stream")
