from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    await run_startup_tasks()
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

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


app.include_router(interview_router, prefix=settings.API_V1_PREFIX)
app.include_router(resume_router, prefix=settings.API_V1_PREFIX)
app.include_router(report_router, prefix=settings.API_V1_PREFIX)
app.include_router(behavior_router, prefix=settings.API_V1_PREFIX)
app.include_router(llm_config_router, prefix=settings.API_V1_PREFIX)
app.include_router(tts_metrics_router, prefix=settings.API_V1_PREFIX)
app.include_router(interview_ws_router, prefix="/ws")
