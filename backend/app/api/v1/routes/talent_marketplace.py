from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.talent_marketplace import (
    TalentAssistantRequest,
    TalentAssistantResponse,
    TalentMarketplaceRequest,
    TalentMarketplaceResponse,
    TalentSearchRequest,
    TalentSearchResponse,
)
from app.services.talent_marketplace_service import talent_marketplace_service

router = APIRouter()


@router.get("/default", response_model=TalentMarketplaceResponse)
def default_talent_marketplace(_: EnterpriseUser = Depends(get_current_user)) -> TalentMarketplaceResponse:
    return talent_marketplace_service.default()


@router.post("/analyze", response_model=TalentMarketplaceResponse)
def analyze_talent_marketplace(
    payload: TalentMarketplaceRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> TalentMarketplaceResponse:
    return talent_marketplace_service.analyze(payload)


@router.post("/search", response_model=TalentSearchResponse)
def search_talent_marketplace(
    payload: TalentSearchRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> TalentSearchResponse:
    return talent_marketplace_service.search(payload)


@router.post("/assistant", response_model=TalentAssistantResponse)
def ask_talent_assistant(
    payload: TalentAssistantRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> TalentAssistantResponse:
    return talent_marketplace_service.ask(payload)


@router.get("/stream")
def stream_talent_marketplace(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(talent_marketplace_service.stream(), media_type="text/event-stream")
