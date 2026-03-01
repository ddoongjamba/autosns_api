"""
Cloudflare R2 (S3 호환) 파일 저장소
R2_ACCOUNT_ID 등이 설정되지 않으면 로컬 파일시스템 사용 (개발 환경)
"""
import asyncio
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from app.core.config import settings


def _get_s3_client():
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def _is_r2_enabled() -> bool:
    return bool(settings.R2_ACCOUNT_ID and settings.R2_ACCESS_KEY_ID and settings.R2_SECRET_ACCESS_KEY)


async def upload_file(content: bytes, key: str, content_type: str) -> str:
    """파일을 R2에 업로드하고 공개 URL 반환. R2 미설정 시 로컬 저장."""
    if not _is_r2_enabled():
        return await _save_local(content, key)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _upload_r2, content, key, content_type)
    return f"{settings.R2_PUBLIC_URL.rstrip('/')}/{key}"


async def download_to_tempfile(file_url_or_path: str, suffix: str = "") -> str:
    """R2 URL 또는 로컬 경로에서 임시 파일로 다운로드. 임시 파일 경로 반환."""
    if file_url_or_path.startswith("http"):
        import httpx
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _download_http, file_url_or_path, suffix)
    # 이미 로컬 경로
    return file_url_or_path


def _upload_r2(content: bytes, key: str, content_type: str):
    client = _get_s3_client()
    client.put_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=key,
        Body=content,
        ContentType=content_type,
    )


def _download_http(url: str, suffix: str) -> str:
    import httpx
    with httpx.Client(timeout=60) as client:
        response = client.get(url)
        response.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.write(response.content)
    tmp.close()
    return tmp.name


async def _save_local(content: bytes, key: str) -> str:
    """로컬 개발 환경용: uploads 디렉토리에 저장."""
    save_path = settings.UPLOADS_DIR / key
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(content)
    return str(save_path)
