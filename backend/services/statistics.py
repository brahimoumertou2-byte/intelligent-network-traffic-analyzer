"""Database-backed dashboard aggregates."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .. import models
from .devices import active_device_cutoff

def overview(db: Session):
    cutoff = active_device_cutoff()
    return {"total_packets": db.scalar(select(func.count(models.Traffic.id))) or 0,
            "traffic_volume": db.scalar(select(func.coalesce(func.sum(models.Traffic.packet_size), 0))) or 0,
            "active_devices": db.scalar(select(func.count(models.Device.id)).where(models.Device.status == "active", models.Device.last_seen >= cutoff)) or 0,
            "total_alerts": db.scalar(select(func.count(models.Alert.id)).where(models.Alert.status == "open")) or 0}

def protocols(db):
    return [{"protocol": p, "count": int(n)} for p, n in db.execute(select(models.Traffic.protocol, func.count()).group_by(models.Traffic.protocol).order_by(func.count().desc()))]

def top_ips(db, limit=10):
    sources = [{"ip": ip, "count": int(n), "direction": "source"} for ip, n in db.execute(select(models.Traffic.source_ip, func.count()).group_by(models.Traffic.source_ip).order_by(func.count().desc()).limit(limit))]
    destinations = [{"ip": ip, "count": int(n), "direction": "destination"} for ip, n in db.execute(select(models.Traffic.destination_ip, func.count()).group_by(models.Traffic.destination_ip).order_by(func.count().desc()).limit(limit))]
    return {"sources": sources, "destinations": destinations}

def top_ports(db, limit=10):
    return [{"port": port, "count": int(n)} for port, n in db.execute(select(models.Traffic.destination_port, func.count()).where(models.Traffic.destination_port.is_not(None)).group_by(models.Traffic.destination_port).order_by(func.count().desc()).limit(limit))]

def timeline(db, buckets=24):
    rows = db.scalars(select(models.Traffic).order_by(models.Traffic.timestamp.desc()).limit(5000)).all()
    grouped = {}
    for row in rows:
        stamp = row.timestamp
        if stamp.tzinfo is None: stamp = stamp.replace(tzinfo=__import__('datetime').timezone.utc)
        key = stamp.replace(minute=0, second=0, microsecond=0).isoformat()
        grouped[key] = grouped.get(key, 0) + 1
    return [{"timestamp": key, "packets": grouped[key]} for key in sorted(grouped)][-buckets:]
