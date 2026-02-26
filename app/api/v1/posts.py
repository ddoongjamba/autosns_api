"""
포스팅 API: /posts
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.post import CreatePostRequest, PostListResponse, PostResponse
from app.services import post_service

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("", response_model=PostResponse, status_code=201)
async def create_post(
    req: CreatePostRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """포스팅 생성 (즉시 실행 또는 예약)."""
    return await post_service.create_post(db, current_user, req)


@router.get("", response_model=PostListResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """포스팅 목록 조회 (페이지네이션)."""
    return await post_service.list_posts(db, current_user.id, page, size)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """포스팅 상세 조회."""
    return await post_service.get_post(db, current_user.id, post_id)


@router.delete("/{post_id}", status_code=204)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """포스팅 삭제."""
    await post_service.delete_post(db, current_user.id, post_id)
