import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import JSON

# Cross-dialect types: use JSONB on PostgreSQL, plain JSON on SQLite (tests)
JSONVariant = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass


class Organisation(Base):
    __tablename__ = "organisations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    grafana_org_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    users: Mapped[list["User"]] = relationship(back_populates="organisation")
    devices: Mapped[list["DeviceProvisioned"]] = relationship(back_populates="organisation")
    dashboards: Mapped[list["GrafanaDashboard"]] = relationship(back_populates="organisation")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organisations.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organisation: Mapped["Organisation"] = relationship(back_populates="users")


class DeviceType(Base):
    __tablename__ = "device_types"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    allowed_metrics: Mapped[list["DeviceTypeMetric"]] = relationship(
        back_populates="device_type", cascade="all, delete-orphan"
    )
    devices: Mapped[list["DeviceProvisioned"]] = relationship(back_populates="device_type")


class DeviceTypeMetric(Base):
    __tablename__ = "device_type_metrics"
    __table_args__ = (UniqueConstraint("device_type_id", "metric_id", name="uq_device_type_metric"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    device_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("device_types.id"), nullable=False
    )
    metric_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("metrics.id"), nullable=False)

    device_type: Mapped["DeviceType"] = relationship(back_populates="allowed_metrics")
    metric: Mapped["Metric"] = relationship(back_populates="device_type_metrics")


class DeviceProvisioned(Base):
    __tablename__ = "devices_provisioned"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    device_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organisations.id"), nullable=False
    )
    device_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("device_types.id"), nullable=False
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONVariant, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organisation: Mapped["Organisation"] = relationship(back_populates="devices")
    device_type: Mapped["DeviceType"] = relationship(back_populates="devices")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="device")
    device_metrics: Mapped[list["DeviceProvisionedMetric"]] = relationship(back_populates="device")


class GrafanaDashboard(Base):
    __tablename__ = "grafana_dashboards"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organisations.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    grafana_uid: Mapped[str] = mapped_column(String(255), nullable=False)
    grafana_org_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    panel_ids: Mapped[dict | None] = mapped_column(JSONVariant, nullable=True)
    embed_base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organisation: Mapped["Organisation"] = relationship(back_populates="dashboards")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("devices_provisioned.id"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    metric: Mapped[str] = mapped_column(String(100), nullable=False)
    condition: Mapped[str] = mapped_column(String(20), nullable=False)
    threshold: Mapped[float] = mapped_column(nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    notification_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    grafana_rule_uid: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    device: Mapped["DeviceProvisioned"] = relationship(back_populates="alerts")


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    data_type: Mapped[str] = mapped_column(String(50), nullable=False, default="float")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    device_type_metrics: Mapped[list["DeviceTypeMetric"]] = relationship(back_populates="metric")
    device_provisioned_metrics: Mapped[list["DeviceProvisionedMetric"]] = relationship(
        back_populates="metric"
    )


class DeviceProvisionedMetric(Base):
    __tablename__ = "device_provisioned_metrics"
    __table_args__ = (UniqueConstraint("device_id", "metric_id", name="uq_device_provisioned_metric"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("devices_provisioned.id"), nullable=False
    )
    metric_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("metrics.id"), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    enabled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    device: Mapped["DeviceProvisioned"] = relationship(back_populates="device_metrics")
    metric: Mapped["Metric"] = relationship(back_populates="device_provisioned_metrics")
