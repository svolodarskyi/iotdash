"""Seed script: creates initial data for development.

Run with: python -m app.seed
"""

import bcrypt
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Alert, Device, GrafanaDashboard, Organisation, User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def seed(db: Session) -> None:
    # Check if already seeded
    if db.query(Organisation).first():
        print("Database already seeded, skipping.")
        return

    # ── Organisation 1: Demo Corp ─────────────────────
    org = Organisation(name="Demo Corp", grafana_org_id=1)
    db.add(org)
    db.flush()

    admin = User(
        email="admin@democorp.com",
        password_hash=hash_password("admin123"),
        full_name="Admin User",
        organisation_id=org.id,
        role="admin",
    )
    db.add(admin)

    sensor01 = Device(
        device_code="sensor01",
        name="Temperature Sensor 01",
        organisation_id=org.id,
        device_type="temperature",
        metadata_={"location": "Room A", "unit": "celsius"},
    )
    sensor02 = Device(
        device_code="sensor02",
        name="Temperature Sensor 02",
        organisation_id=org.id,
        device_type="temperature",
        metadata_={"location": "Room B", "unit": "celsius"},
    )
    db.add_all([sensor01, sensor02])

    dashboard = GrafanaDashboard(
        organisation_id=org.id,
        title="Temperature Overview",
        grafana_uid="iot-temperature",
        grafana_org_id=1,
        panel_ids=[1, 2, 3],
        embed_base_url="http://grafana:3000",
    )
    db.add(dashboard)
    db.flush()

    alert1 = Alert(
        device_id=sensor01.id,
        created_by=admin.id,
        metric="temperature",
        condition="above",
        threshold=30.0,
        duration_seconds=60,
        notification_email="admin@democorp.com",
    )
    db.add(alert1)

    # ── Organisation 2: Acme IoT ──────────────────────
    org2 = Organisation(name="Acme IoT", grafana_org_id=2)
    db.add(org2)
    db.flush()

    viewer = User(
        email="viewer@acmeiot.com",
        password_hash=hash_password("viewer123"),
        full_name="Acme Viewer",
        organisation_id=org2.id,
        role="viewer",
    )
    db.add(viewer)

    sensor03 = Device(
        device_code="sensor03",
        name="Temperature Sensor 03",
        organisation_id=org2.id,
        device_type="temperature",
        metadata_={"location": "Room C", "unit": "celsius"},
    )
    db.add(sensor03)

    dashboard2 = GrafanaDashboard(
        organisation_id=org2.id,
        title="Temperature Overview",
        grafana_uid="iot-temperature",
        grafana_org_id=2,
        panel_ids=[1, 2, 3],
        embed_base_url="http://grafana:3000",
    )
    db.add(dashboard2)
    db.flush()

    alert2 = Alert(
        device_id=sensor03.id,
        created_by=viewer.id,
        metric="temperature",
        condition="above",
        threshold=35.0,
        duration_seconds=120,
        notification_email="viewer@acmeiot.com",
    )
    db.add(alert2)

    db.commit()
    print("Seed data created successfully.")
    print(f"  Organisation 1: {org.name} (id={org.id})")
    print(f"    Admin user:   {admin.email} / admin123")
    print(f"    Devices:      {sensor01.device_code}, {sensor02.device_code}")
    print(f"  Organisation 2: {org2.name} (id={org2.id})")
    print(f"    Viewer user:  {viewer.email} / viewer123")
    print(f"    Devices:      {sensor03.device_code}")
    print("  Alerts:")
    print(f"    {sensor01.device_code}: {alert1.metric} {alert1.condition} {alert1.threshold}")
    print(f"    {sensor03.device_code}: {alert2.metric} {alert2.condition} {alert2.threshold}")


def main() -> None:
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
