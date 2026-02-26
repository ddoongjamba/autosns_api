from typing import List, Optional

from pydantic import BaseModel


class GenerateCaptionRequest(BaseModel):
    topic: str
    tone: str = "친근한"  # 친근한 | 전문적 | 유머러스
    hashtag_count: int = 10
    language: str = "ko"
    extra_context: Optional[str] = None


class GenerateCaptionResponse(BaseModel):
    caption: str
    hashtags: List[str]
    full_text: str  # caption + hashtags 합본
