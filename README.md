<<<<<<< HEAD
# Intelligent Network Traffic Analyzer

A defensive network monitoring application with a FastAPI backend, live dashboard, and a separate packet capture component. The analyzer captures packet metadata and submits normalized records to the existing traffic API; it does not retain packet payloads.

## Architecture

FastAPI routers expose traffic, statistics, alerts, and device resources. SQLAlchemy 2 persists records in SQLite by default and supports PostgreSQL through `DATABASE_URL`. Pydantic validates API inputs. Services compute database-backed metrics and configurable monitoring alerts. The static dashboard reads live API data.

```text
backend/       API, persistence, schemas, routers, services
dashboard/     Static HTML, CSS, JavaScript dashboard
packet_capture/ Scapy interface discovery, metadata parsing, capture, API client
tests/         API integration tests using isolated in-memory SQLite
```

## Install and run

Requires Python 3.12 or later.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn backend.main:app --reload
```

The database initializes automatically. The default SQLite file is `traffic_analyzer.db` in the working directory. Open interactive API docs at <http://127.0.0.1:8000/docs> and health status at `/api/health`.

## Environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./traffic_analyzer.db` | SQLAlchemy database connection |
| `CORS_ORIGINS` | localhost origins | Comma separated dashboard origins |
| `ALERT_MAX_PACKET_BYTES` | `1000000` | Large packet alert threshold |
| `ALERT_SOURCE_BYTES_PER_HOUR` | `100000000` | Source volume alert threshold |
| `ALERT_WATCH_PORTS` | empty | Comma separated destination ports to flag |
| `DEVICE_ACTIVE_WINDOW_SECONDS` | `300` | Time after last local observation for a device to count as active |

For PostgreSQL, install a compatible SQLAlchemy driver such as `psycopg` and set a PostgreSQL `DATABASE_URL`.

## Dashboard

Start the API, then serve the dashboard directory from the workspace root:

```powershell
python -m http.server 8080
```

Visit <http://127.0.0.1:8080/dashboard/>. Set `window.API_BASE` before `app.js` if the API uses a different address. Chart.js is loaded from its CDN.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST/GET | `/api/traffic` | Ingest and list traffic (pagination and IP/protocol filters) |
| GET/DELETE | `/api/traffic/{traffic_id}` | Read or delete traffic |
| GET | `/api/statistics/overview` | Totals and active devices |
| GET | `/api/statistics/protocols` | Protocol counts |
| GET | `/api/statistics/top-ips` | Top source and destination IPs |
| GET | `/api/statistics/top-ports` | Destination port counts |
| GET | `/api/statistics/timeline` | Hourly packet counts |
| GET/POST | `/api/alerts` | List/create alerts |
| PATCH/DELETE | `/api/alerts/{alert_id}` | Update/delete alert |
| GET/POST | `/api/devices` | List/register devices |
| GET/PATCH/DELETE | `/api/devices/{device_id}` | Read/update/delete device |

Send analyzed packet metadata to the ingestion endpoint:

```json
{
  "source_ip": "192.168.1.10",
  "destination_ip": "192.168.1.1",
  "protocol": "TCP",
  "source_port": 52341,
  "destination_port": 443,
  "packet_size": 850,
  "timestamp": "2026-10-03T12:00:00Z"
}
```

The packet analyzer developer can `POST` this JSON to `http://127.0.0.1:8000/api/traffic`. The API validates addresses, ports and sizes, stores the record, then evaluates monitoring rules. Register known devices through `POST /api/devices` to distinguish unknown sources.

## Packet capture on Windows

Install Python dependencies (Scapy is included in `requirements.txt`) and install the Npcap packet capture driver on Windows. Use an account with permission to capture on the selected adapter; elevated PowerShell may be required by the driver and system policy. Capture only on networks and interfaces you are authorized to monitor.

Start the backend first, then run the analyzer from the project root:

```powershell
python -m packet_capture
```

It lists Scapy-discovered interfaces and prompts for a selection. To select an interface without the prompt, set `CAPTURE_INTERFACE` in `.env` to its displayed name or description. Configure the backend using `BACKEND_URL` (default `http://127.0.0.1:8000`). Other analyzer settings are `REQUEST_TIMEOUT` (seconds), `MAX_QUEUE_SIZE` (bounded pending metadata records), `RETRY_COUNT` (finite retries for timeouts and transient server errors), and `LOG_LEVEL`. Press Ctrl+C to stop; queued records are drained before shutdown. If capture fails with permission or adapter errors, check Npcap installation, adapter availability, interface spelling, and permissions.

The analyzer forwards only IP/TCP/UDP/ICMP metadata as JSON to the existing `POST /api/traffic` endpoint. It does not read or persist packet payloads. A captured TCP packet is normalized to `source_ip`, `destination_ip`, `protocol`, `source_port`, `destination_port`, `packet_size`, and a UTC ISO 8601 `timestamp`; ICMP records use null ports. Successful ingestion flows through the existing database, statistics, alerts, and dashboard.

Local private hosts observed in traffic are added to the devices table and their `last_seen` value is refreshed. Active device totals include only hosts seen within `DEVICE_ACTIVE_WINDOW_SECONDS`. An unknown-device alert is created only for an unregistered local source, and one open alert is retained per source and condition; public Internet sources do not produce unknown-device alerts.

## Tests

Install dependencies with `python -m pip install -r requirements.txt`, then run `python -m pytest`. Backend tests use isolated in-memory SQLite; analyzer tests use constructed Scapy packets and mocked HTTP requests, so they do not capture live network traffic.
=======
# intelligent-network-traffic-analyzer
>>>>>>> a402cc9d9ae6fbbebd769bdf18639da8af52bc56
