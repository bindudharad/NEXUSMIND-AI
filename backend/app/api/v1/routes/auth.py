from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials

from app.api.v1.dependencies import bearer_scheme, get_current_user
from app.models.user import EnterpriseUser
from app.schemas.auth import (
    LoginRequest,
    LogoutResponse,
    PasswordResetConfirmRequest,
    PasswordResetConfirmResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import auth_service

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    return auth_service.authenticate(payload)


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest) -> TokenResponse:
    return auth_service.register(payload)


@router.get("/me", response_model=UserResponse)
def me(current_user: EnterpriseUser = Depends(get_current_user)) -> EnterpriseUser:
    return current_user


@router.post("/logout", response_model=LogoutResponse)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    _: EnterpriseUser = Depends(get_current_user),
) -> LogoutResponse:
    return auth_service.logout(credentials.credentials)


@router.post("/password-reset/request", response_model=PasswordResetResponse)
def request_password_reset(payload: PasswordResetRequest) -> PasswordResetResponse:
    return auth_service.request_password_reset(payload)


@router.post("/password-reset/confirm", response_model=PasswordResetConfirmResponse)
def confirm_password_reset(payload: PasswordResetConfirmRequest) -> PasswordResetConfirmResponse:
    return auth_service.confirm_password_reset(payload)
