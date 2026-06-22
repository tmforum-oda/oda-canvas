from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.jwt_validator import validate_token, extract_groups
from auth.models import AuthUser

bearer_scheme = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> AuthUser:
    claims = await validate_token(credentials.credentials)
    return AuthUser(
        username=claims.get("preferred_username") or claims.get("upn", ""),
        email=claims.get("email", ""),
        groups=extract_groups(claims),
        sub=claims.get("sub", ""),
    )
