"""
구독 API: /plans, /me/subscription, /me/usage, /me/subscription/upgrade
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.subscription import PlanInfo, SubscriptionResponse, UpgradeRequest, UsageResponse
from app.services.quota_service import get_monthly_usage

router = APIRouter(tags=["subscription"])

PLANS: List[PlanInfo] = [
    PlanInfo(
        name="free",
        price_krw=0,
        monthly_limit=10,
        description="월 10회 포스팅, 기본 기능",
    ),
    PlanInfo(
        name="standard",
        price_krw=29000,
        monthly_limit=20,
        description="월 20회 포스팅, AI 캡션 생성",
    ),
    PlanInfo(
        name="pro",
        price_krw=59000,
        monthly_limit=-1,
        description="무제한 포스팅, 모든 기능 포함",
    ),
]


@router.get("/plans", response_model=List[PlanInfo])
async def list_plans():
    """구독 플랜 목록 조회 (인증 불필요)."""
    return PLANS


@router.get("/me/subscription", response_model=SubscriptionResponse)
async def my_subscription(current_user: User = Depends(get_current_user)):
    """내 구독 현황 조회."""
    return SubscriptionResponse(
        plan=current_user.plan,
        monthly_limit=current_user.monthly_limit,
        is_active=current_user.is_active,
    )


@router.get("/me/usage", response_model=UsageResponse)
async def my_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """이번 달 포스팅 사용량 조회."""
    used = await get_monthly_usage(db, current_user.id)
    limit = current_user.monthly_limit
    remaining = None if limit == -1 else max(0, limit - used)

    return UsageResponse(
        plan=current_user.plan,
        used=used,
        limit=limit,
        remaining=remaining,
    )


@router.post("/me/subscription/upgrade", response_model=SubscriptionResponse)
async def upgrade_subscription(
    req: UpgradeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """구독 플랜 변경."""
    current_user.plan = req.plan
    await db.commit()
    await db.refresh(current_user)
    return SubscriptionResponse(
        plan=current_user.plan,
        monthly_limit=current_user.monthly_limit,
        is_active=current_user.is_active,
    )
