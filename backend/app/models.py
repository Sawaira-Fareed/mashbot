from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, Enum):
    contributor = "contributor"
    approver = "approver"
    publisher = "publisher"
    admin = "admin"


class CampaignStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"
    scheduled = "scheduled"
    published = "published"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default=UserRole.contributor.value)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="owner")
    service_accounts: Mapped[list["ServiceAccount"]] = relationship(back_populates="user")


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default=CampaignStatus.draft.value)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    owner: Mapped[User] = relationship(back_populates="campaigns")


class ServiceAccount(Base):
    __tablename__ = "service_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(80))
    external_username: Mapped[str] = mapped_column(String(160))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    user: Mapped[User] = relationship(back_populates="service_accounts")


class KeywordAlert(Base):
    __tablename__ = "keyword_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    keyword: Mapped[str] = mapped_column(String(120))
    provider: Mapped[str] = mapped_column(String(80), default="all")
    is_active: Mapped[bool] = mapped_column(default=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

