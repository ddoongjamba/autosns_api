"""
미디어 파일 업로드 서비스 — Cloudflare R2 저장
"""
import sys
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.storage import upload_file
from app.models.media_file import MediaFile
from app.schemas.media import MediaFileResponse

_AUTOSNS_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_AUTOSNS_ROOT) not in sys.path:
    sys.path.insert(0, str(_AUTOSNS_ROOT))

ALLOWED_MIMETYPES = {
    "image/jpeg", "image/png", "image/webp",
    "video/mp4", "video/quicktime",
}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
}


async def save_upload(db: AsyncSession, user_id: int, file: UploadFile) -> MediaFileResponse:
    """업로드 파일을 R2에 저장하고 DB에 기록한다."""
    if file.content_type not in ALLOWED_MIMETYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"지원하지 않는 파일 형식: {file.content_type}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="파일 크기는 100MB를 초과할 수 없습니다.",
        )

    suffix = MIME_TO_EXT.get(file.content_type, Path(file.filename or "").suffix.lower() or ".bin")
    unique_name = f"{uuid.uuid4().hex}{suffix}"
    r2_key = f"{user_id}/{unique_name}"

    # R2 업로드 (미설정 시 로컬 저장)
    file_url = await upload_file(content, r2_key, file.content_type)

    media = MediaFile(
        user_id=user_id,
        filename=file.filename or unique_name,
        filepath=file_url,  # R2 URL 또는 로컬 경로
        mimetype=file.content_type,
        size=len(content),
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)
    return MediaFileResponse.model_validate(media)
