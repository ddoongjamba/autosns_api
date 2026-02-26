"""
결제 API: /me/payment/verify
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.payment import PaymentVerifyRequest, PaymentVerifyResponse
from app.schemas.subscription import SubscriptionResponse
from app.services import payment_service

router = APIRouter(tags=["payment"])


@router.post("/me/payment/verify", response_model=PaymentVerifyResponse)
async def verify_and_upgrade(
    req: PaymentVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    아임포트 결제를 서버에서 검증한 뒤 구독 플랜을 업그레이드한다.
    결제 금액과 플랜 가격이 일치해야 한다.
    """
    try:
        await payment_service.verify_payment(req.imp_uid, req.plan)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    current_user.plan = req.plan
    await db.commit()
    await db.refresh(current_user)

    return PaymentVerifyResponse(
        success=True,
        plan=current_user.plan,
        message=f"{req.plan} 플랜으로 업그레이드되었습니다.",
    )
