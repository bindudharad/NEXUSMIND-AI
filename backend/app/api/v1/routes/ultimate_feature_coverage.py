from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.ultimate_feature_coverage import UltimateFeatureCoverageResponse
from app.services.ultimate_feature_coverage_service import ultimate_feature_coverage_service

router = APIRouter()


@router.get("/audit", response_model=UltimateFeatureCoverageResponse)
def audit_ultimate_feature_coverage(_: EnterpriseUser = Depends(get_current_user)) -> UltimateFeatureCoverageResponse:
    return ultimate_feature_coverage_service.verify()


@router.get("/stream")
def stream_ultimate_feature_coverage(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(ultimate_feature_coverage_service.stream(), media_type="text/event-stream")
