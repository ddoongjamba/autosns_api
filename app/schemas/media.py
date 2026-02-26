from datetime import datetime

from pydantic import BaseModel


class MediaFileResponse(BaseModel):
    id: int
    filename: str
    mimetype: str
    size: int
    created_at: datetime

    model_config = {"from_attributes": True}
