import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response
import httpx
from pydantic import BaseModel
from auth.middleware import get_current_user
from auth.models import AuthUser
from config import Settings, get_settings
from utils.cache import security_status_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

SECURITY_STATUS_TTL = 300

DEFAULT_CANVAS_REALM = "odari"
DEFAULT_CANVAS_USERNAME = "admin"
DEFAULT_CANVAS_PASSWORD = "adpass"


@router.get("/me")
async def get_me(user: AuthUser = Depends(get_current_user)):
    return {
        "username": user.username,
        "email": user.email,
        "groups": user.groups,
        "authenticated": True,
    }


class SecurityStatus(BaseModel):
    defaultCredentialsInUse: bool
    username: str | None = None
    realm: str | None = None


async def _default_password_still_works(cfg: Settings, username: str) -> bool:
    try:
        async with httpx.AsyncClient(verify=False) as client:
            resp = await client.post(
                cfg.keycloak_token_url,
                data={
                    "grant_type": "password",
                    "client_id": cfg.KEYCLOAK_CLIENT_ID,
                    "username": username,
                    "password": DEFAULT_CANVAS_PASSWORD,
                },
                timeout=10,
            )
        return resp.status_code == 200
    except httpx.HTTPError:
        logger.warning("Default-credential check could not reach Keycloak; assuming not default.")
        return False


@router.get("/security-status", response_model=SecurityStatus)
async def security_status(user: AuthUser = Depends(get_current_user)):
    cfg = get_settings()

    if (
        cfg.IDM_PROVIDER != "keycloak"
        or cfg.KEYCLOAK_REALM != DEFAULT_CANVAS_REALM
        or user.username.lower() != DEFAULT_CANVAS_USERNAME
    ):
        return SecurityStatus(defaultCredentialsInUse=False)

    cache_key = f"defaultcred:{cfg.KEYCLOAK_REALM}:{user.username.lower()}"
    cached = security_status_cache.get(cache_key)
    if cached is None:
        cached = await _default_password_still_works(cfg, user.username)
        security_status_cache.set(cache_key, cached, ttl_seconds=SECURITY_STATUS_TTL)

    return SecurityStatus(
        defaultCredentialsInUse=cached,
        username=user.username if cached else None,
        realm=cfg.KEYCLOAK_REALM if cached else None,
    )


class LoginPayload(BaseModel):
    username: str
    password: str


class AccessTokenResponse(BaseModel):
    access_token: str
    expires_in: int | None = None
    token_type: str = "Bearer"


def _set_refresh_cookie(response: Response, cfg: Settings, refresh_token: str, max_age: int | None) -> None:
    if not refresh_token:
        return
    response.set_cookie(
        key=cfg.AUTH_REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=max_age,
        httponly=True,
        secure=cfg.AUTH_COOKIE_SECURE,
        samesite=cfg.AUTH_COOKIE_SAMESITE,
        path="/auth",
    )


def _clear_refresh_cookie(response: Response, cfg: Settings) -> None:
    response.delete_cookie(
        key=cfg.AUTH_REFRESH_COOKIE_NAME,
        path="/auth",
        httponly=True,
        secure=cfg.AUTH_COOKIE_SECURE,
        samesite=cfg.AUTH_COOKIE_SAMESITE,
    )


