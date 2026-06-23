"""Parser for: ot-ctl netdata show."""
from __future__ import annotations
import re
from typing import Optional


def parse_netdata(raw: str) -> dict:
    """
    Parse 'ot-ctl netdata show' output.

    Extracts:
    - OMR prefixes and their border router RLOC16
    - Border router entries
    - Service entries (e.g. SRP server, DNS-SD)

    Expected format (varies by OpenThread version):

        Prefixes:
        fd13:810b:b3b3:1::/64 paos low 9800

        Routes:

        Services:
        44970 5d fd13:810b:b3b3:1::1 9800

    Returns a dict with keys: omr_prefixes, border_routers, services.

    Step 2: implement using real fixture from tests/fixtures/house_netdata.txt
    """
    # TODO (Step 2): implement with real fixture
    result = {
        "omr_prefixes": [],
        "border_routers": [],
        "services": [],
        "raw": raw,
    }

    in_prefixes = False
    in_routes = False
    in_services = False

    for line in raw.strip().splitlines():
        stripped = line.strip()
        if stripped.lower() == "prefixes:":
            in_prefixes, in_routes, in_services = True, False, False
            continue
        if stripped.lower() == "routes:":
            in_prefixes, in_routes, in_services = False, True, False
            continue
        if stripped.lower() == "services:":
            in_prefixes, in_routes, in_services = False, False, True
            continue
        if stripped and in_prefixes:
            result["omr_prefixes"].append(stripped)
        elif stripped and in_routes:
            result["border_routers"].append(stripped)
        elif stripped and in_services:
            result["services"].append(stripped)

    return result
