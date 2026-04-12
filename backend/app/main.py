from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.auth import router as auth_router
from app.api.behavior import router as behavior_router
from app.api.interview import router as interview_router
from app.api.llm_config import router as llm_config_router
from app.api.report import router as report_router
from app.api.resume import router as resume_router
from app.api.tts_metrics import router as tts_metrics_router
from app.config import settings
from app.database import init_db
from app.startup import run_startup_tasks
from app.ws.interview_ws import router as interview_ws_router

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    await run_startup_tasks()
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

allow_origins = ["*"] if settings.CORS_ALLOW_ALL else settings.cors_origins
allow_credentials = not settings.CORS_ALLOW_ALL

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # XSS protection
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(interview_router, prefix=settings.API_V1_PREFIX)
app.include_router(resume_router, prefix=settings.API_V1_PREFIX)
app.include_router(report_router, prefix=settings.API_V1_PREFIX)
app.include_router(behavior_router, prefix=settings.API_V1_PREFIX)
app.include_router(llm_config_router, prefix=settings.API_V1_PREFIX)
app.include_router(tts_metrics_router, prefix=settings.API_V1_PREFIX)
app.include_router(interview_ws_router, prefix="/ws")
