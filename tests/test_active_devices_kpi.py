from datetime import datetime, timedelta, timezone

from tests.test_traffic import client


def add_device(client, ip_address, last_seen, status="active"):
    response = client.post("/api/devices", json={
        "ip_address": ip_address,
        "status": status,
        "last_seen": last_seen.isoformat(),
    })
    assert response.status_code == 201
    return response.json()


def test_kpi_and_devices_api_share_active_window_definition(client, monkeypatch):
    monkeypatch.setenv("DEVICE_ACTIVE_WINDOW_SECONDS", "300")
    now = datetime.now(timezone.utc)
    online = [add_device(client, f"192.168.1.{number}", now) for number in range(10, 14)]
    add_device(client, "192.168.1.14", now - timedelta(seconds=301))

    devices = client.get("/api/devices").json()
    assert sum(device["status"] == "active" for device in devices) == 4
    assert sum(device["status"] == "inactive" for device in devices) == 1
    assert client.get("/api/statistics/overview").json()["active_devices"] == 4

    client.patch(f"/api/devices/{online[0]['id']}", json={"status": "inactive"})
    assert client.get("/api/statistics/overview").json()["active_devices"] == 3

    add_device(client, "192.168.1.15", now)
    assert client.get("/api/statistics/overview").json()["active_devices"] == 4


def test_no_recent_devices_means_zero_active_devices(client, monkeypatch):
    monkeypatch.setenv("DEVICE_ACTIVE_WINDOW_SECONDS", "300")
    add_device(client, "192.168.1.20", datetime.now(timezone.utc) - timedelta(minutes=10))
    assert client.get("/api/devices").json()[0]["status"] == "inactive"
    assert client.get("/api/statistics/overview").json()["active_devices"] == 0
