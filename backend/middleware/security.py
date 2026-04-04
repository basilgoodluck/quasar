from fastapi import Request
from fastapi.responses import JSONResponse
from collections import defaultdict
import time

_requests: dict = defaultdict(list)
RATE_LIMIT       = 60
WINDOW_SECONDS   = 60


async def rate_limit(request: Request, call_next):
    ip  = request.client.host
    now = time.time()

    _requests[ip] = [t for t in _requests[ip] if now - t < WINDOW_SECONDS]

    if len(_requests[ip]) >= RATE_LIMIT:
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})

    _requests[ip].append(now)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"]        = "DENY"
    response.headers["X-XSS-Protection"]       = "1; mode=block"
    return response
