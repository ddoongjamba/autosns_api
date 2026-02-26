from typing import Literal

from pydantic import BaseModel


class PaymentVerifyRequest(BaseModel):
    imp_uid: str       # 아임포트 결제 고유번호
    merchant_uid: str  # 주문 고유번호 (프론트에서 생성)
    plan: Literal["standard", "pro"]  # 결제한 플랜


class PaymentVerifyResponse(BaseModel):
    success: bool
    plan: str
    message: str
