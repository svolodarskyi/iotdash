import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models import Base, Device, GrafanaDashboard, Organisation

# In-memory SQLite for tests — no external dependencies needed
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
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
