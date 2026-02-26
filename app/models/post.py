"""
Post 모델 - 포스팅 작업
"""
import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# status: pending | running | done | failed | cancelled
# type: photo | carousel | video | reel


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("ig_accounts.id"), nullable=False, index=True)
    post_type: Mapped[str] = mapped_column(String(20), nullable=False)  # photo|carousel|video|reel
    caption: Mapped[str] = mapped_column(Text, default="", nullable=False)
    _media_paths: Mapped[str] = mapped_column("media_paths", Text, default="[]", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="posts")  # noqa: F821
    ig_account: Mapped["IGAccount"] = relationship("IGAccount", back_populates="posts")  # noqa: F821

    @property
    def media_paths(self) -> list[str]:
        return json.loads(self._media_paths)

    @media_paths.setter
    def media_paths(self, value: list[str]) -> None:
        self._media_paths = json.dumps(value)
