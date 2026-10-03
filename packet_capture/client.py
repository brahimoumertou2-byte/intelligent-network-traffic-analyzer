"""HTTP client for the existing FastAPI traffic endpoint."""
import logging
import time

import httpx

logger = logging.getLogger(__name__)


class BackendClient:
    def __init__(self, base_url: str, timeout: float = 5, retry_count: int = 3, client: httpx.Client | None = None):
        self.endpoint = f"{base_url.rstrip('/')}/api/traffic"
        self.retry_count = retry_count
        self._client = client or httpx.Client(timeout=timeout)
        self._owns_client = client is None

    def send_traffic(self, record: dict) -> bool:
        for attempt in range(self.retry_count + 1):
            try:
                response = self._client.post(self.endpoint, json=record)
                if response.status_code == 429 or response.status_code >= 500:
                    response.raise_for_status()
                if response.is_error:
                    logger.error("Backend rejected traffic (HTTP %s): %s", response.status_code, response.text[:300])
                    return False
                try:
                    result = response.json()
                except ValueError:
                    logger.error("Backend returned an invalid JSON response")
                    return False
                if not isinstance(result, dict) or not isinstance(result.get("id"), int):
                    logger.error("Backend returned an unexpected traffic response")
                    return False
                return True
            except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError, httpx.HTTPStatusError) as exc:
                if attempt >= self.retry_count:
                    logger.warning("Backend unavailable; packet was not delivered after %s attempts: %s", attempt + 1, exc)
                    return False
                delay = min(0.25 * (2 ** attempt), 2.0)
                logger.warning("Backend request failed; retrying in %.2f seconds (%s/%s)", delay, attempt + 1, self.retry_count)
                time.sleep(delay)
            except httpx.HTTPError as exc:
                logger.error("Backend request failed: %s", exc)
                return False
        return False

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
