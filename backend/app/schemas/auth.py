from pydantic import BaseModel, EmailStr, Field

from app.models.roles import EnterpriseRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    role: EnterpriseRole = EnterpriseRole.EMPLOYEE
    department: str = Field(default="General", min_length=2, max_length=80)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    reset_token: str = Field(min_length=24, max_length=256)
    new_password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: EnterpriseRole
    department: str
    tenant_id: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LogoutResponse(BaseModel):
    status: str
    revoked: bool


class PasswordResetResponse(BaseModel):
    status: str
    reset_token: str | None = None


class PasswordResetConfirmResponse(BaseModel):
    status: str
