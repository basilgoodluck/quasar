from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from redis_client import get_session, rate_limit_check

SESSION_COOKIE = "qsid"

async def get_current_session(request: Request) -> tuple[str, dict]:
    session_id = request.cookies.get(SESSION_COOKIE)
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session not found or expired")
    return session_id, session

async def require_auth(request: Request) -> dict:
    _, session = await get_current_session(request)
    return session

async def require_admin(session: dict = Depends(require_auth)) -> dict:
    if session.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return session

async def rate_limit(request: Request, call_next):
    ip = request.client.host
    if await rate_limit_check(ip):
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})
    return await call_next(request)