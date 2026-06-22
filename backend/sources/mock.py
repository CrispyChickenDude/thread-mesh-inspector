"""
Mock OTBR source — returns realistic fake data for development and demo.

⚠ MOCK MODE — no real Thread data.
This source is clearly labelled in the UI. Never used in production unless
mock_mode: true is explicitly set in the add-on options.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from .base import OtbrSource, OtbrSourceConfig, SourceSnapshot
from backend.models.node import ThreadNode, NodeRole, NameConfidence
from backend.models.link import ThreadLink
from backend.models.dataset import DatasetFingerprint

logger = logging.getLogger(__name__)

# Realistic mock data based on the real network topology.
# Uses the real extaddrs / rloc16s confirmed from live checks.
MOCK_NODES = [
    {
        "extaddr": "6e50644a86a9b7a4",   # house OTBR (confirmed live)
        "rloc16": "0x9800",
        "router_id": 38,
        "role": NodeRole.LEADER,
        "is_border_router": True,
        "friendly_name": "House OTBR",
        "name_confidence": NameConfidence.HIGH,
        "area": "Utility Room",
        "source": "House OTBR",
        "lq_in": 3,
        "rssi": -55,
    },
    {
        "extaddr": "4232f2a613d2a61a",   # garage OTBR (confirmed live)
        "rloc16": "0x3400",
        "router_id": 13,
        "role": NodeRole.ROUTER,
        "is_border_router": True,
        "friendly_name": "Garage OTBR",
        "name_confidence": NameConfidence.HIGH,
        "area": "Garage",
        "source": "Garage OTBR",
        "lq_in": 3,
        "rssi": -68,
        "parent_extaddr": "6e50644a86a9b7a4",
    },
    {
        "extaddr": "62e24d4b7e30e78c",
        "rloc16": "0x3401",
        "role": NodeRole.SLEEPY_CHILD,
        "friendly_name": "Environment - Garage [Ambient]",
        "name_confidence": NameConfidence.LOW,
        "area": "Garage",
        "source": "Garage OTBR",
        "lq_in": 3,
        "rssi": -72,
        "parent_extaddr": "4232f2a613d2a61a",
    },
    {
        "extaddr": "bea21efee32302ba",
        "rloc16": "0x3405",
        "role": NodeRole.CHILD,
        "friendly_name": "Remote - Garage [Lights]",
        "name_confidence": NameConfidence.LOW,
        "area": "Garage",
        "source": "Garage OTBR",
        "lq_in": 3,
        "rssi": -65,
        "parent_extaddr": "4232f2a613d2a61a",
    },
]

MOCK_DATASET = DatasetFingerprint(
    network_name="ha-thread-1c20",
    channel=15,
    pan_id="0x1c20",
    fingerprint_hash="abcd1234ef567890",  # synthetic — not a real hash
    source_name="Mock",
    observed_at=datetime.now(timezone.utc),
)


class MockOtbrSource(OtbrSource):
    """
    Returns realistic mock topology data. Used when mock_mode: true.
    Clearly labelled as mock in every snapshot and the UI.
    """

    MOCK_LABEL = "⚠ MOCK MODE — not real data"

    async def is_reachable(self) -> bool:
        return True

    async def collect(self) -> SourceSnapshot:
        now = datetime.now(timezone.utc)
        snap = SourceSnapshot(
            source_name=f"{self.name} [{self.MOCK_LABEL}]",
            collected_at=now,
        )

        nodes = []
        for n in MOCK_NODES:
            node = ThreadNode(
                extaddr=n["extaddr"],
                rloc16=n["rloc16"],
                router_id=n.get("router_id"),
                role=n["role"],
                is_border_router=n.get("is_border_router", False),
                friendly_name=n.get("friendly_name"),
                name_confidence=n.get("name_confidence", NameConfidence.LOW),
                area=n.get("area"),
                lq_in=n.get("lq_in"),
                rssi=n.get("rssi"),
                parent_extaddr=n.get("parent_extaddr"),
                source_names=[n.get("source", self.name)],
                observed_at=now,
                last_seen=now,
                first_seen=now - timedelta(days=3),
            )
            node.display_name  # ensure property is accessible
            nodes.append(node)

        # Build mock links
        links = []
        garage_otbr = next(n for n in nodes if n.rloc16 == "0x3400")
        house_otbr = next(n for n in nodes if n.rloc16 == "0x9800")

        links.append(ThreadLink(
            source_extaddr=garage_otbr.extaddr,
            target_extaddr=house_otbr.extaddr,
            lq_in=3, rssi=-68, is_router_link=True,
            source_otbr=self.name, observed_at=now,
        ))
        for node in nodes:
            if node.parent_extaddr:
                links.append(ThreadLink(
                    source_extaddr=node.extaddr,
                    target_extaddr=node.parent_extaddr,
                    lq_in=node.lq_in,
                    rssi=node.rssi,
                    is_child_link=True,
                    source_otbr=self.name,
                    observed_at=now,
                ))

        snap.nodes = nodes
        snap.links = links
        snap.dataset = MOCK_DATASET
        snap.self_extaddr = nodes[0].extaddr
        snap.errors = [self.MOCK_LABEL]
        return snap
