"""Interactive entry point: python -m packet_capture."""
import logging
import sys

from .capture import TrafficCapture
from .config import load_settings
from .interfaces import select_interface


def main() -> int:
    try:
        settings = load_settings()
        logging.basicConfig(level=settings.log_level, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        logger = logging.getLogger("packet_capture")
        logger.info("Intelligent Network Traffic Analyzer — packet capture")
        interface = select_interface(settings.capture_interface)
        TrafficCapture(settings, interface).run()
        return 0
    except (ValueError, RuntimeError, KeyboardInterrupt) as exc:
        logging.getLogger("packet_capture").error("%s", exc)
        return 1
    except EOFError:
        logging.getLogger("packet_capture").error("No interface selection was provided")
        return 1


if __name__ == "__main__":
    sys.exit(main())
