from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Campaign, CampaignStatus, KeywordAlert, ServiceAccount, User
from app.schemas import CampaignCreate, ScheduleRequest


def create_campaign(db: Session, data: CampaignCreate, owner: User) -> Campaign:
    campaign = Campaign(name=data.name.strip(), content=data.content.strip(), owner_id=owner.id)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def submit_campaign(db: Session, campaign: Campaign, owner: User) -> Campaign:
    if campaign.owner_id != owner.id:
        raise HTTPException(status_code=403, detail="Only the campaign owner can submit it")
    if campaign.status not in {CampaignStatus.draft.value, CampaignStatus.rejected.value}:
        raise HTTPException(status_code=409, detail="Only draft or rejected campaigns can be submitted")
    campaign.status = CampaignStatus.submitted.value
    db.commit()
    db.refresh(campaign)
    return campaign


def decide_campaign(db: Session, campaign: Campaign, approved: bool) -> Campaign:
    if campaign.status != CampaignStatus.submitted.value:
        raise HTTPException(status_code=409, detail="Only submitted campaigns can be decided")
    campaign.status = CampaignStatus.approved.value if approved else CampaignStatus.rejected.value
    db.commit()
    db.refresh(campaign)
    return campaign


def schedule_campaign(db: Session, campaign: Campaign, data: ScheduleRequest) -> Campaign:
    if campaign.status != CampaignStatus.approved.value:
        raise HTTPException(status_code=409, detail="Only approved campaigns can be scheduled")
    if data.scheduled_for <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="Scheduled time must be in the future")
    campaign.scheduled_for = data.scheduled_for
    campaign.status = CampaignStatus.scheduled.value
    db.commit()
    db.refresh(campaign)
    return campaign


def connect_service_account(db: Session, user: User, provider: str, external_username: str) -> ServiceAccount:
    account = ServiceAccount(provider=provider.strip(), external_username=external_username.strip(), user_id=user.id)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def list_campaigns(db: Session, user: User) -> list[Campaign]:
    query = select(Campaign).order_by(Campaign.created_at.desc())
    if user.role not in {"admin", "approver", "publisher"}:
        query = query.where(Campaign.owner_id == user.id)
    return list(db.scalars(query))


def dashboard_summary(db: Session, user: User) -> dict:
    campaigns = list_campaigns(db, user)
    services = list(db.scalars(select(ServiceAccount).where(ServiceAccount.user_id == user.id)))
    upcoming = sorted(
        [campaign for campaign in campaigns if campaign.scheduled_for is not None and campaign.status == CampaignStatus.scheduled.value],
        key=lambda campaign: campaign.scheduled_for,
    )[:5]
    return {
        "total_campaigns": len(campaigns),
        "draft_campaigns": sum(c.status in {CampaignStatus.draft.value, CampaignStatus.rejected.value} for c in campaigns),
        "pending_approval": sum(c.status == CampaignStatus.submitted.value for c in campaigns),
        "scheduled_campaigns": sum(c.status == CampaignStatus.scheduled.value for c in campaigns),
        "published_campaigns": sum(c.status == CampaignStatus.published.value for c in campaigns),
        "connected_services": len(services),
        "upcoming": upcoming,
    }


def list_alerts(db: Session, user: User) -> list[KeywordAlert]:
    return list(db.scalars(select(KeywordAlert).where(KeywordAlert.user_id == user.id).order_by(KeywordAlert.created_at.desc())))


def create_alert(db: Session, user: User, keyword: str, provider: str) -> KeywordAlert:
    alert = KeywordAlert(keyword=keyword.strip(), provider=provider.strip(), user_id=user.id)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert
