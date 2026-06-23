"""Parser for: ot-ctl state / extaddr / rloc16 / partitionid / version / channel."""
from __future__ import annotations
from typing import Optional
from backend.models.node import NodeRole


def parse_state(raw: str) -> Optional[str]:
    """
    Parse 'ot-ctl state' output.

    Expected output examples:
        leader
        router
        child
        detached
        disabled

    Returns the state string (lowercase), or None if unparseable.

    Step 2: implement using real fixture from tests/fixtures/house_state.txt
    """
    # TODO (Step 2): implement with real fixture
    line = raw.strip().lower()
    if line in ("leader", "router", "child", "reed", "detached", "disabled"):
        return line
    return None


def state_to_role(state: Optional[str]) -> NodeRole:
    """Convert an ot-ctl state string to a NodeRole enum value."""
    mapping = {
        "leader": NodeRole.LEADER,
        "router": NodeRole.ROUTER,
        "child": NodeRole.CHILD,
        "reed": NodeRole.REED,
        "detached": NodeRole.UNKNOWN,
        "disabled": NodeRole.UNKNOWN,
    }
    return mapping.get(state or "", NodeRole.UNKNOWN)


def parse_extaddr(raw: str) -> Optional[str]:
    """
    Parse 'ot-ctl extaddr' output.

    Expected output example:
        6e50644a86a9b7a4

    Returns lowercase hex string, or None.

    Step 2: implement using real fixture.
    """
    value = raw.strip().lower()
    if len(value) == 16 and all(c in "0123456789abcdef" for c in value):
        return value
    return None


def parse_rloc16(raw: str) -> Optional[str]:
    """
    Parse 'ot-ctl rloc16' output.

    Expected output example:
        0x9800   (or just: 38912)

    Returns hex string like '0x9800'.

    Step 2: implement using real fixture.
    """
    raw = raw.strip()
    try:
        if raw.startswith("0x") or raw.startswith("0X"):
            return hex(int(raw, 16))
        return hex(int(raw))
    except ValueError:
        return None


def parse_partitionid(raw: str) -> Optional[int]:
    """
    Parse 'ot-ctl partitionid' output.

    Expected output example:
        1812778284

    Step 2: implement using real fixture.
    """
    try:
        return int(raw.strip())
    except ValueError:
        return None


def parse_channel(raw: str) -> Optional[int]:
    """
    Parse 'ot-ctl channel' output.

    Expected output example:
        15

    Step 2: implement using real fixture.
    """
    try:
        return int(raw.strip())
    except ValueError:
        return None
