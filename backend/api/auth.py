from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from config import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI, FRONTEND_URL,
)

router = APIRouter()

oauth = OAuth()
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/google")
async def login(request: Request):
    return await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI)


@router.get("/google/callback")
async def callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user  = token.get("userinfo")
    request.session["user"] = {
        "email":   user["email"],
        "name":    user["name"],
        "picture": user["picture"],
    }
    return RedirectResponse(url=FRONTEND_URL)


@router.get("/me")
async def me(request: Request):
    user = request.session.get("user")
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "user": user}


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"ok": True}
