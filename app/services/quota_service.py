"""
월별 사용량 체크 → 초과 시 HTTP 429
"""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post
from app.models.user import User


async def get_monthly_usage(db: AsyncSession, user_id: int) -> int:
    """이번 달 완료(done) 포스팅 수 반환."""
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(func.count(Post.id)).where(
            Post.user_id == user_id,
            Post.status == "done",
            Post.executed_at >= start_of_month,
        )
    )
    return result.scalar_one() or 0


async def check_quota(db: AsyncSession, user: User) -> None:
    """사용량 초과 시 HTTP 429 발생."""
    limit = user.monthly_limit
    if limit == -1:
        return  # pro: 무제한

    used = await get_monthly_usage(db, user.id)
    if used >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"이번 달 포스팅 한도({limit}회)를 초과했습니다. 플랜을 업그레이드하세요.",
            headers={"X-RateLimit-Limit": str(limit), "X-RateLimit-Remaining": "0"},
        )
