from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..database import get_db
from .. import crud, models, schemas
from ..services.devices import active_device_cutoff, is_active_device

router = APIRouter(prefix="/api/devices", tags=["devices"])

@router.get("", response_model=list[schemas.DeviceRead])
def list_devices(offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), device_status: str | None = Query(None, alias="status"), db: Session = Depends(get_db)):
    q = select(models.Device)
    cutoff = active_device_cutoff()
    if device_status == "active":
        q = q.where(models.Device.status == "active", models.Device.last_seen >= cutoff)
    elif device_status == "inactive":
        q = q.where(or_(models.Device.status != "active", models.Device.last_seen < cutoff))
    rows = list(db.scalars(q.order_by(models.Device.last_seen.desc()).offset(offset).limit(limit)))
    return [_device_response(row, cutoff) for row in rows]

@router.get("/{device_id}", response_model=schemas.DeviceRead)
def get_device(device_id: int, db: Session = Depends(get_db)):
    row = db.get(models.Device, device_id)
    if row is None: raise HTTPException(404, "Device not found")
    return _device_response(row)

@router.post("", response_model=schemas.DeviceRead, status_code=201)
def add_device(payload: schemas.DeviceCreate, db: Session = Depends(get_db)):
    try: return _device_response(crud.create_device(db, payload))
    except IntegrityError as exc: db.rollback(); raise HTTPException(409, "A device with this IP address already exists") from exc

@router.patch("/{device_id}", response_model=schemas.DeviceRead)
def update_device(device_id: int, payload: schemas.DeviceUpdate, db: Session = Depends(get_db)):
    row = db.get(models.Device, device_id)
    if row is None: raise HTTPException(404, "Device not found")
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(row, key, value)
    db.commit(); db.refresh(row); return _device_response(row)

@router.delete("/{device_id}", status_code=204)
def delete_device(device_id: int, db: Session = Depends(get_db)):
    row = db.get(models.Device, device_id)
    if row is None: raise HTTPException(404, "Device not found")
    db.delete(row); db.commit(); return Response(status_code=204)


def _device_response(row: models.Device, cutoff=None) -> schemas.DeviceRead:
    """Expose the same derived active state used by the dashboard KPI."""
    response = schemas.DeviceRead.model_validate(row)
    return response.model_copy(update={"status": "active" if is_active_device(row, cutoff) else "inactive"})
