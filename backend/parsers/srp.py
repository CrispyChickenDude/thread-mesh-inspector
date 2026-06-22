"""Parser for: ot-ctl srp server host / srp server service."""
from __future__ import annotations
import re
from typing import Optional


def parse_srp_server_host(raw: str) -> list[dict]:
    """
    Parse 'ot-ctl srp server host' output.

    Expected output (abbreviated):
        hostname1.local.
            deleted: false
            addresses: [fd13:810b:b3b3:1::1]
        hostname2.local.
            deleted: true

    Returns a list of dicts with keys: hostname, addresses, deleted.

    Step 2: implement using real fixture.
    """
    # TODO (Step 2): implement with real fixture
    hosts = []
    current = None
    for line in raw.strip().splitlines():
        stripped = line.strip()
        if stripped.endswith(".local.") or (stripped and not stripped.startswith(("deleted", "addresses", "ttl"))):
            if current:
                hosts.append(current)
            current = {"hostname": stripped, "addresses": [], "deleted": False}
        elif current and stripped.startswith("deleted:"):
            current["deleted"] = "true" in stripped.lower()
        elif current and stripped.startswith("addresses:"):
            addr_match = re.findall(r"[0-9a-fA-F:]+:[0-9a-fA-F:]+", stripped)
            current["addresses"].extend(addr_match)
    if current:
        hosts.append(current)
    return hosts


def parse_srp_server_service(raw: str) -> list[dict]:
    """
    Parse 'ot-ctl srp server service' output.

    Returns a list of dicts with keys: service_name, instance_name, port, host.

    Step 2: implement using real fixture.
    """
    # TODO (Step 2): implement with real fixture
    services = []
    current = None
    for line in raw.strip().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith(("deleted", "port", "host", "txt", "priority")):
            if current:
                services.append(current)
            current = {"service_name": stripped, "port": None, "host": None}
        elif current and stripped.startswith("port:"):
            try:
                current["port"] = int(stripped.split(":")[1].strip())
            except (ValueError, IndexError):
                pass
        elif current and stripped.startswith("host:"):
            current["host"] = stripped.split(":", 1)[1].strip()
    if current:
        services.append(current)
    return services
