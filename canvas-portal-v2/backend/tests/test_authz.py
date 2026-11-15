import asyncio

import pytest
from fastapi import HTTPException

import auth.jwt_validator as jwt_validator
from auth.middleware import require_admin
from auth.models import AuthUser
from config import get_settings


@pytest.fixture(autouse=True)
def fresh_settings(monkeypatch):
    monkeypatch.delenv("AUTHZ_ADMIN_GROUPS", raising=False)
    monkeypatch.delenv("AUTHZ_ALLOW_ALL_AUTHENTICATED", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def configure(monkeypatch, groups=None, allow_all=None):
    if groups is not None:
        monkeypatch.setenv("AUTHZ_ADMIN_GROUPS", groups)
    if allow_all is not None:
        monkeypatch.setenv("AUTHZ_ALLOW_ALL_AUTHENTICATED", allow_all)
    get_settings.cache_clear()


def check(groups):
    user = AuthUser(username="alice", email="", groups=groups)
    return asyncio.run(require_admin(user))


@pytest.mark.parametrize("groups", [["canvas-admin"], ["/canvas-admin"], ["viewers", "canvas-admin"]])
def test_default_admin_group_is_allowed(groups):
    assert check(groups).username == "alice"


@pytest.mark.parametrize("groups", [[], ["viewers"], ["canvas-admin-x"]])
def test_other_users_are_denied(groups):
    with pytest.raises(HTTPException) as exc:
        check(groups)
    assert exc.value.status_code == 403


def test_configured_groups_are_normalised(monkeypatch):
    configure(monkeypatch, groups='["/ops", " platform "]')
    assert check(["/platform"])
    with pytest.raises(HTTPException):
        check(["canvas-admin"])


def test_empty_list_denies_everyone(monkeypatch):
    configure(monkeypatch, groups="[]")
    with pytest.raises(HTTPException) as exc:
        check(["canvas-admin"])
    assert exc.value.status_code == 403


def test_empty_list_with_opt_in_allows_everyone(monkeypatch):
    configure(monkeypatch, groups="[]", allow_all="true")
    assert check([])


def test_opt_in_allows_everyone_even_with_groups_set(monkeypatch):
    configure(monkeypatch, allow_all="true")
    assert check(["viewers"])
    assert check([])


def test_keycloak_groups_and_realm_roles_are_merged(monkeypatch):
    monkeypatch.setattr(jwt_validator.settings, "IDM_PROVIDER", "keycloak")
    claims = {"groups": ["/viewers"], "realm_access": {"roles": ["canvas-admin", "/viewers"]}}
    assert jwt_validator.extract_groups(claims) == ["/viewers", "canvas-admin"]
    assert jwt_validator.extract_groups({"realm_access": {"roles": ["canvas-admin"]}}) == ["canvas-admin"]
    assert jwt_validator.extract_groups({"groups": None, "realm_access": None}) == []


def test_realm_role_grants_access_alongside_unrelated_groups(monkeypatch):
    monkeypatch.setattr(jwt_validator.settings, "IDM_PROVIDER", "keycloak")
    claims = {"groups": ["/viewers"], "realm_access": {"roles": ["canvas-admin"]}}
    assert check(jwt_validator.extract_groups(claims))
