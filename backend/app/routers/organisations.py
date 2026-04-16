import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Device, Organisation
from app.schemas import DeviceOut, OrganisationOut

router = APIRouter(prefix="/api/organisations", tags=["organisations"])


@router.get("", response_model=list[OrganisationOut])
def list_organisations(db: Session = Depends(get_db)):
    return db.query(Organisation).all()


@router.get("/{org_id}", response_model=OrganisationOut)
def get_organisation(org_id: uuid.UUID, db: Session = Depends(get_db)):
    org = db.query(Organisation).filter(Organisation.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return org


@router.get("/{org_id}/devices", response_model=list[DeviceOut])
def list_org_devices(org_id: uuid.UUID, db: Session = Depends(get_db)):
    org = db.query(Organisation).filter(Organisation.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return db.query(Device).filter(Device.organisation_id == org_id).all()
