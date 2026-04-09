import time
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from config import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI, FRONTEND_URL, ADMIN_EMAIL,
)
from redis_client import create_session, get_session, update_session, delete_session, SESSION_TTL
from middleware.security import SESSION_COOKIE, require_auth

router = APIRouter()
oauth = OAuth()
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    },
)

@router.get("/google")
async def login(request: Request):
    return await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI)

@router.get("/google/callback")
async def callback(request: Request):
    token  = await oauth.google.authorize_access_token(request)
    user   = token.get("userinfo")
    session_id = await create_session({
        "email":         user["email"],
        "name":          user["name"],
        "picture":       user["picture"],
        "role":          "admin" if user["email"] == ADMIN_EMAIL else "readonly",
        "access_token":  token.get("access_token"),
        "refresh_token": token.get("refresh_token"),
        "expires_at":    token.get("expires_at", time.time() + 3600),
    })
    response = RedirectResponse(url=FRONTEND_URL)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=SESSION_TTL,
    )
    return response

@router.get("/me")
async def me(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE)
    if not session_id:
        return {"authenticated": False}

    session = await get_session(session_id)
    if not session:
        return {"authenticated": False, "reason": "session_expired"}

    if time.time() > session.get("expires_at", 0):
        refresh_token = session.get("refresh_token")
        if not refresh_token:
            await delete_session(session_id)
            return {"authenticated": False, "reason": "token_expired"}
        try:
            new_token = await oauth.google.fetch_access_token(
                grant_type="refresh_token",
                refresh_token=refresh_token,
            )
            session["access_token"] = new_token["access_token"]
            session["expires_at"]   = new_token.get("expires_at", time.time() + 3600)
            await update_session(session_id, session)
        except Exception:
            await delete_session(session_id)
            return {"authenticated": False, "reason": "refresh_failed"}

    return {
        "authenticated": True,
        "user": {
            "email":   session["email"],
            "name":    session["name"],
            "picture": session["picture"],
            "role":    session["role"],
        }
    }

@router.post("/logout")
async def logout(request: Request, session=Depends(require_auth)):
    session_id = request.cookies.get(SESSION_COOKIE)
    await delete_session(session_id)
    response = JSONResponse(content={"ok": True})
    response.delete_cookie(SESSION_COOKIE)
    return response