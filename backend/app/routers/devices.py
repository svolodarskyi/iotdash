import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Device, GrafanaDashboard, User
from app.schemas import DeviceEmbedUrlsOut, DeviceOut, EmbedUrl

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", response_model=list[DeviceOut])
def list_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Device)
        .filter(Device.organisation_id == current_user.organisation_id)
        .all()
    )


@router.get("/{device_id}", response_model=DeviceOut)
def get_device(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = (
        db.query(Device)
        .filter(Device.id == device_id, Device.organisation_id == current_user.organisation_id)
        .first()
    )
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.get("/{device_id}/embed-urls", response_model=DeviceEmbedUrlsOut)
def get_device_embed_urls(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = (
        db.query(Device)
        .filter(Device.id == device_id, Device.organisation_id == current_user.organisation_id)
        .first()
    )
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    dashboards = (
        db.query(GrafanaDashboard)
        .filter(GrafanaDashboard.organisation_id == current_user.organisation_id)
        .all()
    )

    urls: list[EmbedUrl] = []
    grafana_url = settings.GRAFANA_URL
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
