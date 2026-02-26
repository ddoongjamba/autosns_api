"""
미디어 업로드 API: /uploads
"""
from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.media import MediaFileResponse
from app.services import media_service

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("", response_model=MediaFileResponse, status_code=201)
async def upload_media(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """미디어 파일(이미지/동영상) 업로드."""
    return await media_service.save_upload(db, current_user.id, file)
