from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.nlp import NLPAnalyzeRequest, NLPAnalyzeResponse, NLPBatchRequest, NLPBatchResponse, NLPTrendsResponse
from app.services.nlp_service import nlp_service

router = APIRouter()


@router.post("/analyze", response_model=NLPAnalyzeResponse)
def analyze_message(payload: NLPAnalyzeRequest, _: EnterpriseUser = Depends(get_current_user)) -> NLPAnalyzeResponse:
    return nlp_service.analyze(payload)


@router.post("/batch", response_model=NLPBatchResponse)
def analyze_batch(payload: NLPBatchRequest, _: EnterpriseUser = Depends(get_current_user)) -> NLPBatchResponse:
    return nlp_service.batch(payload)


@router.get("/trends", response_model=NLPTrendsResponse)
def emotion_trends(_: EnterpriseUser = Depends(get_current_user)) -> NLPTrendsResponse:
    return nlp_service.trends()
