from datetime import datetime

import pytest
pytest.importorskip("scapy", reason="Install project dependencies to run Scapy packet parser tests")
from scapy.all import ICMP, IP, Raw, TCP, UDP
from scapy.layers.inet6 import IPv6, ICMPv6EchoRequest

from packet_capture.parser import parse_packet


def test_parse_tcp_metadata_without_payload():
    packet = IP(src="192.168.1.10", dst="192.168.1.1") / TCP(sport=52341, dport=443) / Raw(load=b"private payload")
    record = parse_packet(packet)
    assert record["source_ip"] == "192.168.1.10"
    assert record["destination_ip"] == "192.168.1.1"
    assert record["protocol"] == "TCP"
    assert record["source_port"] == 52341
    assert record["destination_port"] == 443
    assert record["packet_size"] == len(packet)
    assert "private payload" not in str(record)
    datetime.fromisoformat(record["timestamp"])


def test_parse_udp():
    record = parse_packet(IP(src="10.0.0.1", dst="10.0.0.2") / UDP(sport=5353, dport=53))
    assert (record["protocol"], record["source_port"], record["destination_port"]) == ("UDP", 5353, 53)


def test_parse_icmp_has_null_ports():
    record = parse_packet(IP(src="10.0.0.1", dst="10.0.0.2") / ICMP())
    assert record["protocol"] == "ICMP"
    assert record["source_port"] is None and record["destination_port"] is None


def test_parse_icmpv6():
    record = parse_packet(IPv6(src="2001:db8::1", dst="2001:db8::2") / ICMPv6EchoRequest())
    assert record["protocol"] == "ICMPv6"


@pytest.mark.parametrize("packet", [Raw(load=b"not IP"), IP(proto=47, src="10.0.0.1", dst="10.0.0.2")])
def test_ignores_unsupported_packets(packet):
    assert parse_packet(packet) is None
