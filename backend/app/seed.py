"""Seed script: creates initial data for development.

Run with: python -m app.seed
"""

import bcrypt
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Alert,
    DeviceProvisioned,
    DeviceProvisionedMetric,
    DeviceType,
    DeviceTypeMetric,
    GrafanaDashboard,
    Metric,
    Organisation,
    User,
)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def seed(db: Session) -> None:
    # Check if already seeded
    if db.query(Organisation).first():
        print("Database already seeded, skipping.")
        return

    # ── Metrics catalog ──────────────────────────────
    metric_temp = Metric(name="temperature", unit="\u00b0C", data_type="float", description="Temperature reading")
    metric_humidity = Metric(name="humidity", unit="%", data_type="float", description="Relative humidity")
    metric_rpm = Metric(
        name="engine_rpm", unit="rpm", data_type="float", description="Engine revolutions per minute"
    )
    db.add_all([metric_temp, metric_humidity, metric_rpm])
    db.flush()

    # ── Device Types ──────────────────────────────────
    dt_temp_sensor = DeviceType(
        name="temperature_sensor",
        description="Temperature and humidity sensor",
    )
    dt_engine_monitor = DeviceType(
        name="engine_monitor",
        description="Engine monitoring unit",
    )
    db.add_all([dt_temp_sensor, dt_engine_monitor])
    db.flush()

    # Link device types to allowed metrics
    # temperature_sensor supports: temperature, humidity
    db.add(DeviceTypeMetric(device_type_id=dt_temp_sensor.id, metric_id=metric_temp.id))
    db.add(DeviceTypeMetric(device_type_id=dt_temp_sensor.id, metric_id=metric_humidity.id))
    # engine_monitor supports: engine_rpm, temperature
    db.add(DeviceTypeMetric(device_type_id=dt_engine_monitor.id, metric_id=metric_rpm.id))
    db.add(DeviceTypeMetric(device_type_id=dt_engine_monitor.id, metric_id=metric_temp.id))
    db.flush()

    # ── Platform Organisation (admin users only) ──────
    platform_org = Organisation(name="Platform")
    db.add(platform_org)
    db.flush()

    admin = User(
        email="admin@iotdash.com",
        password_hash=hash_password("admin123"),
        full_name="Platform Admin",
        organisation_id=platform_org.id,
        role="admin",
    )
    db.add(admin)
    db.flush()

    # ── Organisation 1: Demo Corp ─────────────────────
    org = Organisation(name="Demo Corp", grafana_org_id=1)
    db.add(org)
    db.flush()

    demo_viewer = User(
        email="viewer@democorp.com",
        password_hash=hash_password("viewer123"),
        full_name="Demo Viewer",
        organisation_id=org.id,
        role="viewer",
    )
    db.add(demo_viewer)

    sensor01 = DeviceProvisioned(
        device_code="sensor01",
        name="Temperature Sensor 01",
        organisation_id=org.id,
        device_type_id=dt_temp_sensor.id,
        metadata_={"location": "Room A", "unit": "celsius"},
    )
    sensor02 = DeviceProvisioned(
        device_code="sensor02",
        name="Temperature Sensor 02",
        organisation_id=org.id,
        device_type_id=dt_temp_sensor.id,
        metadata_={"location": "Room B", "unit": "celsius"},
    )
    db.add_all([sensor01, sensor02])
    db.flush()

    # Link devices to temperature metric
    db.add(DeviceProvisionedMetric(device_id=sensor01.id, metric_id=metric_temp.id))
    db.add(DeviceProvisionedMetric(device_id=sensor02.id, metric_id=metric_temp.id))

    dashboard = GrafanaDashboard(
        organisation_id=org.id,
        title="IoT Metrics",
        grafana_uid="iot-metrics",
        grafana_org_id=1,
        panel_ids=[1],
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
        notification_email="admin@iotdash.com",
    )
    db.add(alert1)

    # ── Organisation 2: Acme IoT ──────────────────────
    org2 = Organisation(name="Acme IoT", grafana_org_id=2)
    db.add(org2)
    db.flush()

    acme_viewer = User(
        email="viewer@acmeiot.com",
        password_hash=hash_password("viewer123"),
        full_name="Acme Viewer",
        organisation_id=org2.id,
        role="viewer",
    )
    db.add(acme_viewer)

    sensor03 = DeviceProvisioned(
        device_code="sensor03",
        name="Temperature Sensor 03",
        organisation_id=org2.id,
        device_type_id=dt_temp_sensor.id,
        metadata_={"location": "Room C", "unit": "celsius"},
    )
    db.add(sensor03)
    db.flush()

    # Link sensor03 to temperature metric
    db.add(DeviceProvisionedMetric(device_id=sensor03.id, metric_id=metric_temp.id))

    dashboard2 = GrafanaDashboard(
        organisation_id=org2.id,
        title="IoT Metrics",
        grafana_uid="iot-metrics",
        grafana_org_id=2,
        panel_ids=[1],
        embed_base_url="http://grafana:3000",
    )
    db.add(dashboard2)
    db.flush()

    alert2 = Alert(
        device_id=sensor03.id,
        created_by=acme_viewer.id,
        metric="temperature",
        condition="above",
        threshold=35.0,
        duration_seconds=120,
        notification_email="viewer@acmeiot.com",
    )
    db.add(alert2)

    db.commit()
    print("Seed data created successfully.")
    print(f"  Platform Org:   {platform_org.name} (id={platform_org.id})")
    print(f"    Admin user:   {admin.email} / admin123")
    print(f"  Organisation 1: {org.name} (id={org.id})")
    print(f"    Viewer user:  {demo_viewer.email} / viewer123")
    print(f"    Devices:      {sensor01.device_code}, {sensor02.device_code}")
    print(f"  Organisation 2: {org2.name} (id={org2.id})")
    print(f"    Viewer user:  {acme_viewer.email} / viewer123")
    print(f"    Devices:      {sensor03.device_code}")
    print(f"  Device Types:   {dt_temp_sensor.name}, {dt_engine_monitor.name}")
    print("  Metrics:        temperature, humidity, engine_rpm")
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