@router.post("/login", response_model=AccessTokenResponse)
async def login(payload: LoginPayload, response: Response):
    cfg = get_settings()
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.post(
            cfg.keycloak_token_url,
            data={
                "grant_type": "password",
                "client_id": cfg.KEYCLOAK_CLIENT_ID,
                "username": payload.username,
                "password": payload.password,
            },
            timeout=10,
        )
    if resp.status_code != 200:
        err = resp.json() if resp.content else {}
        if "not fully set up" in (err.get("error_description") or "").lower():
            raise HTTPException(status_code=409, detail="Account is not fully set up")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    tokens = resp.json()
    _set_refresh_cookie(response, cfg, tokens.get("refresh_token", ""), tokens.get("refresh_expires_in"))
    return AccessTokenResponse(access_token=tokens["access_token"], expires_in=tokens.get("expires_in"))


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(request: Request, response: Response):
    cfg = get_settings()
    refresh_token = request.cookies.get(cfg.AUTH_REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No active session")
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.post(
            cfg.keycloak_token_url,
            data={
                "grant_type": "refresh_token",
                "client_id": cfg.KEYCLOAK_CLIENT_ID,
                "refresh_token": refresh_token,
            },
            timeout=10,
        )
    if resp.status_code != 200:
        _clear_refresh_cookie(response, cfg)
        raise HTTPException(status_code=401, detail="Session expired")
    tokens = resp.json()
    _set_refresh_cookie(response, cfg, tokens.get("refresh_token", ""), tokens.get("refresh_expires_in"))
    return AccessTokenResponse(access_token=tokens["access_token"], expires_in=tokens.get("expires_in"))


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response):
    cfg = get_settings()
    refresh_token = request.cookies.get(cfg.AUTH_REFRESH_COOKIE_NAME)
    if refresh_token:
        try:
            async with httpx.AsyncClient(verify=False) as client:
                await client.post(
                    f"{cfg.keycloak_issuer_url}/protocol/openid-connect/logout",
                    data={"client_id": cfg.KEYCLOAK_CLIENT_ID, "refresh_token": refresh_token},
                    timeout=10,
                )
        except httpx.HTTPError:
            logger.warning("Keycloak token revocation failed during logout; clearing cookie anyway.")
    _clear_refresh_cookie(response, cfg)


class SetInitialPasswordPayload(BaseModel):
    username: str
    current_password: str
    new_password: str


@router.post("/set-initial-password", response_model=AccessTokenResponse)
async def set_initial_password(payload: SetInitialPasswordPayload, response: Response):
    cfg = get_settings()

    async with httpx.AsyncClient(verify=False) as client:
        check = await client.post(
            cfg.keycloak_token_url,
            data={
                "grant_type": "password",
                "client_id": cfg.KEYCLOAK_CLIENT_ID,
                "username": payload.username,
                "password": payload.current_password,
            },
            timeout=10,
        )

    if check.status_code == 200:
        tokens = check.json()
        _set_refresh_cookie(response, cfg, tokens.get("refresh_token", ""), tokens.get("refresh_expires_in"))
        return AccessTokenResponse(access_token=tokens["access_token"], expires_in=tokens.get("expires_in"))

    err_desc = (check.json() if check.content else {}).get("error_description", "").lower()
    if "not fully set up" not in err_desc:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    async with httpx.AsyncClient(verify=False) as client:
        admin_resp = await client.post(
            cfg.keycloak_token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": cfg.KEYCLOAK_ADMIN_CLIENT_ID,
                "client_secret": cfg.KEYCLOAK_ADMIN_CLIENT_SECRET,
            },
            timeout=10,
        )
    if admin_resp.status_code != 200:
        raise HTTPException(status_code=503, detail="Admin authentication failed")
    admin_token = admin_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    async with httpx.AsyncClient(verify=False) as client:
        users_resp = await client.get(
            f"{cfg.keycloak_admin_base_url}/users",
            params={"username": payload.username, "exact": "true"},
            headers=headers,
            timeout=10,
        )
    users = users_resp.json() if users_resp.status_code == 200 else []
    if not users:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = users[0]["id"]

    async with httpx.AsyncClient(verify=False) as client:
        await client.put(
            f"{cfg.keycloak_admin_base_url}/users/{user_id}",
            headers={**headers, "Content-Type": "application/json"},
            json={"requiredActions": []},
            timeout=10,
        )
        reset_resp = await client.put(
            f"{cfg.keycloak_admin_base_url}/users/{user_id}/reset-password",
            headers={**headers, "Content-Type": "application/json"},
            json={"type": "password", "value": payload.new_password, "temporary": False},
            timeout=10,
        )
    if reset_resp.status_code >= 400:
        raise HTTPException(status_code=502, detail="Failed to update password")

    async with httpx.AsyncClient(verify=False) as client:
        token_resp = await client.post(
            cfg.keycloak_token_url,
            data={
                "grant_type": "password",
                "client_id": cfg.KEYCLOAK_CLIENT_ID,
                "username": payload.username,
                "password": payload.new_password,
            },
            timeout=10,
        )
    if token_resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Password updated but login failed")

    tokens = token_resp.json()
    _set_refresh_cookie(response, cfg, tokens.get("refresh_token", ""), tokens.get("refresh_expires_in"))
    return AccessTokenResponse(access_token=tokens["access_token"], expires_in=tokens.get("expires_in"))
