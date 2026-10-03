"""Capture packets and forward metadata on a bounded worker queue."""
from __future__ import annotations

import logging
import queue
import threading

from .client import BackendClient
from .config import Settings
from .interfaces import NetworkInterface
from .parser import parse_packet

logger = logging.getLogger(__name__)


class TrafficCapture:
    def __init__(self, settings: Settings, interface: NetworkInterface, client: BackendClient | None = None):
        self.settings = settings
        self.interface = interface
        self.client = client or BackendClient(settings.backend_url, settings.request_timeout, settings.retry_count)
        self._queue: queue.Queue = queue.Queue(maxsize=settings.max_queue_size)
        self._stop = threading.Event()
        self._worker = threading.Thread(target=self._send_loop, name="traffic-api-worker", daemon=True)
        self._sniffer = None
        self._dropped = 0

    def _on_packet(self, packet) -> None:
        record = parse_packet(packet)
        if record is None:
            return
        logger.debug("Captured %s %s -> %s (%s bytes)", record["protocol"], record["source_ip"], record["destination_ip"], record["packet_size"])
        try:
            self._queue.put_nowait(record)
        except queue.Full:
            self._dropped += 1
            if self._dropped == 1 or self._dropped % 100 == 0:
                logger.warning("Traffic queue is full; dropped %s packet metadata records", self._dropped)

    def _send_loop(self) -> None:
        while not self._stop.is_set() or not self._queue.empty():
            try:
                record = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                if self.client.send_traffic(record):
                    logger.debug("Traffic record delivered to backend")
            except Exception:
                logger.exception("Unexpected error forwarding packet metadata; capture will continue")
            finally:
                self._queue.task_done()

    def run(self) -> None:
        try:
            from scapy.all import AsyncSniffer
        except ImportError as exc:
            raise RuntimeError("Scapy is required. Install dependencies with python -m pip install -r requirements.txt") from exc

        self._worker.start()
        try:
            self._sniffer = AsyncSniffer(iface=self.interface.name, prn=self._on_packet, store=False)
            self._sniffer.start()
            logger.info("Capture started on %s", self.interface.description)
            logger.info("Interface: %s (%s)", self.interface.name, self.interface.ip_address or "no IPv4 address")
            logger.info("Backend: %s", self.settings.backend_url)
            logger.info("Press Ctrl+C to stop capture")
            self._sniffer.join()
        except KeyboardInterrupt:
            logger.info("Stopping capture...")
        except Exception as exc:
            message = str(exc)
            if "permission" in message.lower() or "access is denied" in message.lower() or "winpcap" in message.lower():
                logger.error("Unable to start packet capture. Run with permission and install Npcap: %s", exc)
            else:
                logger.exception("Unable to run packet capture: %s", exc)
            raise RuntimeError(f"Packet capture failed: {exc}") from exc
        finally:
            if self._sniffer is not None and getattr(self._sniffer, "running", False):
                try:
                    self._sniffer.stop(join=True)
                except Exception:
                    logger.exception("Error while stopping packet capture")
            self._stop.set()
            if self._worker.is_alive():
                self._worker.join()
            self.client.close()
            logger.info("Capture stopped")
            if self._dropped:
                logger.warning("Total packet metadata records dropped because the queue filled: %s", self._dropped)
