import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.jwt_validator import validate_token, extract_groups
from auth.models import AuthUser
from config import get_settings

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> AuthUser:
    claims = await validate_token(credentials.credentials)
    return AuthUser(
        username=claims.get("preferred_username") or claims.get("upn", ""),
        email=claims.get("email", ""),
        groups=extract_groups(claims),
        sub=claims.get("sub", ""),
    )


def _normalize_group(group: str) -> str:
    # Keycloak's group-membership mapper emits full paths such as "/canvas-admin".
    return group.strip().lstrip("/")


async def require_admin(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Allow only users in one of AUTHZ_ADMIN_GROUPS (group or realm role). Fails closed.

    AUTHZ_ALLOW_ALL_AUTHENTICATED=true turns the check off and allows any authenticated user.
    """
    settings = get_settings()
    if settings.AUTHZ_ALLOW_ALL_AUTHENTICATED:
        return user
    required = {_normalize_group(g) for g in settings.AUTHZ_ADMIN_GROUPS if g.strip()}
    if not required:
        logger.error("AUTHZ_ADMIN_GROUPS is empty; denying admin route access to user=%s", user.username)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access is not configured.")
    if required.isdisjoint(_normalize_group(g) for g in user.groups):
        logger.warning("Access denied: user=%s is not in any of %s", user.username, sorted(required))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )
    return user
