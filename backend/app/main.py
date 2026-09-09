from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Campaign, KeywordAlert, ServiceAccount, User, UserRole
from app.schemas import CampaignCreate, CampaignRead, DashboardSummary, KeywordAlertCreate, KeywordAlertRead, ScheduleRequest, ServiceAccountCreate, ServiceAccountRead, Token, UserCreate, UserRead, UserUpdate
from app.security import create_access_token, current_user, hash_password, require_roles, verify_password
from app.services import connect_service_account, create_alert, create_campaign, dashboard_summary, decide_campaign, list_alerts, list_campaigns, schedule_campaign, submit_campaign


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.bootstrap_admin_email and settings.bootstrap_admin_password:
        db = next(get_db())
        try:
            existing = db.scalar(select(User).where(User.email == settings.bootstrap_admin_email.lower()))
            if not existing:
                db.add(User(email=settings.bootstrap_admin_email.lower(), name="Administrator", password_hash=hash_password(settings.bootstrap_admin_password), role=UserRole.admin.value))
                db.commit()
        finally:
            db.close()
    yield


app = FastAPI(title="Mashbot API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/register", response_model=UserRead, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    email = str(data.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(email=email, name=data.name.strip(), password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/auth/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if not user or not user.is_active or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return Token(access_token=create_access_token(user.id))


@app.get("/api/users/me", response_model=UserRead)
def get_profile(user: User = Depends(current_user)):
    return user


@app.patch("/api/users/me", response_model=UserRead)
def update_profile(data: UserUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if data.name is not None:
        user.name = data.name.strip()
    if data.password is not None:
        user.password_hash = hash_password(data.password)
    db.commit()
    db.refresh(user)
    return user


@app.get("/api/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.admin))):
    return list(db.scalars(select(User).order_by(User.created_at)))


@app.patch("/api/users/{user_id}/role", response_model=UserRead)
def set_role(user_id: int, role: UserRole, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.admin))):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.role = role.value
    db.commit()
    db.refresh(target)
    return target


@app.post("/api/campaigns", response_model=CampaignRead, status_code=201)
def create(data: CampaignCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.contributor, UserRole.admin))):
    return create_campaign(db, data, user)


@app.get("/api/campaigns", response_model=list[CampaignRead])
def campaigns(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return list_campaigns(db, user)


@app.get("/api/dashboard/summary", response_model=DashboardSummary)
def dashboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return dashboard_summary(db, user)


@app.get("/api/schedule", response_model=list[CampaignRead])
def schedule_view(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return [campaign for campaign in list_campaigns(db, user) if campaign.scheduled_for is not None]


@app.post("/api/campaigns/{campaign_id}/submit", response_model=CampaignRead)
def submit(campaign_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.contributor, UserRole.admin))):
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return submit_campaign(db, campaign, user)


@app.post("/api/campaigns/{campaign_id}/approve", response_model=CampaignRead)
def approve(campaign_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.approver, UserRole.admin))):
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return decide_campaign(db, campaign, True)


@app.post("/api/campaigns/{campaign_id}/reject", response_model=CampaignRead)
def reject(campaign_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.approver, UserRole.admin))):
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return decide_campaign(db, campaign, False)


@app.post("/api/campaigns/{campaign_id}/schedule", response_model=CampaignRead)
def schedule(campaign_id: int, data: ScheduleRequest, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.publisher, UserRole.admin))):
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return schedule_campaign(db, campaign, data)


@app.post("/api/service-accounts", response_model=ServiceAccountRead, status_code=201)
def connect(data: ServiceAccountCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return connect_service_account(db, user, data.provider, data.external_username)


@app.get("/api/service-accounts", response_model=list[ServiceAccountRead])
def services(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return list(db.scalars(select(ServiceAccount).where(ServiceAccount.user_id == user.id)))


@app.get("/api/explore/alerts", response_model=list[KeywordAlertRead])
def alerts(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return list_alerts(db, user)


@app.post("/api/explore/alerts", response_model=KeywordAlertRead, status_code=201)
def add_alert(data: KeywordAlertCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return create_alert(db, user, data.keyword, data.provider)


@app.patch("/api/explore/alerts/{alert_id}", response_model=KeywordAlertRead)
def toggle_alert(alert_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    alert = db.scalar(select(KeywordAlert).where(KeywordAlert.id == alert_id, KeywordAlert.user_id == user.id))
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_active = not alert.is_active
    db.commit()
    db.refresh(alert)
    return alert
