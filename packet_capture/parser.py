"""Extract only network and transport metadata from captured packets."""
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


def parse_packet(packet) -> dict | None:
    """Convert a Scapy packet into the existing Traffic API payload.

    Raw payload bytes are never read, copied, logged, or included in the result.
    Unsupported, malformed, and non-IP packets return None.
    """
    try:
        from scapy.layers.inet import ICMP, IP, TCP, UDP
        from scapy.layers.inet6 import ICMPv6Unknown, IPv6

        ipv4 = packet.getlayer(IP)
        ipv6 = packet.getlayer(IPv6)
        network = ipv4 if ipv4 is not None else ipv6
        if network is None:
            return None

        tcp = packet.getlayer(TCP)
        udp = packet.getlayer(UDP)
        icmp = packet.getlayer(ICMP)
        icmpv6 = packet.getlayer(ICMPv6Unknown)
        source_port = destination_port = None
        if tcp is not None:
            protocol = "TCP"
            source_port, destination_port = int(tcp.sport), int(tcp.dport)
        elif udp is not None:
            protocol = "UDP"
            source_port, destination_port = int(udp.sport), int(udp.dport)
        elif icmp is not None:
            protocol = "ICMP"
        elif icmpv6 is not None or any(layer.__name__.startswith("ICMPv6") for layer in packet.layers()) or (ipv6 is not None and int(ipv6.nh) == 58):
            protocol = "ICMPv6"
        else:
            return None

        source_ip = str(network.src)
        destination_ip = str(network.dst)
        if not source_ip or not destination_ip:
            return None
        return {
            "source_ip": source_ip,
            "destination_ip": destination_ip,
            "protocol": protocol,
            "source_port": source_port,
            "destination_port": destination_port,
            "packet_size": int(len(packet)),
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        }
    except Exception as exc:
        logger.debug("Ignored malformed or unsupported packet (%s)", type(exc).__name__)
        return None
