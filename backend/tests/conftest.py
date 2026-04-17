import uuid

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from unittest.mock import MagicMock

from app.database import get_db
from app.main import app
from app.models import Alert, Base, Device, GrafanaDashboard, Organisation, User
from app.services.grafana_client import get_grafana_client

# In-memory SQLite for tests — no external dependencies needed
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def mock_grafana():
    """A MagicMock GrafanaClient used for all tests."""
    mock = MagicMock()
    mock.ensure_alerts_folder.return_value = "test-folder-uid"
    mock.create_alert_rule.return_value = "test-rule-uid"
    return mock


@pytest.fixture()
def client(db, mock_grafana):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_grafana_client] = lambda: mock_grafana
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def seed_data(db):
    """Insert test data and return references."""
    org = Organisation(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="Test Org",
        grafana_org_id=1,
    )
    db.add(org)
    db.flush()

    device1 = Device(
        id=uuid.UUID("00000000-0000-0000-0000-000000000010"),
        device_code="test_sensor01",
        name="Test Sensor 01",
        organisation_id=org.id,
        device_type="temperature",
        metadata_={"location": "Lab A"},
    )
    device2 = Device(
        id=uuid.UUID("00000000-0000-0000-0000-000000000020"),
        device_code="test_sensor02",
        name="Test Sensor 02",
        organisation_id=org.id,
        device_type="temperature",
    )
    db.add_all([device1, device2])

    dashboard = GrafanaDashboard(
        id=uuid.UUID("00000000-0000-0000-0000-000000000100"),
        organisation_id=org.id,
        title="Test Dashboard",
        grafana_uid="test-dash",
        grafana_org_id=1,
        panel_ids=[1, 2],
        embed_base_url="http://grafana:3000",
    )
    db.add(dashboard)
    db.commit()

    return {"org": org, "devices": [device1, device2], "dashboard": dashboard}


@pytest.fixture()
def seed_user(db, seed_data):
    """Create a test user in the existing test org."""
    user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        email="testuser@testorg.com",
        password_hash=_hash("testpass123"),
        full_name="Test User",
        organisation_id=seed_data["org"].id,
        role="viewer",
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture()
def auth_client(client, seed_user):
    """A TestClient that is already logged in as seed_user."""
    response = client.post(
        "/api/auth/login",
        json={"email": "testuser@testorg.com", "password": "testpass123"},
    )
    assert response.status_code == 200
    return client


@pytest.fixture()
def two_org_seed(db):
    """Seed two orgs with users and devices for isolation testing."""
    org_a = Organisation(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000a1"),
        name="Org A",
        grafana_org_id=1,
    )
    org_b = Organisation(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000b1"),
        name="Org B",
        grafana_org_id=2,
    )
    db.add_all([org_a, org_b])
    db.flush()

    user_a = User(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000a2"),
        email="user_a@orga.com",
        password_hash=_hash("passa123"),
        full_name="User A",
        organisation_id=org_a.id,
        role="viewer",
    )
    user_b = User(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000b2"),
        email="user_b@orgb.com",
        password_hash=_hash("passb123"),
        full_name="User B",
        organisation_id=org_b.id,
        role="viewer",
    )
    db.add_all([user_a, user_b])

    device_a = Device(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000a3"),
        device_code="org_a_sensor",
        name="Org A Sensor",
        organisation_id=org_a.id,
        device_type="temperature",
    )
    device_b = Device(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000b3"),
        device_code="org_b_sensor",
        name="Org B Sensor",
        organisation_id=org_b.id,
        device_type="temperature",
    )
    db.add_all([device_a, device_b])

    dashboard_a = GrafanaDashboard(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000a4"),
        organisation_id=org_a.id,
        title="Org A Dashboard",
        grafana_uid="org-a-dash",
        grafana_org_id=1,
        panel_ids=[1],
        embed_base_url="http://grafana:3000",
    )
    db.add(dashboard_a)
    db.commit()

    alert_a = Alert(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000a5"),
        device_id=device_a.id,
        created_by=user_a.id,
        metric="temperature",
        condition="above",
        threshold=30.0,
        duration_seconds=60,
        notification_email="user_a@orga.com",
    )
    alert_b = Alert(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000b5"),
        device_id=device_b.id,
        created_by=user_b.id,
        metric="temperature",
        condition="above",
        threshold=35.0,
        duration_seconds=120,
        notification_email="user_b@orgb.com",
    )
    db.add_all([alert_a, alert_b])
    db.commit()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "user_a": user_a,
        "user_b": user_b,
        "device_a": device_a,
        "device_b": device_b,
        "alert_a": alert_a,
        "alert_b": alert_b,
    }
