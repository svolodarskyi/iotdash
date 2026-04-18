import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Alert, DeviceProvisioned, DeviceProvisionedMetric, Metric, User
from app.schemas import AlertCreate, AlertOut, AlertToggle, AlertUpdate
from app.services.grafana_client import GrafanaClient, get_grafana_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _alert_to_out(alert: Alert) -> AlertOut:
    """Build AlertOut from an Alert model, pulling device_code from the relationship."""
    return AlertOut(
        id=alert.id,
        device_id=alert.device_id,
        device_code=alert.device.device_code,
        organisation_name=alert.device.organisation.name if alert.device.organisation else None,
        created_by=alert.created_by,
        metric=alert.metric,
        condition=alert.condition,
        threshold=alert.threshold,
        duration_seconds=alert.duration_seconds,
        notification_email=alert.notification_email,
        is_enabled=alert.is_enabled,
        grafana_rule_uid=alert.grafana_rule_uid,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


def _get_alert_for_user(
    alert_id: uuid.UUID,
    current_user: User,
    db: Session,
) -> Alert:
    """Load an alert. Admins can access any alert; viewers only their org's."""
    q = db.query(Alert).join(DeviceProvisioned).filter(Alert.id == alert_id)
    if current_user.role != "admin":
        q = q.filter(DeviceProvisioned.organisation_id == current_user.organisation_id)
    alert = q.first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


def _validate_metric_on_device(db: Session, device_id: uuid.UUID, metric_name: str) -> None:
    """Validate that the metric is enabled on the device."""
    dm = (
        db.query(DeviceProvisionedMetric)
        .join(Metric)
        .filter(
            DeviceProvisionedMetric.device_id == device_id,
            Metric.name == metric_name,
            DeviceProvisionedMetric.is_enabled.is_(True),
        )
        .first()
    )
    if not dm:
        raise HTTPException(status_code=400, detail=f"Metric '{metric_name}' not enabled on this device")


@router.get("", response_model=list[AlertOut])
def list_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Alert).join(DeviceProvisioned)
    if current_user.role != "admin":
        q = q.filter(DeviceProvisioned.organisation_id == current_user.organisation_id)
    alerts = q.all()
    return [_alert_to_out(a) for a in alerts]


@router.post("", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
def create_alert(
    body: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    grafana: GrafanaClient = Depends(get_grafana_client),
):
    # Verify device exists (admins can use any device; viewers only their org's)
    q = db.query(DeviceProvisioned).filter(DeviceProvisioned.id == body.device_id)
    if current_user.role != "admin":
        q = q.filter(DeviceProvisioned.organisation_id == current_user.organisation_id)
    device = q.first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Validate metric is enabled on device
    _validate_metric_on_device(db, device.id, body.metric)

    alert = Alert(
        device_id=body.device_id,
        created_by=current_user.id,
        metric=body.metric,
        condition=body.condition,
        threshold=body.threshold,
        duration_seconds=body.duration_seconds,
        notification_email=body.notification_email,
    )
    db.add(alert)
    db.flush()  # get alert.id before Grafana calls

    # Sync to Grafana
    try:
        folder_uid = grafana.ensure_alerts_folder()
        rule_uid = grafana.create_alert_rule(
            alert, device, device.organisation, folder_uid
        )
        alert.grafana_rule_uid = rule_uid
        grafana.ensure_contact_point(alert)
        grafana.ensure_notification_policy(alert)
    except HTTPException:
        logger.warning("Grafana sync failed for alert %s — saving without rule", alert.id)

    db.commit()
    db.refresh(alert)
    return _alert_to_out(alert)


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = _get_alert_for_user(alert_id, current_user, db)
    return _alert_to_out(alert)


@router.put("/{alert_id}", response_model=AlertOut)
def update_alert(
    alert_id: uuid.UUID,
    body: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    grafana: GrafanaClient = Depends(get_grafana_client),
):
    alert = _get_alert_for_user(alert_id, current_user, db)

    update_data = body.model_dump(exclude_unset=True)

    # Validate metric if being changed
    if "metric" in update_data:
        _validate_metric_on_device(db, alert.device_id, update_data["metric"])

    for field, value in update_data.items():
        setattr(alert, field, value)

    # Sync to Grafana — update existing rule or create if missing
    try:
        folder_uid = grafana.ensure_alerts_folder()
        if alert.grafana_rule_uid:
            grafana.update_alert_rule(
                alert.grafana_rule_uid, alert, alert.device, alert.device.organisation, folder_uid
            )
            if "notification_email" in update_data:
                grafana.ensure_contact_point(alert)
        else:
            rule_uid = grafana.create_alert_rule(
                alert, alert.device, alert.device.organisation, folder_uid
            )
            alert.grafana_rule_uid = rule_uid
            grafana.ensure_contact_point(alert)
            grafana.ensure_notification_policy(alert)
    except HTTPException:
        logger.warning("Grafana sync failed for alert %s update", alert.id)

    db.commit()
    db.refresh(alert)
    return _alert_to_out(alert)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    grafana: GrafanaClient = Depends(get_grafana_client),
):
    alert = _get_alert_for_user(alert_id, current_user, db)

    # Clean up Grafana resources
    if alert.grafana_rule_uid:
        try:
            grafana.delete_alert_rule(alert.grafana_rule_uid)
        except HTTPException:
            logger.warning("Failed to delete Grafana rule %s", alert.grafana_rule_uid)
    try:
        grafana.delete_contact_point(alert.id)
        grafana.remove_notification_policy(alert.id)
    except HTTPException:
        logger.warning("Failed to clean up Grafana contact point for alert %s", alert.id)

    db.delete(alert)
    db.commit()


@router.patch("/{alert_id}/toggle", response_model=AlertOut)
def toggle_alert(
    alert_id: uuid.UUID,
    body: AlertToggle,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    grafana: GrafanaClient = Depends(get_grafana_client),
):
    alert = _get_alert_for_user(alert_id, current_user, db)
    alert.is_enabled = body.is_enabled

    # Pause/unpause in Grafana — or create rule if missing
    try:
        folder_uid = grafana.ensure_alerts_folder()
        if alert.grafana_rule_uid:
            grafana.update_alert_rule(
                alert.grafana_rule_uid,
                alert,
                alert.device,
                alert.device.organisation,
                folder_uid,
                is_paused=not body.is_enabled,
            )
        else:
            rule_uid = grafana.create_alert_rule(
                alert, alert.device, alert.device.organisation, folder_uid
            )
            alert.grafana_rule_uid = rule_uid
            grafana.ensure_contact_point(alert)
            grafana.ensure_notification_policy(alert)
    except HTTPException:
        logger.warning("Failed to sync Grafana rule for alert %s", alert.id)

    db.commit()
    db.refresh(alert)
    return _alert_to_out(alert)
