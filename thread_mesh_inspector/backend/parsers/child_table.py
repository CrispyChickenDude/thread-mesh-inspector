"""Parser for: ot-ctl child table."""
from __future__ import annotations
import re
from typing import Optional
from backend.models.node import ThreadNode, NodeRole


def parse_child_table(raw: str, source_name: str = "") -> list[ThreadNode]:
    """
    Parse 'ot-ctl child table' output into a list of ThreadNode objects.

    Expected output format (columns may vary by OpenThread version):

        | ID  | RLOC16 | Timeout    | Age        | LQ In | C_VN |R|D|N|Ver|CSL|QMsgCnt| Extended MAC     |
        +-----+--------+------------+------------+-------+------+-+-+-+---+---+-------+------------------+
        |   1 | 0x3401 |        240 |          5 |     3 |  225 |0|0|1|  4| 0 |     0 | 62e24d4b7e30e78c |
        |   5 | 0x3405 |        240 |         12 |     3 |  114 |0|1|0|  4| 0 |     0 | bea21efee32302ba |

    Column notes:
        ID      — child ID (relative to parent)
        RLOC16  — child's routing address
        Timeout — registration timeout in seconds
        Age     — seconds since last heard
        LQ In   — link quality from parent's perspective (1-3)
        R       — RxOnWhenIdle flag (0=sleepy, 1=always-on)
        D       — Full Thread Device flag
        N       — Full Network Data flag

    Returns a list of ThreadNode, one per child row.

    Step 2: implement using real fixture from tests/fixtures/house_child_table.txt
             and tests/fixtures/garage_child_table.txt
    """
    # TODO (Step 2): implement with real fixture
    # Header detection: skip lines starting with | ID or +---
    nodes = []
    lines = raw.strip().splitlines()
    for line in lines:
        line = line.strip()
        if not line.startswith("|") or "ID" in line or line.startswith("+"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 8:
            continue
        try:
            child_id = int(parts[0])
            rloc16_str = parts[1].strip()
            timeout = int(parts[2]) if parts[2].strip().isdigit() else None
            age = int(parts[3]) if parts[3].strip().isdigit() else None
            lq_in = int(parts[4]) if parts[4].strip().isdigit() else None
            # R flag: 0=sleepy, 1=always-on
            r_flag = parts[6].strip() if len(parts) > 6 else "1"
            # Extended MAC is the last column
            extaddr = parts[-1].strip().lower()
            if len(extaddr) != 16:
                extaddr = None

            role = NodeRole.SLEEPY_CHILD if r_flag == "0" else NodeRole.CHILD

            nodes.append(ThreadNode(
                extaddr=extaddr,
                rloc16=rloc16_str,
                role=role,
                lq_in=lq_in,
                age_seconds=age,
                timeout_seconds=timeout,
                source_names=[source_name],
            ))
        except (ValueError, IndexError):
            continue
    return nodes
