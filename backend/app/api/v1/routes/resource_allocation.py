from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.resource_allocation import ResourceAllocationRequest, ResourceAllocationResponse
from app.services.resource_allocation_service import resource_allocation_service

router = APIRouter()


@router.get("/default", response_model=ResourceAllocationResponse)
def default_resource_allocation(_: EnterpriseUser = Depends(get_current_user)) -> ResourceAllocationResponse:
    return resource_allocation_service.optimize()


@router.post("/optimize", response_model=ResourceAllocationResponse)
def optimize_resource_allocation(
    payload: ResourceAllocationRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> ResourceAllocationResponse:
    return resource_allocation_service.optimize(payload)


@router.get("/stream")
def stream_resource_allocation(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(resource_allocation_service.stream(), media_type="text/event-stream")
