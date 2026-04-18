import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.auth import require_admin
from app.database import get_db
from app.models import (
    Alert,
    DeviceProvisioned,
    DeviceProvisionedMetric,
    DeviceType,
    DeviceTypeMetric,
    Metric,
    Organisation,
    User,
)
from app.schemas import (
    DeviceAdminOut,
    DeviceCreate,
    DeviceMetricOut,
    DeviceMetricUpdate,
    DeviceSendConfigResponse,
    DeviceUpdate,
)
from app.services.mqtt_publisher import MqttPublisher, get_mqtt_publisher

router = APIRouter(prefix="/api/admin/devices", tags=["admin-devices"])


def _build_device_admin_out(device: DeviceProvisioned) -> DeviceAdminOut:
    metrics = [
        DeviceMetricOut(
            metric_id=dm.metric_id,
            metric_name=dm.metric.name,
            metric_unit=dm.metric.unit,
            is_enabled=dm.is_enabled,
            enabled_at=dm.enabled_at,
            disabled_at=dm.disabled_at,
        )
        for dm in device.device_metrics
    ]
    return DeviceAdminOut(
        id=device.id,
        device_code=device.device_code,
        name=device.name,
        organisation_id=device.organisation_id,
        organisation_name=device.organisation.name,
        device_type_id=device.device_type_id,
        device_type_name=device.device_type.name,
        is_active=device.is_active,
        metrics=metrics,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


def _build_metrics_state(
    db: Session, device_type_id: uuid.UUID, enabled_metric_ids: set[uuid.UUID]
) -> dict[str, int]:
    """Build {metric_name: 1|0} for ALL metrics the device type supports."""
    type_metrics = (
        db.query(DeviceTypeMetric)
        .join(Metric, DeviceTypeMetric.metric_id == Metric.id)
        .filter(DeviceTypeMetric.device_type_id == device_type_id)
        .all()
    )
    return {
        tm.metric.name: (1 if tm.metric_id in enabled_metric_ids else 0)
        for tm in type_metrics
    }


def _load_device_with_relations(db: Session, device_id: uuid.UUID) -> DeviceProvisioned | None:
    return (
        db.query(DeviceProvisioned)
        .options(
            joinedload(DeviceProvisioned.device_metrics).joinedload(DeviceProvisionedMetric.metric),
            joinedload(DeviceProvisioned.organisation),
            joinedload(DeviceProvisioned.device_type),
        )
        .filter(DeviceProvisioned.id == device_id)
        .first()
    )


@router.get("/device-types", response_model=list[str])
def list_device_type_names(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Return distinct device type names (for filter dropdown)."""
    rows = db.query(DeviceType.name).order_by(DeviceType.name).all()
    return [r[0] for r in rows]


@router.get("", response_model=list[DeviceAdminOut])
def list_devices(
    org_id: uuid.UUID | None = None,
    device_type_id: uuid.UUID | None = None,
    metric_name: str | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    q = db.query(DeviceProvisioned).options(
        joinedload(DeviceProvisioned.device_metrics).joinedload(DeviceProvisionedMetric.metric),
        joinedload(DeviceProvisioned.organisation),
        joinedload(DeviceProvisioned.device_type),
    )
    if org_id:
        q = q.filter(DeviceProvisioned.organisation_id == org_id)
    if device_type_id:
        q = q.filter(DeviceProvisioned.device_type_id == device_type_id)
    if metric_name:
        q = (
            q.join(DeviceProvisioned.device_metrics)
            .join(DeviceProvisionedMetric.metric)
            .filter(Metric.name == metric_name)
        )
    devices = q.order_by(DeviceProvisioned.device_code).all()
    # deduplicate in case the metric join produced duplicates
    seen = set()
    unique = []
    for d in devices:
        if d.id not in seen:
            seen.add(d.id)
            unique.append(d)
    return [_build_device_admin_out(d) for d in unique]


@router.post("", response_model=DeviceAdminOut, status_code=201)
def provision_device(
    body: DeviceCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    mqtt: MqttPublisher = Depends(get_mqtt_publisher),
):
    # Generate device_code if not provided
    device_code = body.device_code or f"dev-{uuid.uuid4().hex[:8]}"

    # Validate uniqueness
    if db.query(DeviceProvisioned).filter(DeviceProvisioned.device_code == device_code).first():
        raise HTTPException(status_code=409, detail="Device code already exists")

    # Validate org exists
    org = db.query(Organisation).filter(Organisation.id == body.organisation_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    # Validate device type exists
    device_type = db.query(DeviceType).filter(DeviceType.id == body.device_type_id).first()
    if not device_type:
        raise HTTPException(status_code=404, detail="Device type not found")

    # Validate metric_ids are allowed for this device type
    if body.metric_ids:
        allowed_metric_ids = set(
            row[0]
            for row in db.query(DeviceTypeMetric.metric_id)
            .filter(DeviceTypeMetric.device_type_id == body.device_type_id)
            .all()
        )
        requested = set(body.metric_ids)
        invalid = requested - allowed_metric_ids
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Metrics {[str(m) for m in invalid]} not supported by device type '{device_type.name}'",
            )

    device = DeviceProvisioned(
        device_code=device_code,
        name=body.name,
        organisation_id=body.organisation_id,
        device_type_id=body.device_type_id,
    )
    db.add(device)
    db.flush()

    # Link metrics
    metric_names: list[str] = []
    for metric_id in body.metric_ids:
        metric = db.query(Metric).filter(Metric.id == metric_id).first()
        if not metric:
            raise HTTPException(status_code=404, detail=f"Metric {metric_id} not found")
        dm = DeviceProvisionedMetric(device_id=device.id, metric_id=metric.id)
        db.add(dm)
        metric_names.append(metric.name)

    db.commit()

    # Send MQTT config if auto_enable
    if body.auto_enable:
        enabled_ids = set(body.metric_ids)
        state = _build_metrics_state(db, body.device_type_id, enabled_ids)
        if state:
            mqtt.sync_device_metrics(device_code, state)

    device = _load_device_with_relations(db, device.id)
    return _build_device_admin_out(device)


@router.put("/{device_id}", response_model=DeviceAdminOut)
def update_device(
    device_id: uuid.UUID,
    body: DeviceUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    device = _load_device_with_relations(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if body.name is not None:
        device.name = body.name
    if body.device_type_id is not None:
        dt = db.query(DeviceType).filter(DeviceType.id == body.device_type_id).first()
        if not dt:
            raise HTTPException(status_code=404, detail="Device type not found")
        device.device_type_id = body.device_type_id
    if body.is_active is not None:
        device.is_active = body.is_active
    db.commit()
    db.refresh(device)
    device = _load_device_with_relations(db, device_id)
    return _build_device_admin_out(device)


@router.delete("/{device_id}", status_code=204)
def delete_device(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    device = db.query(DeviceProvisioned).filter(DeviceProvisioned.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    db.query(Alert).filter(Alert.device_id == device_id).delete()
    db.query(DeviceProvisionedMetric).filter(DeviceProvisionedMetric.device_id == device_id).delete()
    db.delete(device)
    db.commit()


@router.patch("/{device_id}/metrics", response_model=DeviceAdminOut)
def update_device_metrics(
    device_id: uuid.UUID,
    body: DeviceMetricUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    mqtt: MqttPublisher = Depends(get_mqtt_publisher),
):
    device = db.query(DeviceProvisioned).filter(DeviceProvisioned.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Validate metric_ids are allowed for this device type
    if body.metric_ids:
        allowed_metric_ids = set(
            row[0]
            for row in db.query(DeviceTypeMetric.metric_id)
            .filter(DeviceTypeMetric.device_type_id == device.device_type_id)
            .all()
        )
        requested = set(body.metric_ids)
        invalid = requested - allowed_metric_ids
        if invalid:
            device_type = db.query(DeviceType).filter(DeviceType.id == device.device_type_id).first()
            raise HTTPException(
                status_code=400,
                detail=f"Metrics {[str(m) for m in invalid]} not supported by device type '{device_type.name}'",
            )

    # Remove existing device_metrics
    db.query(DeviceProvisionedMetric).filter(DeviceProvisionedMetric.device_id == device_id).delete()

    # Add new ones (only enabled metrics stored)
    for metric_id in body.metric_ids:
        metric = db.query(Metric).filter(Metric.id == metric_id).first()
        if not metric:
            raise HTTPException(status_code=404, detail=f"Metric {metric_id} not found")
        dm = DeviceProvisionedMetric(device_id=device.id, metric_id=metric.id)
        db.add(dm)

    db.commit()

    # Send full metrics state to device
    if body.send_config:
        enabled_ids = set(body.metric_ids)
        state = _build_metrics_state(db, device.device_type_id, enabled_ids)
        if state:
            mqtt.sync_device_metrics(device.device_code, state)

    device = _load_device_with_relations(db, device_id)
    return _build_device_admin_out(device)


@router.post("/{device_id}/sync-config", response_model=DeviceSendConfigResponse)
def sync_device_config(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    mqtt: MqttPublisher = Depends(get_mqtt_publisher),
):
    device = (
        db.query(DeviceProvisioned)
        .options(
            joinedload(DeviceProvisioned.device_metrics).joinedload(DeviceProvisionedMetric.metric)
        )
        .filter(DeviceProvisioned.id == device_id)
        .first()
    )
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    enabled_ids = {dm.metric_id for dm in device.device_metrics if dm.is_enabled}
    state = _build_metrics_state(db, device.device_type_id, enabled_ids)
    if not state:
        raise HTTPException(status_code=400, detail="No metrics configured for this device type")

    success = mqtt.sync_device_metrics(device.device_code, state)
    enabled_names = [name for name, val in state.items() if val == 1]
    return DeviceSendConfigResponse(
        device_code=device.device_code,
        metrics_sent=enabled_names,
        success=success,
    )
