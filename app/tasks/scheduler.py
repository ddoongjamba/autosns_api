"""
APScheduler - AsyncIOScheduler
1분 주기로 예약 포스팅(pending + scheduled_at <= now)을 실행한다.
"""
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def poll_pending_posts() -> None:
    """scheduled_at이 지났고 status=pending인 Post를 실행한다."""
    from app.core.database import AsyncSessionLocal
    from app.models.post import Post
    from app.services.post_service import execute_post

    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Post).where(
                Post.status == "pending",
                Post.scheduled_at.isnot(None),
                Post.scheduled_at <= now,
            )
        )
        posts = result.scalars().all()

        if posts:
            logger.info("예약 포스팅 %d건 실행 시작", len(posts))

        for post in posts:
            try:
                await execute_post(db, post.id)
            except Exception as e:
                logger.error("포스팅 %d 실행 오류: %s", post.id, e)


async def start_scheduler() -> None:
    global _scheduler
    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        poll_pending_posts,
        trigger="interval",
        minutes=1,
        id="poll_pending_posts",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info("스케줄러 시작 (1분 주기 폴링)")


async def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("스케줄러 종료")
