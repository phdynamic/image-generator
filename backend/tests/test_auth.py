import pytest
from starlette.websockets import WebSocketDisconnect

from app import auth
from app.config import settings
from app.passwords import hash_password, verify_password
from tests.conftest import PASSWORD


# -- passwords ---------------------------------------------------------------

def test_password_roundtrip():
    stored = hash_password("hunter2hunter2")
    assert verify_password("hunter2hunter2", stored)
    assert not verify_password("hunter2hunter3", stored)


def test_hashes_are_salted():
    assert hash_password("same-password") != hash_password("same-password")


@pytest.mark.parametrize("bad", ["", "plaintext", "scrypt:1:2", "md5:a:b:c:d:e", "scrypt:x:8:1:zz:zz"])
def test_malformed_hash_never_verifies(bad):
    assert not verify_password("anything", bad)


# -- session tokens ----------------------------------------------------------

def test_token_valid(monkeypatch):
    monkeypatch.setattr(settings, "APP_PASSWORD_HASH", hash_password(PASSWORD))
    assert auth.verify_token(auth.make_token())


def test_token_expired(monkeypatch):
    monkeypatch.setattr(settings, "APP_PASSWORD_HASH", hash_password(PASSWORD))
    assert not auth.verify_token(auth.make_token(ttl_seconds=-5))


def test_token_tampered(monkeypatch):
    monkeypatch.setattr(settings, "APP_PASSWORD_HASH", hash_password(PASSWORD))
    token = auth.make_token()
    expires, nonce, sig = token.split(".")
    assert not auth.verify_token(f"{int(expires) + 99999}.{nonce}.{sig}")
    assert not auth.verify_token(f"{expires}.{nonce}.{'0' * len(sig)}")
    assert not auth.verify_token("garbage")
    assert not auth.verify_token(None)


def test_changing_password_invalidates_sessions(monkeypatch):
    monkeypatch.setattr(settings, "APP_PASSWORD_HASH", hash_password(PASSWORD))
    token = auth.make_token()
    monkeypatch.setattr(settings, "APP_PASSWORD_HASH", hash_password("a different password"))
    assert not auth.verify_token(token)


# -- local mode (no password) ------------------------------------------------

def test_local_mode_is_open(open_client):
    assert open_client.get("/api/models").status_code == 200
    status = open_client.get("/api/auth/status").json()
    assert status == {"auth_required": False, "authenticated": True}


def test_no_password_blocks_tunnel_traffic(open_client):
    r = open_client.get("/api/models", headers={"CF-Connecting-IP": "203.0.113.9"})
    assert r.status_code == 403


def test_public_mode_needs_password(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_MODE", True)
    monkeypatch.setattr(settings, "APP_PASSWORD_HASH", "")
    with pytest.raises(RuntimeError):
        auth.assert_safe_config()
    monkeypatch.setattr(settings, "APP_PASSWORD_HASH", hash_password(PASSWORD))
    auth.assert_safe_config()


# -- password protected ------------------------------------------------------

@pytest.mark.parametrize("path", ["/api/models", "/api/images", "/api/gpu-status",
                                  "/api/templates", "/api/prompts/history",
                                  "/outputs/images/x.png", "/outputs/thumbnails/x.png"])
def test_protected_routes_need_session(locked_client, path):
    assert locked_client.get(path).status_code == 401


def test_frontend_shell_is_public(locked_client):
    # the login page must load before anyone is signed in
    assert locked_client.get("/").status_code != 401


def test_status_when_signed_out(locked_client):
    assert locked_client.get("/api/auth/status").json() == {
        "auth_required": True, "authenticated": False}


def test_wrong_password_rejected(locked_client):
    r = locked_client.post("/api/auth/login", json={"password": "nope"})
    assert r.status_code == 401
    assert "set-cookie" not in r.headers
    assert locked_client.get("/api/models").status_code == 401


def test_login_grants_access(signed_in):
    assert signed_in.get("/api/models").status_code == 200
    assert signed_in.get("/api/auth/status").json()["authenticated"] is True


def test_cookie_flags(locked_client):
    r = locked_client.post("/api/auth/login", json={"password": PASSWORD},
                           headers={"X-Forwarded-Proto": "https"})
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "secure" in cookie


def test_logout(signed_in):
    signed_in.post("/api/auth/logout")
    signed_in.cookies.clear()
    assert signed_in.get("/api/models").status_code == 401


def test_lockout_after_repeated_failures(locked_client, monkeypatch):
    async def no_sleep(_):
        return None
    monkeypatch.setattr("app.routers.auth_router.asyncio.sleep", no_sleep)
    for _ in range(5):
        assert locked_client.post("/api/auth/login", json={"password": "bad"}).status_code == 401
    # even the right password is refused while locked
    assert locked_client.post("/api/auth/login", json={"password": PASSWORD}).status_code == 429


def test_lockout_is_per_ip(locked_client, monkeypatch):
    async def no_sleep(_):
        return None
    monkeypatch.setattr("app.routers.auth_router.asyncio.sleep", no_sleep)
    for _ in range(5):
        locked_client.post("/api/auth/login", json={"password": "bad"},
                           headers={"CF-Connecting-IP": "198.51.100.1"})
    r = locked_client.post("/api/auth/login", json={"password": PASSWORD},
                           headers={"CF-Connecting-IP": "198.51.100.2"})
    assert r.status_code == 200


def test_cross_site_post_blocked(signed_in):
    r = signed_in.post("/api/images/batch-delete", json={"ids": []},
                       headers={"Origin": "https://evil.example"})
    assert r.status_code == 403


def test_same_origin_post_allowed(signed_in):
    r = signed_in.post("/api/images/batch-delete", json={"ids": []},
                       headers={"Origin": "http://testserver"})
    assert r.status_code == 200


# -- websocket ---------------------------------------------------------------

def test_websocket_rejected_without_session(locked_client):
    with pytest.raises(WebSocketDisconnect):
        with locked_client.websocket_connect("/ws/progress"):
            pass


def test_websocket_rejected_cross_site(signed_in):
    with pytest.raises(WebSocketDisconnect):
        with signed_in.websocket_connect("/ws/progress", headers={"Origin": "https://evil.example"}):
            pass


def test_websocket_allowed_with_session(signed_in):
    with signed_in.websocket_connect("/ws/progress") as ws:
        ws.send_text("ping")


def test_api_docs_are_not_exposed(locked_client):
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert locked_client.get(path).status_code == 404, path
