from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    # Existing local bootstrap accounts may use reserved development domains
    # such as .local; validate new account input in UserCreate instead.
    email: str
    name: str
    role: str
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1, max_length=5000)


class CampaignRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    content: str
    status: str
    scheduled_for: datetime | None
    owner_id: int


class ScheduleRequest(BaseModel):
    scheduled_for: datetime


class ServiceAccountCreate(BaseModel):
    provider: str = Field(min_length=2, max_length=80)
    external_username: str = Field(min_length=2, max_length=160)


class ServiceAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider: str
    external_username: str
    user_id: int


class DashboardSummary(BaseModel):
    total_campaigns: int
    draft_campaigns: int
    pending_approval: int
    scheduled_campaigns: int
    published_campaigns: int
    connected_services: int
    upcoming: list[CampaignRead]


class KeywordAlertCreate(BaseModel):
    keyword: str = Field(min_length=1, max_length=120)
    provider: str = Field(default="all", min_length=2, max_length=80)


class KeywordAlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keyword: str
    provider: str
    is_active: bool
    user_id: int
