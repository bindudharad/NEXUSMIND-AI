from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from uuid import uuid4

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.roles import EnterpriseRole
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


DEMO_USERS: dict[str, dict[str, str | EnterpriseRole]] = {
    "ceo@nexusmind.ai": {
        "id": "usr_ceo_001",
        "email": "ceo@nexusmind.ai",
        "password": settings.demo_ceo_password,
        "full_name": "Aarav Mehta",
        "role": EnterpriseRole.CEO,
        "department": "Executive",
        "tenant_id": "tenant_nexusmind_demo",
    },
    "admin@nexusmind.ai": {
        "id": "usr_admin_001",
        "email": "admin@nexusmind.ai",
        "password": settings.demo_admin_password,
        "full_name": "Nisha Rao",
        "role": EnterpriseRole.ADMIN,
        "department": "Platform",
        "tenant_id": "tenant_nexusmind_demo",
    },
}


class AuthService:
    def __init__(self) -> None:
        self._users: dict[str, dict[str, str | EnterpriseRole]] = {}
        self._revoked_tokens: set[str] = set()
        self._reset_tokens: dict[str, dict[str, str | datetime]] = {}
        self._seed_demo_users()

    def authenticate(self, credentials: LoginRequest) -> TokenResponse:
        user_record = self._users.get(credentials.email.lower())
        password_hash = str(user_record.get("password_hash", "")) if user_record else ""
        if not user_record or not verify_password(credentials.password, password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        user = self._to_user(user_record)
        token = create_access_token(user.id, {"role": user.role.value, "email": user.email, "tenant_id": user.tenant_id})
        return TokenResponse(access_token=token, user=UserResponse.model_validate(user.model_dump()))

    def register(self, payload: RegisterRequest) -> TokenResponse:
        email = payload.email.lower()
        if email in self._users:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

        user_record: dict[str, str | EnterpriseRole] = {
            "id": f"usr_{uuid4().hex[:12]}",
            "email": email,
            "password_hash": hash_password(payload.password),
            "full_name": payload.full_name.strip(),
            "role": payload.role,
            "department": payload.department.strip(),
            "tenant_id": settings.default_tenant_id,
        }
        self._users[email] = user_record
        user = self._to_user(user_record)
        token = create_access_token(user.id, {"role": user.role.value, "email": user.email, "tenant_id": user.tenant_id})
        return TokenResponse(access_token=token, user=UserResponse.model_validate(user.model_dump()))

    def request_password_reset(self, payload: PasswordResetRequest) -> PasswordResetResponse:
        email = payload.email.lower()
        user_record = self._users.get(email)
        if not user_record:
            return PasswordResetResponse(status="If the account exists, a password reset was issued.")

        reset_token = token_urlsafe(32)
        self._reset_tokens[reset_token] = {
            "email": email,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        token_for_response = None if settings.environment.lower() == "production" else reset_token
        return PasswordResetResponse(status="Password reset issued.", reset_token=token_for_response)

    def confirm_password_reset(self, payload: PasswordResetConfirmRequest) -> PasswordResetConfirmResponse:
        reset_record = self._reset_tokens.pop(payload.reset_token, None)
        expires_at = reset_record.get("expires_at") if reset_record else None
        if not reset_record or not isinstance(expires_at, datetime) or expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired password reset token")

        email = str(reset_record["email"])
        user_record = self._users.get(email)
        if not user_record:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password reset token")

        user_record["password_hash"] = hash_password(payload.new_password)
        return PasswordResetConfirmResponse(status="Password reset completed.")

    def logout(self, token: str) -> LogoutResponse:
        self._revoked_tokens.add(token)
        return LogoutResponse(status="Logged out.", revoked=True)

    def is_token_revoked(self, token: str) -> bool:
        return token in self._revoked_tokens

    def get_user_by_id(self, user_id: str) -> EnterpriseUser | None:
        for user_record in self._users.values():
            if user_record["id"] == user_id:
                return self._to_user(user_record)
        return None

    def _seed_demo_users(self) -> None:
        for user_record in DEMO_USERS.values():
            seeded = {
                **user_record,
                "password_hash": hash_password(str(user_record["password"])),
            }
            seeded.pop("password", None)
            self._users[str(user_record["email"]).lower()] = seeded

    @staticmethod
    def _to_user(user_record: dict[str, str | EnterpriseRole]) -> EnterpriseUser:
        role_value = user_record["role"]
        return EnterpriseUser(
            id=str(user_record["id"]),
            email=str(user_record["email"]),
            full_name=str(user_record["full_name"]),
            role=role_value if isinstance(role_value, EnterpriseRole) else EnterpriseRole(str(role_value)),
            department=str(user_record["department"]),
            tenant_id=str(user_record.get("tenant_id", settings.default_tenant_id)),
        )


auth_service = AuthService()
