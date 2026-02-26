"""
아임포트(PortOne) 결제 검증 서비스
"""
import httpx

from app.core.config import settings

IAMPORT_API = "https://api.iamport.kr"

# 플랜별 결제 금액 (원)
PLAN_PRICES = {
    "standard": 29000,
    "pro": 59000,
}


async def _get_access_token() -> str:
    """아임포트 REST API 액세스 토큰 발급."""
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{IAMPORT_API}/users/getToken",
            json={"imp_key": settings.IMP_KEY, "imp_secret": settings.IMP_SECRET},
            timeout=10,
        )
        res.raise_for_status()
        data = res.json()
        return data["response"]["access_token"]


async def verify_payment(imp_uid: str, plan: str) -> dict:
    """
    아임포트 서버에서 결제 정보를 조회하여 검증한다.

    Returns:
        {"valid": bool, "amount": int, "status": str}
    Raises:
        ValueError: 검증 실패 시
    """
    if not settings.IMP_KEY or not settings.IMP_SECRET:
        raise ValueError("아임포트 API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")

    expected_amount = PLAN_PRICES.get(plan)
    if expected_amount is None:
        raise ValueError(f"알 수 없는 플랜: {plan}")

    token = await _get_access_token()

    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{IAMPORT_API}/payments/{imp_uid}",
            headers={"Authorization": token},
            timeout=10,
        )
        res.raise_for_status()
        payment = res.json()["response"]

    if payment["status"] != "paid":
        raise ValueError(f"결제 상태가 올바르지 않습니다: {payment['status']}")

    if payment["amount"] != expected_amount:
        raise ValueError(
            f"결제 금액 불일치 (기대: {expected_amount}원, 실제: {payment['amount']}원)"
        )

    return {"valid": True, "amount": payment["amount"], "status": payment["status"]}
