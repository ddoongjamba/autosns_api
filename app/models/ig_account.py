"""
IGAccount 모델 - 연결된 Instagram 계정
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class IGAccount(Base):
    __tablename__ = "ig_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    encrypted_password: Mapped[str] = mapped_column(String(500), nullable=False)
    session_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="ig_accounts")  # noqa: F821
    posts: Mapped[list["Post"]] = relationship(  # noqa: F821
        "Post", back_populates="ig_account", cascade="all, delete-orphan"
    )
