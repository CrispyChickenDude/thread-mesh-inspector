"""Parser for: ot-ctl router table."""
from __future__ import annotations
from backend.models.node import ThreadNode, NodeRole


def parse_router_table(raw: str, source_name: str = "") -> list[ThreadNode]:
    """
    Parse 'ot-ctl router table' output into ThreadNode objects.

    Expected output format:

        | ID | RLOC16 | Next Hop | Path Cost | LQ In | LQ Out | Age | Extended MAC     | Link |
        +----+--------+----------+-----------+-------+--------+-----+------------------+------+
        | 13 | 0x3400 |       13 |         0 |     0 |      0 |   0 | 4232f2a613d2a61a |    1 |
        | 38 | 0x9800 |       63 |        11 |     3 |      3 |   6 | 6e50644a86a9b7a4 |    0 |

    Step 2: implement using real fixture from tests/fixtures/house_router_table.txt
             and tests/fixtures/garage_router_table.txt
    """
    # TODO (Step 2): implement with real fixture
    nodes = []
    lines = raw.strip().splitlines()
    for line in lines:
        line = line.strip()
        if not line.startswith("|") or "ID" in line or line.startswith("+"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 7:
            continue
        try:
            router_id = int(parts[0])
            rloc16_str = parts[1].strip()
            path_cost = int(parts[3]) if parts[3].strip().isdigit() else None
            lq_in = int(parts[4]) if parts[4].strip().isdigit() else None
            lq_out = int(parts[5]) if parts[5].strip().isdigit() else None
            age = int(parts[6]) if parts[6].strip().isdigit() else None
            extaddr = parts[7].strip().lower() if len(parts) > 7 else None
            if extaddr and len(extaddr) != 16:
                extaddr = None

            nodes.append(ThreadNode(
                extaddr=extaddr,
                rloc16=rloc16_str,
                router_id=router_id,
                role=NodeRole.ROUTER,
                lq_in=lq_in,
                lq_out=lq_out,
                path_cost=path_cost,
                age_seconds=age,
                source_names=[source_name],
            ))
        except (ValueError, IndexError):
            continue
    return nodes
