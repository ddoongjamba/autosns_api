"""
포스팅 서비스 - autosns.uploader 비동기 래핑 (핵심 통합)
"""
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decrypt_password
from app.models.ig_account import IGAccount
from app.models.media_file import MediaFile
from app.models.post import Post
from app.models.user import User
from app.schemas.post import CreatePostRequest, PostListResponse, PostResponse
from app.services.quota_service import check_quota

_AUTOSNS_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_AUTOSNS_ROOT) not in sys.path:
    sys.path.insert(0, str(_AUTOSNS_ROOT))


async def create_post(db: AsyncSession, user: User, req: CreatePostRequest) -> PostResponse:
    """포스팅 생성 - 즉시 실행 또는 예약."""
    # 할당량 체크
    await check_quota(db, user)

    # IG 계정 소유권 확인
    acc_result = await db.execute(
        select(IGAccount).where(
            IGAccount.id == req.account_id,
            IGAccount.user_id == user.id,
        )
    )
    account = acc_result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Instagram 계정을 찾을 수 없습니다.")

    # 미디어 파일 확인 및 경로 수집
    media_paths: list[str] = []
    for file_id in req.media_file_ids:
        mf_result = await db.execute(
            select(MediaFile).where(MediaFile.id == file_id, MediaFile.user_id == user.id)
        )
        mf = mf_result.scalar_one_or_none()
        if not mf:
            raise HTTPException(status_code=404, detail=f"미디어 파일 {file_id}를 찾을 수 없습니다.")
        media_paths.append(mf.filepath)

    # Post 생성
    post = Post(
        user_id=user.id,
        account_id=account.id,
        post_type=req.post_type,
        caption=req.caption,
        status="pending",
        scheduled_at=req.scheduled_at,
    )
    post.media_paths = media_paths
    db.add(post)
    await db.commit()
    await db.refresh(post)

    # 즉시 실행 (scheduled_at 없음)
    if req.scheduled_at is None:
        await execute_post(db, post.id)
        await db.refresh(post)

    return PostResponse.model_validate(post)


async def execute_post(db: AsyncSession, post_id: int) -> None:
    """Post를 실제로 Instagram에 업로드한다."""
    result = await db.execute(
        select(Post).where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        return

    acc_result = await db.execute(
        select(IGAccount).where(IGAccount.id == post.account_id)
    )
    account = acc_result.scalar_one_or_none()
    if not account:
        post.status = "failed"
        post.error_message = "연결된 Instagram 계정을 찾을 수 없습니다."
        await db.commit()
        return

    post.status = "running"
    await db.commit()

    try:
        from autosns.client import get_client
        from autosns.uploader import upload_carousel, upload_photo, upload_video

        username = account.username
        password = decrypt_password(account.encrypted_password)
        session_dir = settings.SESSIONS_DIR / str(account.user_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        loop = asyncio.get_event_loop()

        # 클라이언트 획득
        cl = await loop.run_in_executor(None, get_client, username, password, session_dir)

        paths = post.media_paths
        caption = post.caption
        post_type = post.post_type

        if post_type == "photo":
            await loop.run_in_executor(None, upload_photo, cl, paths[0], caption)
        elif post_type == "carousel":
            await loop.run_in_executor(None, upload_carousel, cl, paths, caption)
        elif post_type == "video":
            await loop.run_in_executor(None, upload_video, cl, paths[0], caption, False)
        elif post_type == "reel":
            await loop.run_in_executor(None, upload_video, cl, paths[0], caption, True)
        else:
            raise ValueError(f"지원하지 않는 post_type: {post_type}")

        post.status = "done"
        post.executed_at = datetime.now(timezone.utc)

    except Exception as e:
        post.status = "failed"
        post.error_message = str(e)

    await db.commit()


async def list_posts(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    size: int = 20,
) -> PostListResponse:
    from sqlalchemy import func

    total_result = await db.execute(
        select(func.count(Post.id)).where(Post.user_id == user_id)
    )
    total = total_result.scalar_one()

    offset = (page - 1) * size
    result = await db.execute(
        select(Post)
        .where(Post.user_id == user_id)
        .order_by(Post.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    posts = result.scalars().all()

    return PostListResponse(
        items=[PostResponse.model_validate(p) for p in posts],
        total=total,
        page=page,
        size=size,
    )


async def get_post(db: AsyncSession, user_id: int, post_id: int) -> PostResponse:
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="포스팅을 찾을 수 없습니다.")
    return PostResponse.model_validate(post)


async def delete_post(db: AsyncSession, user_id: int, post_id: int) -> None:
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == user_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="포스팅을 찾을 수 없습니다.")
    if post.status == "running":
        raise HTTPException(status_code=409, detail="실행 중인 포스팅은 삭제할 수 없습니다.")

    await db.delete(post)
    await db.commit()
