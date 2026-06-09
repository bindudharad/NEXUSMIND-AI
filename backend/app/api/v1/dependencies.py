from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.core.config import settings
from app.models.user import EnterpriseUser
from app.services.auth_service import auth_service

bearer_scheme = HTTPBearer(auto_error=True)


def get_user_from_token(token: str) -> EnterpriseUser:
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    if auth_service.is_token_revoked(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    user = auth_service.get_user_by_id(str(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    token_tenant = str(payload.get("tenant_id", ""))
    if token_tenant and token_tenant != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant scope mismatch")
    if not token_tenant and settings.environment.lower() == "production":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant scope is required")
    return user


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> EnterpriseUser:
    return get_user_from_token(credentials.credentials)
