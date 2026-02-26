from datetime import datetime

from pydantic import BaseModel


class LinkAccountRequest(BaseModel):
    username: str
    password: str


class IGAccountResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}
