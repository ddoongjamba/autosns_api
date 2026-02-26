from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class CreatePostRequest(BaseModel):
    account_id: int
    post_type: str  # photo | carousel | video | reel
    caption: str = ""
    media_file_ids: List[int]  # MediaFile.id 목록
    scheduled_at: Optional[datetime] = None  # None이면 즉시 실행


class PostResponse(BaseModel):
    id: int
    account_id: int
    post_type: str
    caption: str
    media_paths: List[str]
    status: str
    error_message: Optional[str]
    scheduled_at: Optional[datetime]
    executed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class PostListResponse(BaseModel):
    items: List[PostResponse]
    total: int
    page: int
    size: int
