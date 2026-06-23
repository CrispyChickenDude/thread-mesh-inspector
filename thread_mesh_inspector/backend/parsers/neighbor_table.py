"""Parser for: ot-ctl neighbor table."""
from __future__ import annotations
from backend.models.link import ThreadLink


def parse_neighbor_table(raw: str, self_extaddr: str = "", source_name: str = "") -> list[ThreadLink]:
    """
    Parse 'ot-ctl neighbor table' output into ThreadLink objects.

    Expected output format:

        | Role | RLOC16 | Age | Avg RSSI | Last RSSI |R|D|N| Extended MAC     |
        +------+--------+-----+----------+-----------+-+-+-+------------------+
        |   R  | 0x9800 |  45 |      -55 |       -52 |1|1|1| 6e50644a86a9b7a4 |
        |   C  | 0x3401 |   5 |      -72 |       -70 |0|0|1| 62e24d4b7e30e78c |

    Role: R=Router, C=Child/End Device

    Returns a list of ThreadLink (self → neighbor).

    Step 2: implement using real fixture from tests/fixtures/house_neighbor_table.txt
             and tests/fixtures/garage_neighbor_table.txt
    """
    # TODO (Step 2): implement with real fixture
    links = []
    lines = raw.strip().splitlines()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    for line in lines:
        line = line.strip()
        if not line.startswith("|") or "Role" in line or line.startswith("+"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 6:
            continue
        try:
            role_char = parts[0].strip().upper()
            rloc16_str = parts[1].strip()
            age = int(parts[2]) if parts[2].strip().lstrip("-").isdigit() else None
            avg_rssi_str = parts[3].strip()
            rssi = int(avg_rssi_str) if avg_rssi_str.lstrip("-").isdigit() else None
            extaddr = parts[-1].strip().lower()
            if len(extaddr) != 16:
                extaddr = None

            is_router = role_char == "R"

            links.append(ThreadLink(
                source_extaddr=self_extaddr or None,
                target_extaddr=extaddr,
                target_rloc16=rloc16_str,
                rssi=rssi,
                age_seconds=age,
                is_router_link=is_router,
                is_child_link=not is_router,
                source_otbr=source_name,
                observed_at=now,
            ))
        except (ValueError, IndexError):
            continue
    return links
