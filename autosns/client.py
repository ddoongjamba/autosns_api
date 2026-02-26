"""
Instagram 로그인 & 세션 관리

세션 재사용 우선 전략:
  1. data/sessions/<username>.json 로드
  2. account_info() 로 세션 유효성 검증
  3. 만료/없음 → 풀 로그인 → 세션 저장
"""
import json
from pathlib import Path

from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired

from autosns.utils import get_logger

logger = get_logger(__name__)


def _session_path(username: str, session_dir: Path) -> Path:
    return session_dir / f"{username}.json"


def get_client(username: str, password: str, session_dir: Path) -> Client:
    """로그인된 instagrapi Client를 반환한다."""
    cl = Client()
    cl.delay_range = [2, 5]  # 봇 감지 회피

    session_file = _session_path(username, session_dir)

    if session_file.exists():
        logger.info("저장된 세션을 로드합니다: %s", session_file)
        try:
            cl.load_settings(session_file)
            cl.login(username, password)  # 세션 갱신용 (토큰 유효 시 빠름)
            cl.get_timeline_feed()  # 세션 유효성 검증
            logger.info("세션 재사용 성공")
            return cl
        except (LoginRequired, ChallengeRequired, Exception) as e:
            logger.warning("세션이 만료되었거나 유효하지 않습니다: %s", e)
            logger.info("새로 로그인합니다...")

    # 풀 로그인
    cl = Client()
    cl.delay_range = [2, 5]
    cl.login(username, password)

    session_dir.mkdir(parents=True, exist_ok=True)
    cl.dump_settings(session_file)
    logger.info("로그인 성공. 세션을 저장했습니다: %s", session_file)
    return cl


def build_client() -> Client:
    """config.py 값으로 Client를 빌드하는 편의 함수."""
    from config import IG_USERNAME, IG_PASSWORD, SESSION_DIR, DELAY_MIN, DELAY_MAX

    cl = get_client(IG_USERNAME, IG_PASSWORD, SESSION_DIR)
    cl.delay_range = [DELAY_MIN, DELAY_MAX]
    return cl
