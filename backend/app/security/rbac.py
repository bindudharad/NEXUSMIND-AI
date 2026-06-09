from collections.abc import Iterable

from fastapi import HTTPException, status

from app.models.roles import EnterpriseRole
from app.models.user import EnterpriseUser


def require_roles(user: EnterpriseUser, allowed_roles: Iterable[EnterpriseRole]) -> None:
    if user.role not in set(allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action",
        )
