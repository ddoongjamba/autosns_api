"""
User 모델
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

PLAN_LIMITS = {
    "free": 10,
    "standard": 20,
    "pro": -1,  # 무제한
}


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(20), default="free", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    ig_accounts: Mapped[list["IGAccount"]] = relationship(  # noqa: F821
        "IGAccount", back_populates="user", cascade="all, delete-orphan"
    )
    posts: Mapped[list["Post"]] = relationship(  # noqa: F821
        "Post", back_populates="user", cascade="all, delete-orphan"
    )
    media_files: Mapped[list["MediaFile"]] = relationship(  # noqa: F821
        "MediaFile", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def monthly_limit(self) -> int:
        return PLAN_LIMITS.get(self.plan, 10)
