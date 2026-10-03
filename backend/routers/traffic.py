from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from .. import crud, models, schemas
from ..services.alerts import evaluate_traffic
from ..services.devices import observe_local_devices

router = APIRouter(prefix="/api/traffic", tags=["traffic"])

@router.post("", response_model=schemas.TrafficRead, status_code=status.HTTP_201_CREATED)
def add_traffic(payload: schemas.TrafficCreate, db: Session = Depends(get_db)):
    row = crud.create_traffic(db, payload)
    # Alert evaluation precedes device tracking so the first local observation
    # creates one alert; subsequent records are deduplicated by the alert service.
    evaluate_traffic(db, row)
    observe_local_devices(db, row)
    db.commit()
    return row

@router.get("", response_model=list[schemas.TrafficRead])
def list_traffic(offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), source_ip: str | None = None, destination_ip: str | None = None, protocol: str | None = None, db: Session = Depends(get_db)):
    query = select(models.Traffic)
    if source_ip: query = query.where(models.Traffic.source_ip == source_ip)
    if destination_ip: query = query.where(models.Traffic.destination_ip == destination_ip)
    if protocol: query = query.where(models.Traffic.protocol == protocol.upper())
    return list(db.scalars(query.order_by(models.Traffic.timestamp.desc()).offset(offset).limit(limit)))

@router.get("/{traffic_id}", response_model=schemas.TrafficRead)
def get_traffic(traffic_id: int, db: Session = Depends(get_db)):
    row = db.get(models.Traffic, traffic_id)
    if row is None: raise HTTPException(404, "Traffic record not found")
    return row

@router.delete("/{traffic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_traffic(traffic_id: int, db: Session = Depends(get_db)):
    row = db.get(models.Traffic, traffic_id)
    if row is None: raise HTTPException(404, "Traffic record not found")
    db.delete(row); db.commit(); return Response(status_code=204)
