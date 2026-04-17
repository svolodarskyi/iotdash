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


# ── Device ────────────────────────────────────────────
class DeviceOut(BaseModel):
    id: uuid.UUID
    device_code: str
    name: str
    organisation_id: uuid.UUID
    device_type: str
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
