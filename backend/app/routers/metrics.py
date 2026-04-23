from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import Metric, User
from app.schemas import MetricOut

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("", response_model=list[MetricOut])
def list_metrics(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return db.query(Metric).order_by(Metric.name).all()
