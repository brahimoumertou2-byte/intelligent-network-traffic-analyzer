"""Small shared CRUD helpers."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from . import models, schemas

def create_traffic(db: Session, data: schemas.TrafficCreate):
    row = models.Traffic(**data.model_dump(exclude={"timestamp"}), timestamp=data.timestamp or models.utcnow())
    db.add(row); db.commit(); db.refresh(row); return row

def create_alert(db: Session, data: schemas.AlertCreate):
    values = data.model_dump(exclude={"timestamp"})
    row = models.Alert(**values, timestamp=data.timestamp or models.utcnow())
    db.add(row); db.commit(); db.refresh(row); return row

def create_device(db: Session, data: schemas.DeviceCreate):
    row = models.Device(**data.model_dump(exclude={"last_seen"}), last_seen=data.last_seen or models.utcnow())
    db.add(row); db.commit(); db.refresh(row); return row

def get_or_404(db: Session, model, row_id: int):
    row = db.get(model, row_id)
    return row

def list_rows(db: Session, model, offset=0, limit=100):
    return list(db.scalars(select(model).order_by(model.id.desc()).offset(offset).limit(limit)))
