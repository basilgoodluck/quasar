import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from middleware.security import rate_limit
from api.auth import router as auth_router
from api.public import router as public_router
from api.private import router as private_router
from config import SECRET_KEY

app = FastAPI(title="ARC Agent API")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(rate_limit)

app.include_router(auth_router,    prefix="/auth")
app.include_router(public_router,  prefix="/api/public")
app.include_router(private_router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=4000, reload=True)
