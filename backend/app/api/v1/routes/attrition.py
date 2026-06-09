from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.attrition import AttritionAnalyzeRequest, AttritionResponse
from app.services.attrition_service import attrition_prediction_service

router = APIRouter()


@router.get("/default", response_model=AttritionResponse)
def default_attrition(_: EnterpriseUser = Depends(get_current_user)) -> AttritionResponse:
    return attrition_prediction_service.analyze()


@router.post("/analyze", response_model=AttritionResponse)
def analyze_attrition(
    payload: AttritionAnalyzeRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> AttritionResponse:
    return attrition_prediction_service.analyze(payload)


@router.get("/stream")
def stream_attrition(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(attrition_prediction_service.stream(), media_type="text/event-stream")
