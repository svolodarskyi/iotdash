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
from app.models import (
    Alert,
    Base,
    DeviceProvisioned,
    DeviceProvisionedMetric,
    DeviceType,
    DeviceTypeMetric,
    GrafanaDashboard,
    Metric,
    Organisation,
    User,
)
from app.services.grafana_client import get_grafana_client
from app.services.mqtt_publisher import MqttPublisher, get_mqtt_publisher

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


# ── Well-known IDs ────────────────────────────────────
METRIC_TEMP_ID = uuid.UUID("00000000-0000-0000-0000-0000000e0001")
METRIC_HUMIDITY_ID = uuid.UUID("00000000-0000-0000-0000-0000000e0002")
METRIC_RPM_ID = uuid.UUID("00000000-0000-0000-0000-0000000e0003")

DEVICE_TYPE_TEMP_SENSOR_ID = uuid.UUID("00000000-0000-0000-0000-0000000d0001")
DEVICE_TYPE_ENGINE_MONITOR_ID = uuid.UUID("00000000-0000-0000-0000-0000000d0002")


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
def mock_mqtt():
    """A MagicMock MqttPublisher used for all tests."""
    mock = MagicMock(spec=MqttPublisher)
    mock.sync_device_metrics.return_value = True
    return mock


@pytest.fixture()
def client(db, mock_grafana, mock_mqtt):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_grafana_client] = lambda: mock_grafana
    app.dependency_overrides[get_mqtt_publisher] = lambda: mock_mqtt
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def seed_metrics(db):
    """Seed the 3 default metrics."""
    m1 = Metric(id=METRIC_TEMP_ID, name="temperature", unit="\u00b0C", data_type="float", description="Temperature reading")
    m2 = Metric(id=METRIC_HUMIDITY_ID, name="humidity", unit="%", data_type="float", description="Relative humidity")
    m3 = Metric(id=METRIC_RPM_ID, name="engine_rpm", unit="rpm", data_type="float", description="Engine RPM")
    db.add_all([m1, m2, m3])
    db.commit()
    return {"temperature": m1, "humidity": m2, "engine_rpm": m3}


@pytest.fixture()
def seed_device_types(db, seed_metrics):
    """Seed device types with allowed metrics."""
    dt_temp = DeviceType(
        id=DEVICE_TYPE_TEMP_SENSOR_ID,
        name="temperature_sensor",
        description="Temperature and humidity sensor",
    )
    dt_engine = DeviceType(
        id=DEVICE_TYPE_ENGINE_MONITOR_ID,
        name="engine_monitor",
        description="Engine monitoring unit",
    )
    db.add_all([dt_temp, dt_engine])
    db.flush()

    # temperature_sensor supports: temperature, humidity
    db.add(DeviceTypeMetric(device_type_id=dt_temp.id, metric_id=seed_metrics["temperature"].id))
    db.add(DeviceTypeMetric(device_type_id=dt_temp.id, metric_id=seed_metrics["humidity"].id))
    # engine_monitor supports: engine_rpm, temperature
    db.add(DeviceTypeMetric(device_type_id=dt_engine.id, metric_id=seed_metrics["engine_rpm"].id))
    db.add(DeviceTypeMetric(device_type_id=dt_engine.id, metric_id=seed_metrics["temperature"].id))
    db.commit()

    return {"temperature_sensor": dt_temp, "engine_monitor": dt_engine}


@pytest.fixture()
def seed_data(db, seed_metrics, seed_device_types):
    """Insert test data and return references."""
    org = Organisation(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="Test Org",
        grafana_org_id=1,
    )
    db.add(org)
    db.flush()

    dt_temp = seed_device_types["temperature_sensor"]

    device1 = DeviceProvisioned(
        id=uuid.UUID("00000000-0000-0000-0000-000000000010"),
        device_code="test_sensor01",
        name="Test Sensor 01",
        organisation_id=org.id,
        device_type_id=dt_temp.id,
        metadata_={"location": "Lab A"},
    )
    device2 = DeviceProvisioned(
        id=uuid.UUID("00000000-0000-0000-0000-000000000020"),
        device_code="test_sensor02",
        name="Test Sensor 02",
        organisation_id=org.id,
        device_type_id=dt_temp.id,
    )
    db.add_all([device1, device2])
    db.flush()

    # Link device1 to temperature metric
    dm = DeviceProvisionedMetric(device_id=device1.id, metric_id=seed_metrics["temperature"].id)
    db.add(dm)

    dashboard = GrafanaDashboard(
        id=uuid.UUID("00000000-0000-0000-0000-000000000100"),
        organisation_id=org.id,
        title="Test Dashboard",
        grafana_uid="iot-metrics",
        grafana_org_id=1,
        panel_ids=[1],
        embed_base_url="http://grafana:3000",
    )
    db.add(dashboard)
    db.commit()

    return {
        "org": org,
        "devices": [device1, device2],
        "dashboard": dashboard,
        "metrics": seed_metrics,
        "device_types": seed_device_types,
    }


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
def seed_admin(db, seed_data):
    """Create an admin user in the existing test org."""
    user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
        email="admin@testorg.com",
        password_hash=_hash("admin123"),
        full_name="Admin User",
        organisation_id=seed_data["org"].id,
        role="admin",
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture()
def auth_client(client, seed_user):
    """A TestClient that is already logged in as seed_user (viewer)."""
    response = client.post(
        "/api/auth/login",
        json={"email": "testuser@testorg.com", "password": "testpass123"},
    )
    assert response.status_code == 200
    return client


@pytest.fixture()
def admin_client(client, seed_admin):
    """A TestClient that is already logged in as seed_admin."""
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@testorg.com", "password": "admin123"},
    )
    assert response.status_code == 200
    return client


@pytest.fixture()
def two_org_seed(db, seed_metrics, seed_device_types):
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

    dt_temp = seed_device_types["temperature_sensor"]

    device_a = DeviceProvisioned(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000a3"),
        device_code="org_a_sensor",
        name="Org A Sensor",
        organisation_id=org_a.id,
        device_type_id=dt_temp.id,
    )
    device_b = DeviceProvisioned(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000b3"),
        device_code="org_b_sensor",
        name="Org B Sensor",
        organisation_id=org_b.id,
        device_type_id=dt_temp.id,
    )
    db.add_all([device_a, device_b])

    # Link devices to temperature metric
    db.add(DeviceProvisionedMetric(device_id=device_a.id, metric_id=seed_metrics["temperature"].id))
    db.add(DeviceProvisionedMetric(device_id=device_b.id, metric_id=seed_metrics["temperature"].id))

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
