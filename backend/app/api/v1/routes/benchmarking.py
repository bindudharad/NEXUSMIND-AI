from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.benchmarking import BenchmarkingRequest, BenchmarkingResponse
from app.services.benchmarking_service import benchmarking_service

router = APIRouter()


@router.get("/default", response_model=BenchmarkingResponse)
def default_benchmarking(_: EnterpriseUser = Depends(get_current_user)) -> BenchmarkingResponse:
    return benchmarking_service.analyze()


@router.post("/analyze", response_model=BenchmarkingResponse)
def analyze_benchmarking(
    payload: BenchmarkingRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> BenchmarkingResponse:
    return benchmarking_service.analyze(payload)


@router.get("/stream")
def stream_benchmarking(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(benchmarking_service.stream(), media_type="text/event-stream")
