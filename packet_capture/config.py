"""Runtime configuration for packet capture."""
from dataclasses import dataclass
import logging
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    backend_url: str
    capture_interface: str | None
    request_timeout: float
    max_queue_size: int
    retry_count: int
    log_level: int


def load_settings() -> Settings:
    load_dotenv()
    try:
        timeout = float(os.getenv("REQUEST_TIMEOUT", "5"))
        queue_size = int(os.getenv("MAX_QUEUE_SIZE", "1000"))
        retries = int(os.getenv("RETRY_COUNT", "3"))
    except ValueError as exc:
        raise ValueError("REQUEST_TIMEOUT, MAX_QUEUE_SIZE and RETRY_COUNT must be numeric") from exc
    if timeout <= 0 or queue_size < 1 or retries < 0:
        raise ValueError("REQUEST_TIMEOUT and MAX_QUEUE_SIZE must be positive; RETRY_COUNT cannot be negative")
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, None)
    if not isinstance(level, int):
        raise ValueError("LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR or CRITICAL")
    backend_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").strip().rstrip("/")
    if not backend_url.startswith(("http://", "https://")):
        raise ValueError("BACKEND_URL must start with http:// or https://")
    interface = os.getenv("CAPTURE_INTERFACE", "").strip() or None
    return Settings(backend_url, interface, timeout, queue_size, retries, level)
