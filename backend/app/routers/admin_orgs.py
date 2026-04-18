import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import DeviceProvisioned, GrafanaDashboard, Organisation, User
from app.schemas import OrgCreate, OrgUpdate, OrganisationOut
from app.services.grafana_client import GrafanaClient, get_grafana_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/organisations", tags=["admin-organisations"])

DASHBOARD_JSON_PATH = "/app/grafana/provisioning/dashboards/iot-metrics.json"


@router.get("", response_model=list[OrganisationOut])
def list_orgs(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return db.query(Organisation).order_by(Organisation.name).all()


def _load_dashboard_template() -> dict:
    """Load the default IoT Metrics dashboard JSON template."""
    try:
        with open(DASHBOARD_JSON_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Dashboard template not found at %s", DASHBOARD_JSON_PATH)
        return {}


@router.post("", response_model=OrganisationOut, status_code=201)
def create_org(
    body: OrgCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    grafana: GrafanaClient = Depends(get_grafana_client),
):
    if db.query(Organisation).filter(Organisation.name == body.name).first():
        raise HTTPException(status_code=409, detail="Organisation name already exists")
    org = Organisation(name=body.name)
    db.add(org)
    db.flush()

    # Provision in Grafana
    try:
        grafana_org_id = grafana.create_org(body.name)
        org.grafana_org_id = grafana_org_id

        grafana.add_datasource_to_org(grafana_org_id)

        dashboard_json = _load_dashboard_template()
        if dashboard_json:
            # Reset id/uid so Grafana assigns fresh ones for this org
            dashboard_json["id"] = None
            dashboard_uid = grafana.create_dashboard_in_org(grafana_org_id, dashboard_json)

            dashboard_record = GrafanaDashboard(
                organisation_id=org.id,
                title=dashboard_json.get("title", "IoT Metrics"),
                grafana_uid=dashboard_uid,
                grafana_org_id=grafana_org_id,
                panel_ids=[p["id"] for p in dashboard_json.get("panels", [])],
                embed_base_url="http://grafana:3000",
            )
            db.add(dashboard_record)
    except HTTPException:
        logger.warning("Grafana provisioning failed for org %s — continuing without it", body.name)

    db.commit()
    db.refresh(org)
    return org


@router.put("/{org_id}", response_model=OrganisationOut)
def update_org(
    org_id: uuid.UUID,
    body: OrgUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    org = db.query(Organisation).filter(Organisation.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    if body.name is not None:
        existing = db.query(Organisation).filter(Organisation.name == body.name, Organisation.id != org_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Organisation name already exists")
        org.name = body.name
    db.commit()
    db.refresh(org)
    return org


@router.delete("/{org_id}", status_code=204)
def delete_org(
    org_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    org = db.query(Organisation).filter(Organisation.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    if db.query(DeviceProvisioned).filter(DeviceProvisioned.organisation_id == org_id).first():
        raise HTTPException(status_code=409, detail="Cannot delete organisation with devices")
    if db.query(User).filter(User.organisation_id == org_id).first():
        raise HTTPException(status_code=409, detail="Cannot delete organisation with users")
    db.delete(org)
    db.commit()
