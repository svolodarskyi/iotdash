import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_admin
from app.config import settings
from app.database import get_db
from app.models import DeviceProvisioned, DeviceProvisionedMetric, GrafanaDashboard, User
from app.schemas import DeviceEmbedUrlsOut, DeviceMetricOut, DeviceOut, EmbedUrl

router = APIRouter(prefix="/api/devices", tags=["devices"])


def _get_device_for_user(
    db: Session, device_id: uuid.UUID, current_user: User
) -> DeviceProvisioned | None:
    """Load a device, allowing admins to access any org's devices."""
    q = db.query(DeviceProvisioned).filter(DeviceProvisioned.id == device_id)
    if current_user.role != "admin":
        q = q.filter(DeviceProvisioned.organisation_id == current_user.organisation_id)
    return q.first()


@router.get("", response_model=list[DeviceOut])
def list_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    devices = (
        db.query(DeviceProvisioned)
        .filter(DeviceProvisioned.organisation_id == current_user.organisation_id)
        .all()
    )
    return [
        DeviceOut(
            id=d.id,
            device_code=d.device_code,
            name=d.name,
            organisation_id=d.organisation_id,
            device_type_id=d.device_type_id,
            device_type_name=d.device_type.name,
            metadata_=d.metadata_,
            is_active=d.is_active,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in devices
    ]


@router.get("/{device_id}", response_model=DeviceOut)
def get_device(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = _get_device_for_user(db, device_id, current_user)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceOut(
        id=device.id,
        device_code=device.device_code,
        name=device.name,
        organisation_id=device.organisation_id,
        device_type_id=device.device_type_id,
        device_type_name=device.device_type.name,
        metadata_=device.metadata_,
        is_active=device.is_active,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


@router.get("/{device_id}/embed-urls", response_model=DeviceEmbedUrlsOut)
def get_device_embed_urls(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    device = _get_device_for_user(db, device_id, admin)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Query enabled metrics for this device
    device_metrics = (
        db.query(DeviceProvisionedMetric)
        .join(DeviceProvisionedMetric.metric)
        .filter(
            DeviceProvisionedMetric.device_id == device.id,
            DeviceProvisionedMetric.is_enabled.is_(True),
        )
        .all()
    )

    urls: list[EmbedUrl] = []
    grafana_url = settings.GRAFANA_URL

    if device_metrics:
        for dm in device_metrics:
            url = (
                f"{grafana_url}/d-solo/iot-metrics"
                f"?orgId=1&panelId=1"
                f"&var-device_id={device.device_code}"
                f"&var-metric={dm.metric.name}"
            )
            urls.append(
                EmbedUrl(
                    dashboard_title=f"{dm.metric.name} ({dm.metric.unit or ''})",
                    panel_id=1,
                    url=url,
                )
            )
    else:
        dashboards = (
            db.query(GrafanaDashboard)
            .filter(GrafanaDashboard.organisation_id == device.organisation_id)
            .all()
        )
        for dash in dashboards:
            panel_ids = dash.panel_ids or []
            for panel_id in panel_ids:
                url = (
                    f"{grafana_url}/d-solo/{dash.grafana_uid}"
                    f"?orgId=1&panelId={panel_id}"
                    f"&var-device_id={device.device_code}"
                )
                urls.append(EmbedUrl(dashboard_title=dash.title, panel_id=panel_id, url=url))

    return DeviceEmbedUrlsOut(device_id=device.id, device_code=device.device_code, urls=urls)


@router.get("/{device_id}/metrics", response_model=list[DeviceMetricOut])
def get_device_metrics(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = _get_device_for_user(db, device_id, current_user)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device_metrics = (
        db.query(DeviceProvisionedMetric)
        .join(DeviceProvisionedMetric.metric)
        .filter(
            DeviceProvisionedMetric.device_id == device.id,
            DeviceProvisionedMetric.is_enabled.is_(True),
        )
        .all()
    )
    return [
        DeviceMetricOut(
            metric_id=dm.metric_id,
            metric_name=dm.metric.name,
            metric_unit=dm.metric.unit,
            is_enabled=dm.is_enabled,
            enabled_at=dm.enabled_at,
            disabled_at=dm.disabled_at,
        )
        for dm in device_metrics
    ]
