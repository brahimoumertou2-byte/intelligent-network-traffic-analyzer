from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from .. import crud, models, schemas

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

@router.get("", response_model=list[schemas.AlertRead])
def list_alerts(offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), alert_status: str | None = Query(None, alias="status"), severity: str | None = None, db: Session = Depends(get_db)):
    q = select(models.Alert)
    if alert_status: q = q.where(models.Alert.status == alert_status)
    if severity: q = q.where(models.Alert.severity == severity)
    return list(db.scalars(q.order_by(models.Alert.timestamp.desc()).offset(offset).limit(limit)))

@router.post("", response_model=schemas.AlertRead, status_code=201)
def add_alert(payload: schemas.AlertCreate, db: Session = Depends(get_db)): return crud.create_alert(db, payload)

@router.patch("/{alert_id}", response_model=schemas.AlertRead)
def update_alert(alert_id: int, payload: schemas.AlertUpdate, db: Session = Depends(get_db)):
    row = db.get(models.Alert, alert_id)
    if row is None: raise HTTPException(404, "Alert not found")
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(row, key, value)
    db.commit(); db.refresh(row); return row

@router.delete("/{alert_id}", status_code=204)
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    row = db.get(models.Alert, alert_id)
    if row is None: raise HTTPException(404, "Alert not found")
    db.delete(row); db.commit(); return Response(status_code=204)
