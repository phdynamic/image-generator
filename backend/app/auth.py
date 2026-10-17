"""Session auth for Imaginaree.

A single shared password protects the whole app. Sessions are HMAC-signed
cookies; changing the password invalidates every existing session.
"""
import hashlib
import hmac
import logging
import os
import secrets
import threading
import time
from http.cookies import SimpleCookie
from urllib.parse import urlparse

from starlette.datastructures import Headers
from starlette.responses import JSONResponse

from .config import APP_ROOT, settings

logger = logging.getLogger(__name__)

COOKIE_NAME = "imaginaree_session"
PROTECTED_PREFIXES = ("/api/", "/outputs/", "/ws/")
PUBLIC_PATHS = ("/api/auth/status", "/api/auth/login", "/api/auth/logout")
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
# Cloudflare adds these to anything that arrives through a tunnel.
PROXY_HEADERS = ("cf-connecting-ip", "cf-ray")

_secret_lock = threading.Lock()
_secret_cache: str | None = None


def auth_enabled() -> bool:
    return bool(settings.APP_PASSWORD_HASH)


def assert_safe_config() -> None:
    """Refuse to run in public mode without a password."""
    if settings.PUBLIC_MODE and not auth_enabled():
        raise RuntimeError(
            "PUBLIC_MODE is on but no password is set. Run "
            "'python scripts/set_password.py' and restart."
        )


def _session_secret() -> str:
    global _secret_cache
    if settings.SESSION_SECRET:
        return settings.SESSION_SECRET
    with _secret_lock:
        if _secret_cache is None:
            path = APP_ROOT / ".session_secret"
            try:
                _secret_cache = path.read_text().strip()
            except OSError:
                _secret_cache = ""
            if not _secret_cache:
                _secret_cache = secrets.token_hex(32)
                try:
                    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                    with os.fdopen(fd, "w") as f:
                        f.write(_secret_cache)
                except OSError:
                    logger.warning("Could not persist session secret; sessions reset on restart")
        return _secret_cache


def _signing_key() -> bytes:
    # Bound to the password hash so changing the password logs everyone out.
    return f"{_session_secret()}|{settings.APP_PASSWORD_HASH}".encode()


def _sign(payload: str) -> str:
    return hmac.new(_signing_key(), payload.encode(), hashlib.sha256).hexdigest()


def make_token(ttl_seconds: int | None = None) -> str:
    ttl = ttl_seconds if ttl_seconds is not None else settings.SESSION_HOURS * 3600
    payload = f"{int(time.time()) + ttl}.{secrets.token_hex(8)}"
    return f"{payload}.{_sign(payload)}"


def verify_token(token: str | None) -> bool:
    if not token:
        return False
    try:
        expires, nonce, signature = token.split(".")
        payload = f"{expires}.{nonce}"
        if not hmac.compare_digest(signature, _sign(payload)):
            return False
        return int(expires) > time.time()
    except (ValueError, TypeError):
        return False


def token_from_cookie_header(cookie_header: str | None) -> str | None:
    if not cookie_header:
        return None
    try:
        cookies = SimpleCookie()
        cookies.load(cookie_header)
        morsel = cookies.get(COOKIE_NAME)
        return morsel.value if morsel else None
    except Exception:
        return None


def client_ip(headers: Headers, fallback: str | None) -> str:
    return headers.get("cf-connecting-ip") or fallback or "unknown"


class LoginLimiter:
    """Locks an IP out after repeated failures."""

    def __init__(self, max_failures: int = 5, window: int = 900, lockout: int = 900):
        self.max_failures = max_failures
        self.window = window
        self.lockout = lockout
        self._failures: dict[str, list[float]] = {}
        self._locked_until: dict[str, float] = {}
        self._lock = threading.Lock()

    def retry_after(self, ip: str) -> int:
        with self._lock:
            remaining = self._locked_until.get(ip, 0) - time.time()
            return int(remaining) + 1 if remaining > 0 else 0

    def record_failure(self, ip: str) -> None:
        now = time.time()
        with self._lock:
            recent = [t for t in self._failures.get(ip, []) if now - t < self.window]
            recent.append(now)
            self._failures[ip] = recent
            if len(recent) >= self.max_failures:
                self._locked_until[ip] = now + self.lockout
                self._failures[ip] = []

    def record_success(self, ip: str) -> None:
        with self._lock:
            self._failures.pop(ip, None)
            self._locked_until.pop(ip, None)


login_limiter = LoginLimiter()


def _origin_matches_host(headers: Headers) -> bool:
    origin = headers.get("origin")
    if not origin or origin == "null":
        return origin is None
    host = headers.get("host", "")
    return urlparse(origin).netloc.lower() == host.lower()


class AuthMiddleware:
    """Pure ASGI middleware so it covers HTTP and WebSocket connections."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        path = scope["path"]

        if not auth_enabled():
            # No password configured. That's fine on localhost, but never if
            # the request came through a Cloudflare tunnel.
            if any(h in headers for h in PROXY_HEADERS):
                await self._deny(scope, receive, send, 403,
                                 "Access is not configured. Set a password first.")
                return
            await self.app(scope, receive, send)
            return

        # Cross-site requests are never legitimate for this app.
        method = scope.get("method", "GET")
        if (scope["type"] == "websocket" or method in UNSAFE_METHODS) \
                and not _origin_matches_host(headers):
            await self._deny(scope, receive, send, 403, "Cross-origin request blocked")
            return

        protected = path.startswith(PROTECTED_PREFIXES) and path not in PUBLIC_PATHS
        if protected:
            token = token_from_cookie_header(headers.get("cookie"))
            if not verify_token(token):
                await self._deny(scope, receive, send, 401, "Not signed in")
                return

        await self.app(scope, receive, send)

    @staticmethod
    async def _deny(scope, receive, send, status: int, message: str):
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return
        response = JSONResponse({"detail": message}, status_code=status)
        await response(scope, receive, send)
