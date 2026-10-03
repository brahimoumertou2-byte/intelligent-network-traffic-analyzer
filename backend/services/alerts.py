"""Configurable, defensive traffic alert rules."""
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .. import models
from .devices import is_local_host

def evaluate_traffic(db: Session, traffic: models.Traffic) -> list[models.Alert]:
    created = []
    max_packet = int(os.getenv("ALERT_MAX_PACKET_BYTES", "1000000"))
    source_limit = int(os.getenv("ALERT_SOURCE_BYTES_PER_HOUR", "100000000"))
    if traffic.packet_size >= max_packet:
        created.extend(_add_if_open_missing(db, "large_packet", traffic.source_ip, f"Packet size {traffic.packet_size} bytes meets the configured threshold.", "high"))
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    recent_volume = db.scalar(select(func.coalesce(func.sum(models.Traffic.packet_size), 0)).where(models.Traffic.source_ip == traffic.source_ip, models.Traffic.timestamp >= since)) or 0
    if recent_volume >= source_limit:
        created.extend(_add_if_open_missing(db, "high_source_volume", traffic.source_ip, "Observed source traffic has reached the configured volume threshold.", "medium"))
    if is_local_host(traffic.source_ip) and db.scalar(select(models.Device.id).where(models.Device.ip_address == traffic.source_ip).limit(1)) is None:
        created.extend(_add_if_open_missing(db, "unknown_device", traffic.source_ip, "Traffic was received from an unregistered local device.", "low"))
    ports = {int(value.strip()) for value in os.getenv("ALERT_WATCH_PORTS", "").split(",") if value.strip().isdigit()}
    if traffic.destination_port in ports:
        created.extend(_add_if_open_missing(db, "watched_port", traffic.source_ip, f"Traffic targeted configured watched port {traffic.destination_port}.", "medium"))
    db.commit()
    for alert in created: db.refresh(alert)
    return created

def _add(db, kind, source_ip, description, severity):
    alert = models.Alert(type=kind, source_ip=source_ip, description=description, severity=severity, status="open")
    db.add(alert)
    return alert


def _add_if_open_missing(db: Session, kind: str, source_ip: str | None, description: str, severity: str) -> list[models.Alert]:
    """Create one alert for each persistent open condition and source."""
    existing = db.scalar(select(models.Alert.id).where(
        models.Alert.type == kind,
        models.Alert.source_ip == source_ip,
        models.Alert.status == "open",
    ).limit(1))
    return [] if existing is not None else [_add(db, kind, source_ip, description, severity)]
