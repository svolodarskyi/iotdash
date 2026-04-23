from fastapi import APIRouter, Depends

from app.auth import require_admin
from app.config import settings
from app.models import User

router = APIRouter(prefix="/api/admin/external-services", tags=["admin-external"])


@router.get("")
def get_external_services(
    admin: User = Depends(require_admin),
):
    """Get URLs for external services (Grafana, InfluxDB, EMQX).

    Returns URLs that can be used by admins to access external service UIs.
    EMQX web UI runs on port 18083 (dashboard), not 1883 (MQTT).
    """
    # Replace internal docker hostnames with localhost for browser access
    grafana_url = settings.GRAFANA_URL.replace("http://grafana:", "http://localhost:")
    influxdb_url = settings.INFLUXDB_URL.replace("http://influxdb:", "http://localhost:")
    emqx_url = settings.EMQX_WEB_URL.replace("http://emqx:", "http://localhost:")

    return {
        "grafana_url": grafana_url,
        "influxdb_url": influxdb_url,
        "emqx_url": emqx_url,
    }
