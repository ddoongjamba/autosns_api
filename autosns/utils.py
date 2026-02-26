"""
로깅 설정 및 공통 유틸리티
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 허용 이미지/동영상 확장자
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

_logger_initialized = False


def get_logger(name: str = "autosns") -> logging.Logger:
    """stdout + 로테이팅 파일에 동시 기록하는 로거를 반환한다."""
    global _logger_initialized

    logger = logging.getLogger(name)
    if _logger_initialized:
        return logger

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # stdout 핸들러
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # 파일 핸들러 (로테이팅, 최대 5 MB × 3개)
    try:
        from config import LOG_DIR  # 런타임 임포트로 순환 방지

        log_file = LOG_DIR / "autosns.log"
        fh = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        pass  # 파일 핸들러 실패해도 stdout은 유지

    _logger_initialized = True
    return logger


def validate_media(path: str | Path) -> Path:
    """미디어 파일 경로를 검증하고 Path 객체로 반환한다.

    Raises:
        FileNotFoundError: 파일이 없을 때
        ValueError: 지원하지 않는 확장자일 때
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"미디어 파일을 찾을 수 없습니다: {p}")
    if p.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"지원하지 않는 파일 형식: {p.suffix} "
            f"(허용: {', '.join(sorted(ALLOWED_EXTENSIONS))})"
        )
    return p


def is_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTENSIONS


def is_video(path: str | Path) -> bool:
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS
