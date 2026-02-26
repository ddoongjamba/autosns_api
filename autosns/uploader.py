"""
미디어 업로드: 사진 / 캐러셀 / 동영상
"""
from pathlib import Path

from instagrapi import Client
from instagrapi.types import Media

from autosns.utils import get_logger, validate_media, is_image, is_video

logger = get_logger(__name__)


def upload_photo(cl: Client, media_path: str | Path, caption: str = "") -> Media:
    """단일 이미지를 Instagram에 포스팅한다.

    Args:
        cl: 로그인된 instagrapi Client
        media_path: 업로드할 이미지 파일 경로
        caption: 포스팅 캡션 (해시태그 포함)

    Returns:
        업로드된 Media 객체
    """
    path = validate_media(media_path)
    if not is_image(path):
        raise ValueError(f"사진 업로드에는 이미지 파일이 필요합니다: {path}")

    logger.info("사진 업로드 시작: %s", path.name)
    media = cl.photo_upload(path, caption)
    logger.info("사진 업로드 완료. media_id=%s", media.pk)
    return media


def upload_carousel(
    cl: Client,
    media_paths: list[str | Path],
    caption: str = "",
) -> Media:
    """캐러셀(앨범) 포스팅 - 최대 10개 이미지/동영상.

    Args:
        cl: 로그인된 instagrapi Client
        media_paths: 업로드할 파일 경로 목록 (1~10개)
        caption: 포스팅 캡션

    Returns:
        업로드된 Media 객체
    """
    if not media_paths:
        raise ValueError("캐러셀에는 최소 1개의 미디어가 필요합니다.")
    if len(media_paths) > 10:
        raise ValueError(f"캐러셀 최대 개수는 10개입니다. (입력: {len(media_paths)})")

    paths = [validate_media(p) for p in media_paths]
    logger.info("캐러셀 업로드 시작: %d개 파일", len(paths))
    media = cl.album_upload(paths, caption)
    logger.info("캐러셀 업로드 완료. media_id=%s", media.pk)
    return media


def upload_video(
    cl: Client,
    media_path: str | Path,
    caption: str = "",
    is_reel: bool = False,
) -> Media:
    """동영상(릴스) 포스팅.

    Args:
        cl: 로그인된 instagrapi Client
        media_path: 업로드할 동영상 파일 경로
        caption: 포스팅 캡션
        is_reel: True면 릴스로 업로드

    Returns:
        업로드된 Media 객체
    """
    path = validate_media(media_path)
    if not is_video(path):
        raise ValueError(f"동영상 업로드에는 영상 파일이 필요합니다: {path}")

    logger.info("동영상 업로드 시작: %s (reel=%s)", path.name, is_reel)
    if is_reel:
        media = cl.clip_upload(path, caption)
    else:
        media = cl.video_upload(path, caption)
    logger.info("동영상 업로드 완료. media_id=%s", media.pk)
    return media
