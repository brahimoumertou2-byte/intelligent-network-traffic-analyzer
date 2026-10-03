from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..services import statistics

router = APIRouter(prefix="/api/statistics", tags=["statistics"])

@router.get("/overview")
def get_overview(db: Session = Depends(get_db)): return statistics.overview(db)

@router.get("/protocols")
def get_protocols(db: Session = Depends(get_db)): return statistics.protocols(db)

@router.get("/top-ips")
def get_top_ips(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)): return statistics.top_ips(db, limit)

@router.get("/top-ports")
def get_top_ports(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)): return statistics.top_ports(db, limit)

@router.get("/timeline")
def get_timeline(buckets: int = Query(24, ge=1, le=168), db: Session = Depends(get_db)): return statistics.timeline(db, buckets)
