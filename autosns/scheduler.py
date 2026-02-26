"""
예약 포스팅 엔진

data/queue/*.json 파일을 읽어 APScheduler DateTrigger로 등록한다.
- 성공: <name>.json → <name>.done
- 실패: <name>.json → <name>.failed
"""
import json
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.date import DateTrigger

from autosns.utils import get_logger

logger = get_logger(__name__)


def _rename(path: Path, suffix: str) -> None:
    target = path.with_suffix(suffix)
    path.rename(target)
    logger.debug("파일 이름 변경: %s → %s", path.name, target.name)


def _execute_job(job_file: Path) -> None:
    """단일 예약 파일을 읽어 포스팅을 실행한다."""
    logger.info("예약 포스팅 실행: %s", job_file.name)
    try:
        data = json.loads(job_file.read_text(encoding="utf-8"))
        _run_post(data)
        _rename(job_file, ".done")
        logger.info("예약 포스팅 성공: %s", job_file.name)
    except Exception as e:
        logger.error("예약 포스팅 실패 (%s): %s", job_file.name, e, exc_info=True)
        _rename(job_file, ".failed")


def _run_post(data: dict) -> None:
    """data dict의 내용으로 실제 포스팅을 수행한다."""
    from autosns.client import build_client
    from autosns.uploader import upload_photo, upload_carousel, upload_video
    from autosns.hashtags import load_hashtags, append_hashtags
    from config import HASHTAG_DIR, HASHTAG_MAX

    media_type = data.get("type", "photo")
    caption = data.get("caption", "")
    hashtag_sets = data.get("hashtags", [])
    media = data.get("media", [])

    if isinstance(media, str):
        media = [media]

    # 해시태그 추가
    if hashtag_sets:
        tags = load_hashtags(hashtag_sets, HASHTAG_DIR, HASHTAG_MAX)
        caption = append_hashtags(caption, tags)

    cl = build_client()

    if media_type == "photo":
        upload_photo(cl, media[0], caption)
    elif media_type == "carousel":
        upload_carousel(cl, media, caption)
    elif media_type in ("video", "reel"):
        upload_video(cl, media[0], caption, is_reel=(media_type == "reel"))
    else:
        raise ValueError(f"알 수 없는 미디어 타입: {media_type}")


def load_pending_jobs(queue_dir: Path) -> list[Path]:
    """큐 디렉토리에서 .json 파일 목록을 반환한다."""
    return sorted(queue_dir.glob("*.json"))


def run_scheduler(queue_dir: Path) -> None:
    """큐 디렉토리의 예약 파일을 등록하고 스케줄러를 실행한다."""
    scheduler = BlockingScheduler(timezone="Asia/Seoul")

    jobs = load_pending_jobs(queue_dir)
    if not jobs:
        logger.info("예약된 포스팅 파일이 없습니다: %s", queue_dir)

    for job_file in jobs:
        try:
            data = json.loads(job_file.read_text(encoding="utf-8"))
            run_at_str = data.get("run_at")
            if not run_at_str:
                logger.warning("run_at 필드가 없습니다: %s", job_file.name)
                continue

            run_at = datetime.fromisoformat(run_at_str)
            scheduler.add_job(
                _execute_job,
                trigger=DateTrigger(run_date=run_at),
                args=[job_file],
                id=job_file.stem,
                name=job_file.stem,
            )
            logger.info("예약 등록: %s → %s", job_file.name, run_at)
        except Exception as e:
            logger.error("예약 파일 파싱 실패 (%s): %s", job_file.name, e)

    logger.info("스케줄러 시작. 종료하려면 Ctrl+C를 누르세요.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("스케줄러가 종료되었습니다.")
