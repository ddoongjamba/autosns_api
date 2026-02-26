from typing import Literal, Optional

from pydantic import BaseModel


class UpgradeRequest(BaseModel):
    plan: Literal["free", "standard", "pro"]


class PlanInfo(BaseModel):
    name: str
    price_krw: int
    monthly_limit: int  # -1 = 무제한
    description: str


class SubscriptionResponse(BaseModel):
    plan: str
    monthly_limit: int
    is_active: bool


class UsageResponse(BaseModel):
    plan: str
    used: int
    limit: int  # -1 = 무제한
    remaining: Optional[int]  # None = 무제한
