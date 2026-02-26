"""
Instagram 계정 연결/관리 서비스
autosns.client.get_client()를 run_in_executor로 비동기 래핑
"""
import asyncio
import sys
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decrypt_password, encrypt_password
from app.models.ig_account import IGAccount
from app.schemas.ig_account import IGAccountResponse, LinkAccountRequest

# autosns 패키지 경로 추가
_AUTOSNS_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_AUTOSNS_ROOT) not in sys.path:
    sys.path.insert(0, str(_AUTOSNS_ROOT))


async def link_account(db: AsyncSession, user_id: int, req: LinkAccountRequest) -> IGAccountResponse:
    """Instagram 계정을 로그인 검증 후 DB에 저장한다."""
    session_dir = settings.SESSIONS_DIR / str(user_id)
    session_dir.mkdir(parents=True, exist_ok=True)

    # 로그인 검증 (동기 instagrapi를 executor에서 실행)
    loop = asyncio.get_event_loop()
    try:
        from autosns.client import get_client
        await loop.run_in_executor(
            None,
            get_client,
            req.username,
            req.password,
            session_dir,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Instagram 로그인 실패: {e}",
        )

    # 기존 계정 중복 확인
    result = await db.execute(
        select(IGAccount).where(
            IGAccount.user_id == user_id,
            IGAccount.username == req.username,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        # 비밀번호 업데이트 (재연결)
        existing.encrypted_password = encrypt_password(req.password)
        existing.session_path = str(session_dir / f"{req.username}.json")
        await db.commit()
        await db.refresh(existing)
        return IGAccountResponse.model_validate(existing)

    account = IGAccount(
        user_id=user_id,
        username=req.username,
        encrypted_password=encrypt_password(req.password),
        session_path=str(session_dir / f"{req.username}.json"),
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return IGAccountResponse.model_validate(account)


async def list_accounts(db: AsyncSession, user_id: int) -> list[IGAccountResponse]:
    result = await db.execute(
        select(IGAccount).where(IGAccount.user_id == user_id).order_by(IGAccount.id)
    )
    accounts = result.scalars().all()
    return [IGAccountResponse.model_validate(a) for a in accounts]


async def delete_account(db: AsyncSession, user_id: int, account_id: int) -> None:
    result = await db.execute(
        select(IGAccount).where(IGAccount.id == account_id, IGAccount.user_id == user_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")

    await db.delete(account)
    await db.commit()
