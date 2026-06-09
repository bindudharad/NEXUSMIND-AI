from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_current_user
from app.models.user import EnterpriseUser
from app.schemas.project_failure import ProjectFailureRequest, ProjectFailureResponse
from app.services.project_failure_service import project_failure_service

router = APIRouter()


@router.get("/default", response_model=ProjectFailureResponse)
def default_project_failure(_: EnterpriseUser = Depends(get_current_user)) -> ProjectFailureResponse:
    return project_failure_service.analyze()


@router.post("/predict", response_model=ProjectFailureResponse)
def predict_project_failure(
    payload: ProjectFailureRequest,
    _: EnterpriseUser = Depends(get_current_user),
) -> ProjectFailureResponse:
    return project_failure_service.analyze(payload)


@router.get("/stream")
def stream_project_failure(_: EnterpriseUser = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(project_failure_service.stream(), media_type="text/event-stream")
