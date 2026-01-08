"""Keycloak OpenID Connect authentication module."""

import os
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from pydantic import BaseModel
import logging

from app.oauth2_httpx_async import auth_client


logger = logging.getLogger(__name__)

# Keycloak configuration from environment variables
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "https://canvas-keycloak.ihc-dt.cluster-2.de/auth/realms/odari")
KEYCLOAK_AUDIENCE = os.getenv("KEYCLOAK_AUDIENCE", "account")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "componentregistry")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
KEYCLOAK_ENABLED = os.getenv("KEYCLOAK_ENABLED", "false").lower() == "true"

# Cache for OIDC configuration and keys
_oidc_config_cache: Optional[Dict[str, Any]] = None
_jwks_cache: Optional[Dict[str, Any]] = None
_cache_expiry: Optional[datetime] = None


class KeycloakUser(BaseModel):
    """Keycloak user model."""
    sub: str  # Subject (user ID)
    preferred_username: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    realm_access: Optional[Dict[str, Any]] = None
    resource_access: Optional[Dict[str, Any]] = None


# OAuth2 scheme for Keycloak
oauth2_scheme_keycloak = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{KEYCLOAK_URL}/protocol/openid-connect/auth",
    tokenUrl=f"{KEYCLOAK_URL}/protocol/openid-connect/token",
    auto_error=False
)


async def get_oidc_config() -> Dict[str, Any]:
    """Fetch OpenID Connect configuration from Keycloak."""
    global _oidc_config_cache, _cache_expiry
    
    # Return cached config if still valid (cache for 1 hour)
    if _oidc_config_cache and _cache_expiry and datetime.utcnow() < _cache_expiry:
        return _oidc_config_cache
    
    well_known_url = f"{KEYCLOAK_URL}/.well-known/openid-configuration"
    
    try:
        response = await auth_client.get(well_known_url, timeout=10)
        response.raise_for_status()
        _oidc_config_cache = response.json()
        _cache_expiry = datetime.utcnow() + timedelta(hours=1)
        logger.info(f"Fetched OIDC configuration from {well_known_url}")
        return _oidc_config_cache
    except Exception as e:
        logger.error(f"Failed to fetch OIDC configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Keycloak: {str(e)}"
        )


async def get_jwks() -> Dict[str, Any]:
    """Fetch JSON Web Key Set from Keycloak."""
    global _jwks_cache
    
    # Return cached JWKS if available
    if _jwks_cache:
        return _jwks_cache
    
    oidc_config = await get_oidc_config()
    jwks_uri = oidc_config.get("jwks_uri")
    
    if not jwks_uri:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWKS URI not found in OIDC configuration"
        )
    
    try:
        response = await auth_client.get(jwks_uri, timeout=10)
        response.raise_for_status()
        _jwks_cache = response.json()
        logger.info(f"Fetched JWKS from {jwks_uri}")
        return _jwks_cache
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch JWKS: {str(e)}"
        )


async def verify_keycloak_token(token: str) -> KeycloakUser:
    """Verify and decode a Keycloak JWT token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Get OIDC configuration to get issuer
        oidc_config = await get_oidc_config()
        issuer = oidc_config.get("issuer")
        
        # Get JWKS for key verification
        jwks = await get_jwks()
        
        # Decode token header to get key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        # Find the right key
        key = None
        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == kid:
                key = jwk
                break
        
        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify and decode the token
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=KEYCLOAK_AUDIENCE,
            issuer=issuer,
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iat": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iss": True,
            }
        )
        
        return KeycloakUser(**payload)
        
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_keycloak_user(
    token: Optional[str] = Depends(oauth2_scheme_keycloak)
) -> Optional[KeycloakUser]:
    """Get current user from Keycloak token."""
    if not KEYCLOAK_ENABLED:
        return None
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return await verify_keycloak_token(token)


async def get_current_keycloak_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_keycloak)
) -> Optional[KeycloakUser]:
    """Get current user from Keycloak token (optional - returns None if not authenticated)."""
    if not KEYCLOAK_ENABLED:
        return None
    
    if not token:
        return None
    
    try:
        return await verify_keycloak_token(token)
    except HTTPException:
        return None
