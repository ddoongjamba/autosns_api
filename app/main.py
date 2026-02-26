"""
AutoSNS API - FastAPI 앱 진입점
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("DB 초기화 중...")
    await init_db()
    logger.info("DB 초기화 완료")

    # 스케줄러 시작
    from app.tasks.scheduler import start_scheduler, stop_scheduler
    await start_scheduler()
    logger.info("스케줄러 시작")

    yield

    # Shutdown
    from app.tasks.scheduler import stop_scheduler
    await stop_scheduler()
    logger.info("스케줄러 종료")


app = FastAPI(
    title="AutoSNS API",
    description="소상공인 대상 SNS 콘텐츠 자동화 SaaS API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_origin_regex=r"https://.*\.vercel\.app",  # Vercel 미리보기 URL 자동 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
from app.api.v1.router import router as v1_router  # noqa: E402
app.include_router(v1_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
