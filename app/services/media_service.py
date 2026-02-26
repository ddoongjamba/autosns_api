"""
미디어 파일 업로드 서비스
autosns.utils.validate_media 재사용
"""
import sys
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
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


async def save_upload(db: AsyncSession, user_id: int, file: UploadFile) -> MediaFileResponse:
    """업로드 파일을 저장하고 DB에 기록한다."""
    if file.content_type not in ALLOWED_MIMETYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"지원하지 않는 파일 형식: {file.content_type}",
        )

    # 파일 내용 읽기
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="파일 크기는 100MB를 초과할 수 없습니다.",
        )

    # 사용자별 디렉토리
    user_dir = settings.UPLOADS_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    # 고유 파일명 (UUID + 원본 확장자)
    suffix = Path(file.filename or "").suffix.lower() or ".bin"
    unique_name = f"{uuid.uuid4().hex}{suffix}"
    save_path = user_dir / unique_name

    save_path.write_bytes(content)

    # autosns validate_media로 확장자 검증
    try:
        from autosns.utils import validate_media
        validate_media(save_path)
    except ValueError as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(e))

    media = MediaFile(
        user_id=user_id,
        filename=file.filename or unique_name,
        filepath=str(save_path),
        mimetype=file.content_type,
        size=len(content),
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)
    return MediaFileResponse.model_validate(media)
