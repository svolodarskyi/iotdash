import uuid
from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


# ── Organisation ──────────────────────────────────────
class OrganisationOut(BaseModel):
    id: uuid.UUID
    name: str
    grafana_org_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Device Type ──────────────────────────────────────
class DeviceTypeMetricOut(BaseModel):
    metric_id: uuid.UUID
    metric_name: str
    metric_unit: str | None

    model_config = {"from_attributes": True}


class DeviceTypeOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    allowed_metrics: list[DeviceTypeMetricOut]
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceTypeCreate(BaseModel):
    name: str
    description: str | None = None
    metric_ids: list[uuid.UUID] = []


class DeviceTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    metric_ids: list[uuid.UUID] | None = None


# ── Device ────────────────────────────────────────────
class DeviceOut(BaseModel):
    id: uuid.UUID
    device_code: str
    name: str
    organisation_id: uuid.UUID
    device_type_id: uuid.UUID
    device_type_name: str
    metadata_: dict | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmbedUrl(BaseModel):
    dashboard_title: str
    panel_id: int
    url: str


class DeviceEmbedUrlsOut(BaseModel):
    device_id: uuid.UUID
    device_code: str
    urls: list[EmbedUrl]


# ── Auth ─────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    organisation_id: uuid.UUID
    role: str

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    organisation_id: uuid.UUID
    organisation_name: str
    role: str


# ── Metrics ──────────────────────────────────────────
class MetricOut(BaseModel):
    id: uuid.UUID
    name: str
    unit: str | None
    data_type: str
    description: str | None

    model_config = {"from_attributes": True}


class DeviceMetricOut(BaseModel):
    metric_id: uuid.UUID
    metric_name: str
    metric_unit: str | None
    is_enabled: bool
    enabled_at: datetime
    disabled_at: datetime | None

    model_config = {"from_attributes": True}


# ── Admin — Organisations ────────────────────────────
class OrgCreate(BaseModel):
    name: str


class OrgUpdate(BaseModel):
    name: str | None = None


# ── Admin — Users ────────────────────────────────────
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    organisation_id: uuid.UUID


class UserUpdate(BaseModel):
    email: str | None = None
    full_name: str | None = None
    is_active: bool | None = None


# ── Admin — Devices ──────────────────────────────────
class DeviceCreate(BaseModel):
    device_code: str | None = None
    name: str
    organisation_id: uuid.UUID
    device_type_id: uuid.UUID
    metric_ids: list[uuid.UUID] = []
    auto_enable: bool = False


class DeviceUpdate(BaseModel):
    name: str | None = None
    device_type_id: uuid.UUID | None = None
    is_active: bool | None = None


class DeviceAdminOut(BaseModel):
    id: uuid.UUID
    device_code: str
    name: str
    organisation_id: uuid.UUID
    organisation_name: str
    device_type_id: uuid.UUID
    device_type_name: str
    is_active: bool
    metrics: list[DeviceMetricOut]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeviceMetricUpdate(BaseModel):
    metric_ids: list[uuid.UUID]
    send_config: bool = False


class DeviceSendConfigResponse(BaseModel):
    device_code: str
    metrics_sent: list[str]
    success: bool


# ── Alert ─────────────────────────────────────────────
class AlertCreate(BaseModel):
    device_id: uuid.UUID
    metric: str
    condition: str  # "above" | "below"
    threshold: float
    duration_seconds: int = 60
    notification_email: str


class AlertUpdate(BaseModel):
    metric: str | None = None
    condition: str | None = None
    threshold: float | None = None
    duration_seconds: int | None = None
    notification_email: str | None = None


class AlertToggle(BaseModel):
    is_enabled: bool


class AlertOut(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    device_code: str
    organisation_name: str | None = None
    created_by: uuid.UUID | None = None
    metric: str
    condition: str
    threshold: float
    duration_seconds: int
    notification_email: str | None = None
    is_enabled: bool
    grafana_rule_uid: str | None = None
    created_at: datetime
    updated_at: datetime
