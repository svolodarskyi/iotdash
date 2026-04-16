"""Seed script: creates initial data for development.

Run with: python -m app.seed
"""

import bcrypt
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Device, GrafanaDashboard, Organisation, User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def seed(db: Session) -> None:
    # Check if already seeded
    if db.query(Organisation).first():
        print("Database already seeded, skipping.")
        return

    # Organisation
    org = Organisation(name="Demo Corp", grafana_org_id=1)
    db.add(org)
    db.flush()

    # Admin user
    admin = User(
        email="admin@democorp.com",
        password_hash=hash_password("admin123"),
        full_name="Admin User",
        organisation_id=org.id,
        role="admin",
    )
    db.add(admin)

    # Devices
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

    # Grafana dashboard
    dashboard = GrafanaDashboard(
        organisation_id=org.id,
        title="Temperature Overview",
        grafana_uid="iot-temperature",
        grafana_org_id=1,
        panel_ids=[1, 2, 3],
        embed_base_url="http://grafana:3000",
    )
    db.add(dashboard)

    db.commit()
    print("Seed data created successfully.")
    print(f"  Organisation: {org.name} (id={org.id})")
    print(f"  Admin user:   {admin.email}")
    print(f"  Devices:      {sensor01.device_code}, {sensor02.device_code}")
    print(f"  Dashboard:    {dashboard.title}")


def main() -> None:
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
