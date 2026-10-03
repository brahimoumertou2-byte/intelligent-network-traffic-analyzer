"""Track observed local network hosts and calculate their current status."""
import os
from datetime import datetime, timedelta, timezone
from ipaddress import IPv4Address, ip_address, ip_network

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models


def is_local_host(address: str) -> bool:
    """Return true for RFC1918 IPv4 or unique-local IPv6 host addresses."""
    candidate = ip_address(address)
    if isinstance(candidate, IPv4Address):
        private_lan = (
            ip_network("10.0.0.0/8"),
            ip_network("172.16.0.0/12"),
            ip_network("192.168.0.0/16"),
        )
        return any(candidate in network for network in private_lan)
    return candidate in ip_network("fc00::/7") and not any((
        candidate.is_loopback, candidate.is_link_local, candidate.is_multicast,
        candidate.is_unspecified, candidate.is_reserved,
    ))


def active_device_cutoff() -> datetime:
    """Return the shared cutoff used by the device API and KPI."""
    window_seconds = int(os.getenv("DEVICE_ACTIVE_WINDOW_SECONDS", "300"))
    return datetime.now(timezone.utc) - timedelta(seconds=window_seconds)


def is_active_device(device: models.Device, cutoff: datetime | None = None) -> bool:
    """A device is online only when enabled and observed in the active window."""
    if device.status != "active" or device.last_seen is None:
        return False
    last_seen = device.last_seen
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    return last_seen >= (cutoff or active_device_cutoff())


def observe_local_devices(db: Session, traffic: models.Traffic) -> list[models.Device]:
    """Create or refresh devices only for observed private local addresses."""
    observed = []
    for address in {traffic.source_ip, traffic.destination_ip}:
        if not is_local_host(address):
            continue
        device = db.scalar(select(models.Device).where(models.Device.ip_address == address))
        if device is None:
            device = models.Device(ip_address=address, status="active", last_seen=traffic.timestamp)
            db.add(device)
        else:
            device.status = "active"
            device.last_seen = traffic.timestamp
        observed.append(device)
    return observed
