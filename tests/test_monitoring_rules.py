from datetime import datetime, timedelta, timezone

from tests.test_traffic import client


def traffic(source: str, destination: str = "192.168.1.152", **overrides):
    payload = {
        "source_ip": source,
        "destination_ip": destination,
        "protocol": "TCP",
        "source_port": 52000,
        "destination_port": 443,
        "packet_size": 850,
    }
    payload.update(overrides)
    return payload


def open_unknown_alerts(client):
    return [alert for alert in client.get("/api/alerts?status=open").json() if alert["type"] == "unknown_device"]


def test_unknown_local_device_creates_one_open_alert_and_device(client):
    response = client.post("/api/traffic", json=traffic("192.168.1.50"))
    assert response.status_code == 201
    assert [alert["source_ip"] for alert in open_unknown_alerts(client)] == ["192.168.1.50"]
    devices = client.get("/api/devices").json()
    assert {device["ip_address"] for device in devices} == {"192.168.1.50", "192.168.1.152"}


def test_repeated_local_traffic_does_not_flood_unknown_alerts(client):
    for _ in range(5):
        assert client.post("/api/traffic", json=traffic("192.168.1.50")).status_code == 201
    assert len(open_unknown_alerts(client)) == 1
    assert client.get("/api/statistics/overview").json()["total_packets"] == 5


def test_public_remote_source_never_creates_unknown_device_or_device(client):
    assert client.post("/api/traffic", json=traffic("104.18.32.47")).status_code == 201
    assert open_unknown_alerts(client) == []
    assert {device["ip_address"] for device in client.get("/api/devices").json()} == {"192.168.1.152"}


def test_known_local_device_does_not_generate_unknown_alert(client):
    assert client.post("/api/devices", json={"ip_address": "192.168.1.50"}).status_code == 201
    assert client.post("/api/traffic", json=traffic("192.168.1.50")).status_code == 201
    assert open_unknown_alerts(client) == []


def test_device_last_seen_is_refreshed(client):
    first = "2026-10-03T12:00:00Z"
    second = "2026-10-03T12:05:00Z"
    client.post("/api/traffic", json=traffic("192.168.1.50", timestamp=first))
    client.post("/api/traffic", json=traffic("192.168.1.50", timestamp=second))
    device = next(row for row in client.get("/api/devices").json() if row["ip_address"] == "192.168.1.50")
    assert device["last_seen"].startswith("2026-10-03T12:05:00")


def test_overview_counts_recent_active_devices_and_open_alerts(client):
    now = datetime.now(timezone.utc).isoformat()
    client.post("/api/traffic", json=traffic("192.168.1.50", timestamp=now))
    overview = client.get("/api/statistics/overview").json()
    assert overview["active_devices"] == 2
    assert overview["total_alerts"] == 1
    alert_id = open_unknown_alerts(client)[0]["id"]
    assert client.patch(f"/api/alerts/{alert_id}", json={"status": "acknowledged"}).status_code == 200
    assert client.get("/api/statistics/overview").json()["total_alerts"] == 0


def test_statistics_use_real_records_and_destination_ports(client):
    client.post("/api/traffic", json=traffic("192.168.1.50", packet_size=100, destination_port=443))
    client.post("/api/traffic", json=traffic("192.168.1.51", packet_size=200, destination_port=443))
    client.post("/api/traffic", json=traffic("192.168.1.50", packet_size=300, destination_port=53, source_port=9999))
    overview = client.get("/api/statistics/overview").json()
    assert overview["total_packets"] == 3
    assert overview["traffic_volume"] == 600
    assert client.get("/api/statistics/top-ports").json()[0] == {"port": 443, "count": 2}
    ips = client.get("/api/statistics/top-ips").json()
    assert ips["sources"][0] == {"ip": "192.168.1.50", "count": 2, "direction": "source"}


def test_identical_valid_traffic_records_are_preserved(client):
    payload = traffic("192.168.1.50", timestamp="2026-10-03T12:00:00.123Z")
    assert client.post("/api/traffic", json=payload).status_code == 201
    assert client.post("/api/traffic", json=payload).status_code == 201
    assert len(client.get("/api/traffic").json()) == 2
