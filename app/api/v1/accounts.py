"""
Instagram 계정 API: /accounts
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.ig_account import IGAccountResponse, LinkAccountRequest
from app.services import account_service

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/link", response_model=IGAccountResponse, status_code=201)
async def link_account(
    req: LinkAccountRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Instagram 계정을 서비스에 연결한다."""
    return await account_service.link_account(db, current_user.id, req)


@router.get("", response_model=List[IGAccountResponse])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """연결된 Instagram 계정 목록 조회."""
    return await account_service.list_accounts(db, current_user.id)


@router.delete("/{account_id}", status_code=204)
async def delete_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Instagram 계정 연결 해제."""
    await account_service.delete_account(db, current_user.id, account_id)
