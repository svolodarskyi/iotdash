import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.auth import require_admin
from app.database import get_db
from app.models import DeviceProvisioned, DeviceType, DeviceTypeMetric, Metric, User
from app.schemas import DeviceTypeCreate, DeviceTypeMetricOut, DeviceTypeOut, DeviceTypeUpdate

router = APIRouter(prefix="/api/admin/device-types", tags=["admin-device-types"])


def _build_device_type_out(dt: DeviceType) -> DeviceTypeOut:
    return DeviceTypeOut(
        id=dt.id,
        name=dt.name,
        description=dt.description,
        allowed_metrics=[
            DeviceTypeMetricOut(
                metric_id=dtm.metric_id,
                metric_name=dtm.metric.name,
                metric_unit=dtm.metric.unit,
            )
            for dtm in dt.allowed_metrics
        ],
        created_at=dt.created_at,
    )


@router.get("", response_model=list[DeviceTypeOut])
def list_device_types(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    dts = (
        db.query(DeviceType)
        .options(joinedload(DeviceType.allowed_metrics).joinedload(DeviceTypeMetric.metric))
        .order_by(DeviceType.name)
        .all()
    )
    return [_build_device_type_out(dt) for dt in dts]


@router.post("", response_model=DeviceTypeOut, status_code=201)
def create_device_type(
    body: DeviceTypeCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if db.query(DeviceType).filter(DeviceType.name == body.name).first():
        raise HTTPException(status_code=409, detail="Device type name already exists")

    dt = DeviceType(name=body.name, description=body.description)
    db.add(dt)
    db.flush()

    for metric_id in body.metric_ids:
        metric = db.query(Metric).filter(Metric.id == metric_id).first()
        if not metric:
            raise HTTPException(status_code=404, detail=f"Metric {metric_id} not found")
        db.add(DeviceTypeMetric(device_type_id=dt.id, metric_id=metric.id))

    db.commit()

    dt = (
        db.query(DeviceType)
        .options(joinedload(DeviceType.allowed_metrics).joinedload(DeviceTypeMetric.metric))
        .filter(DeviceType.id == dt.id)
        .first()
    )
    return _build_device_type_out(dt)


@router.put("/{device_type_id}", response_model=DeviceTypeOut)
def update_device_type(
    device_type_id: uuid.UUID,
    body: DeviceTypeUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    dt = db.query(DeviceType).filter(DeviceType.id == device_type_id).first()
    if not dt:
        raise HTTPException(status_code=404, detail="Device type not found")

    if body.name is not None:
        existing = db.query(DeviceType).filter(
            DeviceType.name == body.name, DeviceType.id != device_type_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Device type name already exists")
        dt.name = body.name
    if body.description is not None:
        dt.description = body.description
    if body.metric_ids is not None:
        # Replace allowed metrics
        db.query(DeviceTypeMetric).filter(DeviceTypeMetric.device_type_id == device_type_id).delete()
        for metric_id in body.metric_ids:
            metric = db.query(Metric).filter(Metric.id == metric_id).first()
            if not metric:
                raise HTTPException(status_code=404, detail=f"Metric {metric_id} not found")
            db.add(DeviceTypeMetric(device_type_id=dt.id, metric_id=metric.id))

    db.commit()

    dt = (
        db.query(DeviceType)
        .options(joinedload(DeviceType.allowed_metrics).joinedload(DeviceTypeMetric.metric))
        .filter(DeviceType.id == dt.id)
        .first()
    )
    return _build_device_type_out(dt)


@router.delete("/{device_type_id}", status_code=204)
def delete_device_type(
    device_type_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    dt = db.query(DeviceType).filter(DeviceType.id == device_type_id).first()
    if not dt:
        raise HTTPException(status_code=404, detail="Device type not found")
    if db.query(DeviceProvisioned).filter(DeviceProvisioned.device_type_id == device_type_id).first():
        raise HTTPException(status_code=409, detail="Cannot delete device type with provisioned devices")
    db.delete(dt)
    db.commit()
