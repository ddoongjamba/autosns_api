"""
해시태그 관리

data/hashtags/*.txt 파일에서 해시태그를 로드하고,
여러 세트를 합치고, 셔플 후 최대 30개로 제한한다.
"""
import random
from pathlib import Path

from autosns.utils import get_logger

logger = get_logger(__name__)


def _load_file(path: Path) -> list[str]:
    """텍스트 파일에서 해시태그를 읽어 정규화된 리스트로 반환한다.

    - 빈 줄, # 시작 주석 줄 무시
    - # 접두사를 붙여 정규화
    """
    tags: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        tag = line if line.startswith("#") else f"#{line}"
        tags.append(tag)
    return tags


def load_hashtags(sets: list[str], hashtag_dir: Path, max_tags: int = 30) -> list[str]:
    """해시태그 세트 이름 목록을 받아 합치고 셔플 후 최대 max_tags개를 반환한다.

    Args:
        sets: 파일명(확장자 제외) 목록, 예: ["general", "food"]
        hashtag_dir: data/hashtags/ 경로
        max_tags: 최대 해시태그 수 (기본 30, Instagram 제한)

    Returns:
        정규화된 해시태그 리스트
    """
    pool: list[str] = []
    for name in sets:
        path = hashtag_dir / f"{name}.txt"
        if not path.exists():
            logger.warning("해시태그 파일을 찾을 수 없습니다: %s", path)
            continue
        loaded = _load_file(path)
        logger.debug("'%s' 세트에서 %d개 해시태그 로드", name, len(loaded))
        pool.extend(loaded)

    # 중복 제거 후 셔플
    pool = list(dict.fromkeys(pool))
    random.shuffle(pool)
    return pool[:max_tags]


def append_hashtags(caption: str, tags: list[str]) -> str:
    """캡션에 해시태그 블록을 추가한다.

    캡션과 해시태그 사이에 빈 줄 두 개를 삽입해
    Instagram의 '더 보기' 접기 기능 활용.
    """
    if not tags:
        return caption
    tag_block = " ".join(tags)
    if caption.strip():
        return f"{caption.strip()}\n\n.\n.\n.\n{tag_block}"
    return tag_block
