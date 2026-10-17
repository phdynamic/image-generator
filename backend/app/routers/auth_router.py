import asyncio

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from .. import auth
from ..config import settings
from ..passwords import verify_password

router = APIRouter(prefix="/api/auth")


class LoginRequest(BaseModel):
    password: str


def _is_https(request: Request) -> bool:
    return request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"


@router.get("/status")
def status(request: Request):
    token = request.cookies.get(auth.COOKIE_NAME)
    enabled = auth.auth_enabled()
    return {
        "auth_required": enabled,
        "authenticated": (not enabled) or auth.verify_token(token),
    }


@router.post("/login")
async def login(req: LoginRequest, request: Request, response: Response):
    if not auth.auth_enabled():
        return {"authenticated": True}

    ip = auth.client_ip(request.headers, request.client.host if request.client else None)
    wait = auth.login_limiter.retry_after(ip)
    if wait:
        raise HTTPException(status_code=429, detail=f"Too many attempts. Try again in {wait // 60 + 1} min.")

    ok = await run_in_threadpool(verify_password, req.password, settings.APP_PASSWORD_HASH)
    if not ok:
        auth.login_limiter.record_failure(ip)
        await asyncio.sleep(0.75)
        raise HTTPException(status_code=401, detail="Incorrect password")

    auth.login_limiter.record_success(ip)
    response.set_cookie(
        auth.COOKIE_NAME,
        auth.make_token(),
        max_age=settings.SESSION_HOURS * 3600,
        httponly=True,
        samesite="lax",
        secure=_is_https(request),
        path="/",
    )
    return {"authenticated": True}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(auth.COOKIE_NAME, path="/")
    return {"authenticated": False}
