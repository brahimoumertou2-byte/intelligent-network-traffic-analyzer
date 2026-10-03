"""Discover and select capture interfaces through Scapy."""
from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkInterface:
    name: str
    description: str
    ip_address: str
    status: str = "available"


def list_interfaces() -> list[NetworkInterface]:
    try:
        from scapy.all import conf
        discovered = []
        for iface in conf.ifaces.values():
            name = str(getattr(iface, "name", "") or "").strip()
            if not name:
                continue
            description = str(getattr(iface, "description", "") or name)
            ip_address = str(getattr(iface, "ip", "") or "")
            discovered.append(NetworkInterface(name, description, ip_address))
        return discovered
    except ImportError as exc:
        raise RuntimeError("Scapy is not installed. Run: python -m pip install -r requirements.txt") from exc
    except Exception as exc:
        raise RuntimeError(f"Unable to query network interfaces: {exc}") from exc


def select_interface(configured_name: str | None = None) -> NetworkInterface:
    interfaces = list_interfaces()
    if not interfaces:
        raise RuntimeError("No capture interfaces were found. Check the capture driver installation.")
    print("Available network interfaces:")
    for index, iface in enumerate(interfaces, start=1):
        print(f"  {index}. {iface.description} | name={iface.name} | IP={iface.ip_address or 'unassigned'} | {iface.status}")
    if configured_name:
        for iface in interfaces:
            if configured_name.casefold() in {iface.name.casefold(), iface.description.casefold()}:
                return iface
        raise ValueError(f"Configured capture interface was not found: {configured_name}")
    while True:
        choice = input("Select interface number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(interfaces):
            return interfaces[int(choice) - 1]
        print("Enter a number from the displayed list.")
