"""Parser for: ot-ctl ipaddr and ot-ctl parent."""
from __future__ import annotations
import re
from typing import Optional


OMR_PREFIX = "fd"  # OMR addresses start with fd (ULA)


def parse_ipaddr(raw: str) -> dict:
    """
    Parse 'ot-ctl ipaddr' output.

    Expected output:
        fdbd:413a:40c0:4204:0:ff:fe00:3400   <- RLOC address
        fd13:810b:b3b3:1:4232:f2a6:13d2:a61a <- OMR address
        fe80::4032:f2a6:13d2:a61a             <- link-local

    Returns dict with keys: rloc_address, omr_addresses, link_local_address, all_addresses.

    Step 2: implement using real fixture.
    """
    # TODO (Step 2): implement with real fixture
    result = {
        "rloc_address": None,
        "omr_addresses": [],
        "link_local_address": None,
        "all_addresses": [],
    }

    for line in raw.strip().splitlines():
        addr = line.strip()
        if not addr:
            continue
        result["all_addresses"].append(addr)
        if addr.lower().startswith("fe80"):
            result["link_local_address"] = addr
        elif addr.lower().startswith("fdbd") or ":ff:fe00:" in addr.lower():
            # RLOC addresses contain :ff:fe00:RLOC16
            result["rloc_address"] = addr
        elif addr.lower().startswith(OMR_PREFIX):
            result["omr_addresses"].append(addr)

    return result


def parse_parent(raw: str) -> dict:
    """
    Parse 'ot-ctl parent' output.

    Expected output:
        Ext Addr: 6e50644a86a9b7a4
        Rloc: 0x9800
        Link Quality In: 3
        Link Quality Out: 3
        Age: 12

    Returns dict with parent identity fields.

    Step 2: implement using real fixture.
    """
    # TODO (Step 2): implement with real fixture
    result = {
        "parent_extaddr": None,
        "parent_rloc16": None,
        "lq_in": None,
        "lq_out": None,
        "age_seconds": None,
    }

    patterns = {
        "parent_extaddr": re.compile(r"Ext Addr:\s*([0-9a-fA-F]+)", re.IGNORECASE),
        "parent_rloc16": re.compile(r"Rloc:\s*(0x[0-9a-fA-F]+|\d+)", re.IGNORECASE),
        "lq_in": re.compile(r"Link Quality In:\s*(\d+)", re.IGNORECASE),
        "lq_out": re.compile(r"Link Quality Out:\s*(\d+)", re.IGNORECASE),
        "age_seconds": re.compile(r"Age:\s*(\d+)", re.IGNORECASE),
    }

    for field, pattern in patterns.items():
        m = pattern.search(raw)
        if m:
            val = m.group(1).strip().lower()
            if field in ("lq_in", "lq_out", "age_seconds"):
                try:
                    result[field] = int(val)
                except ValueError:
                    pass
            else:
                result[field] = val

    return result
