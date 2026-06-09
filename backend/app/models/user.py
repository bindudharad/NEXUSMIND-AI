from pydantic import BaseModel, EmailStr

from app.models.roles import EnterpriseRole


class EnterpriseUser(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: EnterpriseRole
    department: str
    tenant_id: str
