import logging
from typing import Any
import httpx
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status

from config import get_settings
from utils.cache import jwks_cache

logger = logging.getLogger(__name__)
settings = get_settings()


async def fetch_jwks() -> dict:
    cached = jwks_cache.get("jwks")
    if cached:
        return cached
    url = settings.keycloak_jwks_url if settings.IDM_PROVIDER == "keycloak" else settings.entraid_jwks_url
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(url, timeout=10)
        response.raise_for_status()
        jwks = response.json()
    jwks_cache.set("jwks", jwks)
    return jwks


async def validate_token(token: str) -> dict[str, Any]:
    try:
        jwks = await fetch_jwks()
        if settings.IDM_PROVIDER == "keycloak":
            issuer   = settings.keycloak_issuer_url
        else:
            issuer   = settings.entraid_issuer_url
        claims = jwt.decode(
            token, jwks, algorithms=["RS256"],
            issuer=issuer,
            options={"verify_exp": True, "verify_aud": False, "verify_iss": True}
        )
        return claims
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired", headers={"WWW-Authenticate": "Bearer"})
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})
    except httpx.HTTPError:
        jwks_cache.delete("jwks")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Unable to reach identity provider")


def extract_groups(claims: dict[str, Any]) -> list[str]:
    if settings.IDM_PROVIDER == "keycloak":
        groups = claims.get("groups", [])
        if not groups:
            groups = claims.get("realm_access", {}).get("roles", [])
        return groups
    return claims.get("groups", [])
