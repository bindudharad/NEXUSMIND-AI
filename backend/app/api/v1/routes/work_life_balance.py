from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.work_life_balance import WorkLifeBalanceRequest, WorkLifeBalanceResponse
from app.services.work_life_balance_service import work_life_balance_service

router = APIRouter()


@router.get("/default", response_model=WorkLifeBalanceResponse)
def default_work_life_balance(_: EnterpriseUser = Depends(get_current_user)) -> WorkLifeBalanceResponse:
    return work_life_balance_service.optimize()


@router.post("/optimize", response_model=WorkLifeBalanceResponse)
def optimize_work_life_balance(
    payload: WorkLifeBalanceRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> WorkLifeBalanceResponse:
    return work_life_balance_service.optimize(payload)


@router.get("/stream")
def stream_work_life_balance(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(work_life_balance_service.stream(), media_type="text/event-stream")
