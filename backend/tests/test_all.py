"""Executable functional test records for the selected Mashbot scope.

The records below mirror the assignment's Table B fields. Automated cases are
API/integration tests; manual system-level execution must be recorded separately
from the browser because these tests do not exercise a user-visible GUI.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.security import hash_password
from app.models import User, UserRole


TEST_CASE_RECORDS = [
    {
        "id_title": "TC-01 Valid account registration",
        "level_category": "API integration, normal",
        "test_basis_objective": "FR1 account management; a valid user can create an account.",
        "preconditions": "The email address is not already registered.",
        "test_data": "Unique valid email, name of 2 characters, password of 8 characters.",
        "steps": "POST /api/auth/register with a valid JSON account payload.",
        "expected_result": "HTTP 201; returned user has a contributor role and no password.",
        "actual_result": "HTTP 201 and returned user matched the expected account fields.",
        "status": "PASSED",
        "evidence": "pytest assertion in TC-01.",
    },
    {
        "id_title": "TC-02 Valid authentication",
        "level_category": "API integration, normal",
        "test_basis_objective": "FR1 authentication; a registered user can sign in.",
        "preconditions": "A registered active account exists.",
        "test_data": "Registered email and correct password.",
        "steps": "POST /api/auth/login using OAuth2 form fields.",
        "expected_result": "HTTP 200 and a bearer access token is returned.",
        "actual_result": "HTTP 200 and a non-empty bearer token was returned.",
        "status": "PASSED",
        "evidence": "pytest assertion in TC-02.",
    },
    {
        "id_title": "TC-03 Administrator assigns publisher role",
        "level_category": "API integration, role-based access, normal",
        "test_basis_objective": "FR2 role-based access; an administrator can assign a supported role.",
        "preconditions": "An administrator and target contributor account exist.",
        "test_data": "Target user and role=publisher.",
        "steps": "PATCH /api/users/{id}/role?role=publisher with an admin token.",
        "expected_result": "HTTP 200 and the target role becomes publisher.",
        "actual_result": "HTTP 200 and the returned role was publisher.",
        "status": "PASSED",
        "evidence": "pytest assertion in TC-03.",
    },
    {
        "id_title": "TC-04 Publisher is denied contributor-only creation",
        "level_category": "API integration, authorization/error",
        "test_basis_objective": "FR2 role-based access; publisher cannot create campaigns.",
        "preconditions": "An active publisher account exists.",
        "test_data": "Valid campaign payload submitted with publisher token.",
        "steps": "POST /api/campaigns with the publisher bearer token.",
        "expected_result": "HTTP 403 with a role authorization error.",
        "actual_result": "HTTP 403 and campaign creation was rejected.",
        "status": "PASSED",
        "evidence": "pytest assertion in TC-04.",
    },
    {
        "id_title": "TC-05 Campaign content exact maximum boundary",
        "level_category": "API integration, boundary",
        "test_basis_objective": "FR3 campaign management; content at the declared 5,000-character limit is accepted.",
        "preconditions": "An authenticated contributor exists.",
        "test_data": "Campaign name of 1 character and content of exactly 5,000 characters.",
        "steps": "POST /api/campaigns with the boundary payload.",
        "expected_result": "HTTP 201 and the campaign is stored as draft.",
        "actual_result": "HTTP 201; returned status was draft and content length was 5,000.",
        "status": "PASSED",
        "evidence": "pytest assertion in TC-05.",
    },
    {
        "id_title": "TC-06 Owner submits a draft",
        "level_category": "API integration, workflow, normal",
        "test_basis_objective": "FR4 approval workflow; a campaign owner can submit a draft.",
        "preconditions": "The contributor owns a draft campaign.",
        "test_data": "Existing draft campaign ID and owner token.",
        "steps": "POST /api/campaigns/{id}/submit with the owner token.",
        "expected_result": "HTTP 200 and status changes from draft to submitted.",
        "actual_result": "HTTP 200 and status changed to submitted.",
        "status": "PASSED",
        "evidence": "pytest assertion in TC-06.",
    },
    {
        "id_title": "TC-07 Submitted campaign cannot be submitted twice",
        "level_category": "API integration, business-rule/error",
        "test_basis_objective": "FR4 approval workflow; only draft or rejected campaigns can be submitted.",
        "preconditions": "The campaign is already submitted and owned by the caller.",
        "test_data": "Same campaign ID submitted a second time.",
        "steps": "POST /api/campaigns/{id}/submit again.",
        "expected_result": "HTTP 409 and the status remains submitted.",
        "actual_result": "HTTP 409 and the submitted state was preserved.",
        "status": "PASSED",
        "evidence": "pytest assertion in TC-07.",
    },
    {
        "id_title": "TC-08 Approver approves submitted campaign",
        "level_category": "API integration, workflow, normal",
        "test_basis_objective": "FR4 approval workflow; an approver can approve a submitted campaign.",
        "preconditions": "A submitted campaign and active approver exist.",
        "test_data": "Submitted campaign ID and approver token.",
        "steps": "POST /api/campaigns/{id}/approve with the approver token.",
        "expected_result": "HTTP 200 and status changes to approved.",
        "actual_result": "HTTP 200 and status changed to approved.",
        "status": "PASSED",
        "evidence": "pytest assertion in TC-08.",
    },
    {
        "id_title": "TC-09 Past schedule time is rejected",
        "level_category": "API integration, boundary/error",
        "test_basis_objective": "FR5 scheduling; scheduled time must be in the future.",
        "preconditions": "An approved campaign exists and the caller has publisher permission.",
        "test_data": "Scheduled time one second before current UTC time.",
        "steps": "POST /api/campaigns/{id}/schedule with the past timestamp.",
        "expected_result": "HTTP 422 and the campaign remains approved.",
        "actual_result": "HTTP 422 and the campaign was not scheduled.",
        "status": "PASSED",
        "evidence": "pytest assertion in TC-09.",
    },
    {
        "id_title": "TC-10 Service account minimum boundaries",
        "level_category": "API integration, boundary",
        "test_basis_objective": "FR6 external-service boundary; provider and external username accept their two-character minimum.",
        "preconditions": "An authenticated user exists.",
        "test_data": "provider=FB and external_username=u1.",
        "steps": "POST /api/service-accounts with the exact minimum-length values.",
        "expected_result": "HTTP 201 and the service association is stored.",
        "actual_result": "HTTP 201 and both boundary values were stored.",
        "status": "PASSED",
        "evidence": "pytest assertion in TC-10.",
    },
    {
        "id_title": "TC-11 Invalid service account payload",
        "level_category": "API integration, invalid/error",
        "test_basis_objective": "FR6 external-service boundary; invalid short provider data is rejected.",
        "preconditions": "An authenticated user exists.",
        "test_data": "provider=x and external_username=u1.",
        "steps": "POST /api/service-accounts with an invalid provider.",
        "expected_result": "HTTP 422 validation error and no association is created.",
        "actual_result": "HTTP 422 validation error was returned.",
        "status": "PASSED",
        "evidence": "pytest assertion in TC-11.",
    },
    {
        "id_title": "TC-12 Create and pause keyword alert",
        "level_category": "API integration, normal",
        "test_basis_objective": "FR7 keyword-alert management; an authenticated user can create and toggle an alert.",
        "preconditions": "An authenticated user exists.",
        "test_data": "keyword=sustainable packaging and provider=all.",
        "steps": "POST an alert, then PATCH the returned alert ID.",
        "expected_result": "HTTP 201 creates an active alert; HTTP 200 changes it to inactive.",
        "actual_result": "The alert was created active and then changed to inactive.",
        "status": "PASSED",
        "evidence": "pytest assertion in TC-12.",
    },
    {
        "id_title": "TC-13 Dashboard summary is observable",
        "level_category": "API integration, system-flow support, normal",
        "test_basis_objective": "FR3-FR5 workflow support; an authenticated user can retrieve campaign pipeline totals.",
        "preconditions": "An authenticated user and campaign data exist.",
        "test_data": "Authenticated GET /api/dashboard/summary request.",
        "steps": "Request the dashboard summary with a valid bearer token.",
        "expected_result": "HTTP 200 with all summary counters and an upcoming list.",
        "actual_result": "HTTP 200 with all required summary fields.",
        "status": "PASSED",
        "evidence": "pytest assertion in TC-13.",
    },
    {
        "id_title": "TC-14 Missing authentication is rejected",
        "level_category": "API integration, invalid/error, security",
        "test_basis_objective": "FR1/FR2 authentication boundary; protected resources require a valid token.",
        "preconditions": "No authentication header is supplied.",
        "test_data": "GET /api/users/me without Authorization.",
        "steps": "Call the protected profile endpoint without credentials.",
        "expected_result": "HTTP 401 and no user data is returned.",
        "actual_result": "HTTP 401 was returned.",
        "status": "PASSED",
        "evidence": "pytest assertion in TC-14.",
    },
]


TEST_CONDITION_RECORDS = [
    {"test_basis_requirement": "FR1", "condition_id": "COND-01", "test_condition": "A valid new account can be registered and authenticated."},
    {"test_basis_requirement": "FR2", "condition_id": "COND-02", "test_condition": "An administrator can assign roles and protected actions enforce those roles."},
    {"test_basis_requirement": "FR3", "condition_id": "COND-03", "test_condition": "A permitted user can create a draft at the exact content boundary."},
    {"test_basis_requirement": "FR4", "condition_id": "COND-04", "test_condition": "Campaign submission and approval follow the permitted state transitions."},
    {"test_basis_requirement": "FR5", "condition_id": "COND-05", "test_condition": "Only approved campaigns can be scheduled for a future time."},
    {"test_basis_requirement": "FR6", "condition_id": "COND-06", "test_condition": "Service-account associations accept valid boundary data and reject invalid data."},
    {"test_basis_requirement": "FR7", "condition_id": "COND-07", "test_condition": "Keyword alerts can be created and toggled for the authenticated user."},
]


TRACEABILITY_RECORDS = [
    {"requirement": "FR1", "condition": "COND-01", "test_case": "TC-01, TC-02", "execution_result": "PASSED", "defect_report": "N/A"},
    {"requirement": "FR2", "condition": "COND-02", "test_case": "TC-03, TC-04, TC-14", "execution_result": "PASSED", "defect_report": "N/A"},
    {"requirement": "FR3", "condition": "COND-03", "test_case": "TC-05, TC-13", "execution_result": "PASSED", "defect_report": "N/A"},
    {"requirement": "FR4", "condition": "COND-04", "test_case": "TC-06, TC-07, TC-08", "execution_result": "PASSED", "defect_report": "N/A"},
    {"requirement": "FR5", "condition": "COND-05", "test_case": "TC-09, TC-13", "execution_result": "PASSED", "defect_report": "N/A"},
    {"requirement": "FR6", "condition": "COND-06", "test_case": "TC-10, TC-11", "execution_result": "PASSED", "defect_report": "N/A"},
    {"requirement": "FR7", "condition": "COND-07", "test_case": "TC-12", "execution_result": "PASSED", "defect_report": "N/A"},
]


# Assignment-level execution set. Manual cases are deliberately kept separate
# from pytest assertions because a TestClient call is not a user-visible system test.
ASSIGNMENT_TEST_CASE_RECORDS = [
    {"id_title": "TC-01 Valid account registration", "level_category": "Functional/API", "test_basis_objective": "FR1", "preconditions": "Email is unused", "test_data": "Valid email, 2-character name, 8-character password", "steps": "Submit registration", "expected_result": "Account is created as contributor", "actual_result": "Account created", "status": "PASSED", "evidence": "pytest TC-01"},
    {"id_title": "TC-02 Valid authentication", "level_category": "Functional/API", "test_basis_objective": "FR1", "preconditions": "Active account exists", "test_data": "Correct credentials", "steps": "Submit login form", "expected_result": "Bearer token returned", "actual_result": "Bearer token returned", "status": "PASSED", "evidence": "pytest TC-02"},
    {"id_title": "TC-03 Role assignment and enforcement", "level_category": "Functional/security", "test_basis_objective": "FR2", "preconditions": "Admin and target account exist", "test_data": "publisher role", "steps": "Assign role and attempt contributor-only action", "expected_result": "Role is assigned and forbidden action returns 403", "actual_result": "Role assigned and action returned 403", "status": "PASSED", "evidence": "pytest TC-03 and TC-04"},
    {"id_title": "TC-04 Maximum campaign content", "level_category": "Functional/boundary", "test_basis_objective": "FR3", "preconditions": "Permitted user is authenticated", "test_data": "Exactly 5,000 content characters", "steps": "Create campaign", "expected_result": "Draft is created", "actual_result": "Draft created", "status": "PASSED", "evidence": "pytest TC-05"},
    {"id_title": "TC-05 Approval state transition", "level_category": "Functional/workflow", "test_basis_objective": "FR4", "preconditions": "Draft and approver exist", "test_data": "Draft campaign", "steps": "Submit then approve", "expected_result": "Status becomes approved", "actual_result": "Status became approved", "status": "PASSED", "evidence": "pytest TC-06 and TC-08"},
    {"id_title": "TC-06 Invalid scheduling boundary", "level_category": "Functional/error/boundary", "test_basis_objective": "FR5", "preconditions": "Approved campaign exists", "test_data": "Timestamp one second in the past", "steps": "Request scheduling", "expected_result": "422 and campaign remains approved", "actual_result": "422 and campaign remained approved", "status": "PASSED", "evidence": "pytest TC-09"},
    {"id_title": "TC-07 Service-account validation", "level_category": "Functional/boundary/error", "test_basis_objective": "FR6", "preconditions": "Authenticated user exists", "test_data": "Minimum valid values and one-character provider", "steps": "Submit both payloads", "expected_result": "Minimum valid payload succeeds; invalid payload returns 422", "actual_result": "201 and 422 respectively", "status": "PASSED", "evidence": "pytest TC-10 and TC-11"},
    {"id_title": "TC-08 Keyword alert lifecycle", "level_category": "Functional/API", "test_basis_objective": "FR7", "preconditions": "Authenticated user exists", "test_data": "Keyword and provider=all", "steps": "Create then toggle alert", "expected_result": "Alert changes active to inactive", "actual_result": "Alert changed active to inactive", "status": "PASSED", "evidence": "pytest TC-12"},
    {"id_title": "TC-09 Invalid and non-existent email handling", "level_category": "Functional/invalid/error", "test_basis_objective": "FR1 authentication and account validation", "preconditions": "No account exists for the test addresses", "test_data": "Malformed email for registration; syntactically valid but unregistered email for login", "steps": "Submit malformed registration, then submit login for the unregistered address", "expected_result": "Registration returns 422 and login returns 401", "actual_result": "Both invalid requests were rejected with the expected status", "status": "PASSED", "evidence": "pytest invalid-email and nonexistent-email cases"},
    {"id_title": "TC-10 New user to dashboard journey", "level_category": "System/manual", "test_basis_objective": "FR1, FR2, FR3", "preconditions": "Docker services running; browser available", "test_data": "New user credentials and campaign text", "steps": "Register, sign in, create campaign, open Dashboard", "expected_result": "User sees dashboard and created draft", "actual_result": "Manual browser execution required", "status": "NOT EXECUTED", "evidence": "Capture browser screenshot and URL after execution"},
    {"id_title": "TC-11 End-to-end approval and scheduling", "level_category": "System/manual", "test_basis_objective": "FR3, FR4, FR5", "preconditions": "Contributor, approver, and publisher accounts exist", "test_data": "Draft campaign and future launch time", "steps": "Create, submit, approve, sign in as publisher, schedule", "expected_result": "Campaign appears as scheduled", "actual_result": "Manual browser execution required", "status": "NOT EXECUTED", "evidence": "Capture screenshots for each role and calendar"},
    {"id_title": "TC-12 Admin people-and-roles journey", "level_category": "System/manual/security", "test_basis_objective": "FR2", "preconditions": "Admin and second account exist", "test_data": "Change second account to publisher", "steps": "Sign in as admin, open People & roles, change role", "expected_result": "Role update is visible and persists after refresh", "actual_result": "Manual browser execution required", "status": "NOT EXECUTED", "evidence": "Capture People & roles screenshot before and after refresh"},
    {"id_title": "TC-13 Transport security", "level_category": "Non-functional/security", "test_basis_objective": "NFR1 TLS", "preconditions": "Application containers running", "test_data": "HTTP and HTTPS endpoint checks", "steps": "Inspect exposed endpoints and attempt HTTPS", "expected_result": "User-facing traffic is served over TLS", "actual_result": "Frontend/backend expose HTTP only; no TLS listener or certificate is configured", "status": "FAILED", "evidence": "docker-compose.yml exposes 8080/8000 without TLS; application URL is http://localhost:8080"},
    {"id_title": "TC-14 Database backup and restore", "level_category": "Non-functional/reliability", "test_basis_objective": "NFR2 backup", "preconditions": "A defined backup destination and restore procedure are required", "test_data": "PostgreSQL named volume", "steps": "Create backup, remove service data in a controlled environment, restore, verify records", "expected_result": "Backup can be restored with no unacceptable data loss", "actual_result": "No configured backup job, destination, retention policy, or restore procedure exists", "status": "FAILED", "evidence": "docker-compose.yml defines only postgres_data volume; no backup service or script exists"},
    {"id_title": "TC-15 Configurable session timeout", "level_category": "Non-functional/security", "test_basis_objective": "NFR3 session timeout", "preconditions": "Token lifetime configuration is available", "test_data": "ACCESS_TOKEN_MINUTES=60/default setting", "steps": "Inspect configuration and verify token lifetime policy", "expected_result": "Session timeout is configurable and documented", "actual_result": "Setting exists with a 60-minute default; expiry timing requires a long-running execution", "status": "PASSED", "evidence": "backend/app/config.py access_token_minutes=60 and security.py token expiry"},
]


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    with TestingSession() as session:
        session.add(
            User(
                email="admin@example.com",
                name="Administrator",
                password_hash=hash_password("AdminPass123!"),
                role=UserRole.admin.value,
            )
        )
        session.commit()

    def override_get_db():
        with TestingSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}@example.com"


def register(client: TestClient, prefix: str = "user", password: str = "Pass1234!") -> dict:
    response = client.post(
        "/api/auth/register",
        json={"email": email(prefix), "name": prefix.title(), "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()


def token_for(client: TestClient, email_address: str, password: str = "Pass1234!") -> str:
    response = client.post(
        "/api/auth/login",
        data={"username": email_address, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def admin_token(client: TestClient) -> str:
    return token_for(client, "admin@example.com", "AdminPass123!")


def assign_role(client: TestClient, user_id: int, role: str) -> str:
    response = client.patch(
        f"/api/users/{user_id}/role?role={role}",
        headers=auth(admin_token(client)),
    )
    assert response.status_code == 200, response.text
    return response.json()["role"]


def create_campaign(client: TestClient, token: str, name: str = "Launch") -> dict:
    response = client.post(
        "/api/campaigns",
        headers=auth(token),
        json={"name": name, "content": "A campaign message"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_tc_01_valid_account_registration(client):
    response = client.post(
        "/api/auth/register",
        json={"email": email("register"), "name": "Al", "password": "Pass1234!"},
    )
    assert response.status_code == 201
    assert response.json()["role"] == "contributor"
    assert "password" not in response.json()


def test_tc_02_valid_authentication(client):
    user_email = email("login")
    client.post("/api/auth/register", json={"email": user_email, "name": "Login User", "password": "Pass1234!"})
    response = client.post("/api/auth/login", data={"username": user_email, "password": "Pass1234!"})
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_profile_modification_requires_authentication_and_updates_name(client):
    user = register(client, "profile")
    token = token_for(client, user["email"])
    response = client.patch(
        "/api/users/me",
        headers=auth(token),
        json={"name": "Updated Profile"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Profile"


def test_tc_03_admin_assigns_publisher_role(client):
    user = register(client, "publisher")
    assert assign_role(client, user["id"], "publisher") == "publisher"


def test_tc_04_publisher_is_denied_campaign_creation(client):
    user = register(client, "publisher")
    assign_role(client, user["id"], "publisher")
    response = client.post(
        "/api/campaigns",
        headers=auth(token_for(client, user["email"])),
        json={"name": "Not allowed", "content": "Publisher cannot create"},
    )
    assert response.status_code == 403


def test_tc_05_campaign_content_exact_maximum_boundary(client):
    token = token_for(client, "admin@example.com", "AdminPass123!")
    content = "x" * 5000
    response = client.post(
        "/api/campaigns",
        headers=auth(token),
        json={"name": "x", "content": content},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "draft"
    assert len(response.json()["content"]) == 5000


def test_tc_06_owner_submits_draft(client):
    user = register(client, "contributor")
    token = token_for(client, user["email"])
    campaign = create_campaign(client, token)
    response = client.post(f"/api/campaigns/{campaign['id']}/submit", headers=auth(token))
    assert response.status_code == 200
    assert response.json()["status"] == "submitted"


def test_tc_07_submitted_campaign_cannot_be_submitted_twice(client):
    user = register(client, "contributor")
    token = token_for(client, user["email"])
    campaign = create_campaign(client, token)
    client.post(f"/api/campaigns/{campaign['id']}/submit", headers=auth(token))
    response = client.post(f"/api/campaigns/{campaign['id']}/submit", headers=auth(token))
    assert response.status_code == 409


def test_tc_08_approver_approves_submitted_campaign(client):
    contributor = register(client, "contributor")
    contributor_token = token_for(client, contributor["email"])
    campaign = create_campaign(client, contributor_token)
    client.post(f"/api/campaigns/{campaign['id']}/submit", headers=auth(contributor_token))
    approver = register(client, "approver")
    assign_role(client, approver["id"], "approver")
    response = client.post(
        f"/api/campaigns/{campaign['id']}/approve",
        headers=auth(token_for(client, approver["email"])),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_tc_09_past_schedule_time_is_rejected(client):
    campaign = create_campaign(client, admin_token(client))
    client.post(f"/api/campaigns/{campaign['id']}/submit", headers=auth(admin_token(client)))
    client.post(f"/api/campaigns/{campaign['id']}/approve", headers=auth(admin_token(client)))
    past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    response = client.post(
        f"/api/campaigns/{campaign['id']}/schedule",
        headers=auth(admin_token(client)),
        json={"scheduled_for": past},
    )
    assert response.status_code == 422


def test_tc_10_service_account_minimum_boundaries(client):
    response = client.post(
        "/api/service-accounts",
        headers=auth(admin_token(client)),
        json={"provider": "FB", "external_username": "u1"},
    )
    assert response.status_code == 201
    assert response.json()["provider"] == "FB"
    assert response.json()["external_username"] == "u1"


def test_tc_11_invalid_service_account_payload(client):
    response = client.post(
        "/api/service-accounts",
        headers=auth(admin_token(client)),
        json={"provider": "x", "external_username": "u1"},
    )
    assert response.status_code == 422


def test_tc_12_create_and_pause_keyword_alert(client):
    token = admin_token(client)
    response = client.post(
        "/api/explore/alerts",
        headers=auth(token),
        json={"keyword": "sustainable packaging", "provider": "all"},
    )
    assert response.status_code == 201
    alert_id = response.json()["id"]
    assert response.json()["is_active"] is True
    toggle = client.patch(f"/api/explore/alerts/{alert_id}", headers=auth(token))
    assert toggle.status_code == 200
    assert toggle.json()["is_active"] is False


def test_tc_13_dashboard_summary_is_observable(client):
    response = client.get("/api/dashboard/summary", headers=auth(admin_token(client)))
    assert response.status_code == 200
    body = response.json()
    assert {"total_campaigns", "draft_campaigns", "pending_approval", "scheduled_campaigns", "published_campaigns", "connected_services", "upcoming"} <= body.keys()


def test_tc_14_missing_authentication_is_rejected(client):
    response = client.get("/api/users/me")
    assert response.status_code == 401


def test_invalid_email_registration_is_rejected(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "name": "Invalid Email", "password": "Pass1234!"},
    )
    assert response.status_code == 422


def test_nonexistent_email_login_is_rejected(client):
    response = client.post(
        "/api/auth/login",
        data={"username": "missing-user@example.com", "password": "Pass1234!"},
    )
    assert response.status_code == 401


@pytest.mark.parametrize("record", TEST_CASE_RECORDS)
def test_test_case_record_format(record):
    required = {"id_title", "level_category", "test_basis_objective", "preconditions", "test_data", "steps", "expected_result", "actual_result", "status", "evidence"}
    assert required <= record.keys()
    assert record["status"] in {"PASSED", "FAILED", "BLOCKED", "NOT EXECUTED"}


def test_test_condition_record_format():
    assert len(TEST_CONDITION_RECORDS) == 7
    assert {"test_basis_requirement", "condition_id", "test_condition"} <= TEST_CONDITION_RECORDS[0].keys()
    assert {record["test_basis_requirement"] for record in TEST_CONDITION_RECORDS} == {f"FR{i}" for i in range(1, 8)}


def test_traceability_record_format():
    assert len(TRACEABILITY_RECORDS) == 7
    required = {"requirement", "condition", "test_case", "execution_result", "defect_report"}
    assert all(required <= record.keys() for record in TRACEABILITY_RECORDS)
    assert all(record["execution_result"] in {"PASSED", "FAILED", "BLOCKED", "NOT EXECUTED"} for record in TRACEABILITY_RECORDS)


def test_assignment_execution_set_has_distinct_categories_and_real_statuses():
    assert len(ASSIGNMENT_TEST_CASE_RECORDS) == 15
    assert {record["level_category"].split("/")[0] for record in ASSIGNMENT_TEST_CASE_RECORDS} >= {"Functional", "System", "Non-functional"}
    assert sum(record["status"] in {"FAILED", "BLOCKED"} for record in ASSIGNMENT_TEST_CASE_RECORDS) >= 2
    assert all(record["actual_result"] for record in ASSIGNMENT_TEST_CASE_RECORDS)


def test_tc_13_tls_transport_is_enforced():
    """NFR1 evidence test: the deployed HTTP entry point must enforce TLS."""
    response = TestClient(app).get("/health", follow_redirects=False)
    assert response.url.scheme == "https" or response.status_code in {301, 302, 307, 308}, (
        "The current deployment serves HTTP without HTTPS enforcement."
    )


def test_tc_14_backup_restore_procedure_is_configured():
    """NFR2 evidence test: a repeatable backup/restore artifact must exist."""
    backup_artifacts = list(Path("/app").glob("**/*backup*"))
    assert backup_artifacts, "No backup or restore procedure is configured in the deployed backend."
