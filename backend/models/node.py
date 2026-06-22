"""Thread node data model."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class NodeRole(str, Enum):
    """Role of a Thread node in the mesh."""
    LEADER = "leader"
    BORDER_ROUTER = "border_router"
    ROUTER = "router"
    REED = "reed"              # Router-Eligible End Device
    CHILD = "child"
    SLEEPY_CHILD = "sleepy_child"   # MED / ICD
    UNKNOWN = "unknown"


class NameConfidence(str, Enum):
    """Confidence level of a node's friendly name."""
    HIGH = "high"           # Matched by stable extaddr via HA registry
    MEDIUM = "medium"       # Matched via SRP / IPv6 / service data
    LOW = "low"             # Manually aliased by extaddr, or RLOC16-only (extaddr unknown)
    TEMPORARY = "temporary" # RLOC16-only — RLOC can change; never trust as stable


@dataclass
class ThreadNode:
    """
    A single Thread node, merged from one or more OTBR sources.

    Identity fields (stable, preferred):
        extaddr — 64-bit extended MAC address; stable across reboots
        rloc16  — 16-bit routing address; can change on re-attach

    Source tracking:
        source_names — which OTBRs reported this node
        observed_at  — when this node was last seen
        is_stale     — True if data is older than the configured poll interval * 3

    Naming:
        friendly_name     — best available name (HA registry → alias → fallback hex)
        name_confidence   — how reliable the name is
        ha_device_id      — HA device registry ID if matched
        ha_device_url     — link to the HA device page
        area              — room/area from HA or alias config
    """

    # ── Identity ─────────────────────────────────────────────────────────────
    extaddr: Optional[str] = None        # "4232f2a613d2a61a" (hex, lowercase)
    rloc16: Optional[str] = None         # "0x3400"
    router_id: Optional[int] = None      # numeric router ID
    partition_id: Optional[int] = None

    # ── Role ─────────────────────────────────────────────────────────────────
    role: NodeRole = NodeRole.UNKNOWN
    is_border_router: bool = False
    thread_version: Optional[str] = None

    # ── Addresses ────────────────────────────────────────────────────────────
    rloc_address: Optional[str] = None   # full RLOC IPv6 address
    omr_addresses: list[str] = field(default_factory=list)
    link_local_address: Optional[str] = None

    # ── Topology ─────────────────────────────────────────────────────────────
    parent_extaddr: Optional[str] = None
    parent_rloc16: Optional[str] = None
    child_extaddrs: list[str] = field(default_factory=list)

    # ── Link metrics ─────────────────────────────────────────────────────────
    rssi: Optional[int] = None           # dBm to parent
    lq_in: Optional[int] = None          # 0-3 to parent
    lq_out: Optional[int] = None
    path_cost: Optional[int] = None
    link_margin: Optional[int] = None

    # ── Timing ───────────────────────────────────────────────────────────────
    age_seconds: Optional[int] = None    # seconds since last heard
    timeout_seconds: Optional[int] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    is_stale: bool = False

    # ── Source tracking ───────────────────────────────────────────────────────
    source_names: list[str] = field(default_factory=list)
    observed_at: Optional[datetime] = None

    # ── Naming ───────────────────────────────────────────────────────────────
    friendly_name: Optional[str] = None
    name_confidence: NameConfidence = NameConfidence.TEMPORARY
    ha_device_id: Optional[str] = None
    ha_device_url: Optional[str] = None
    ha_entity_ids: list[str] = field(default_factory=list)
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    area: Optional[str] = None

    # ── SRP / services ────────────────────────────────────────────────────────
    srp_hostname: Optional[str] = None
    srp_services: list[str] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        """Best available display name — friendly or hex fallback."""
        if self.friendly_name:
            return self.friendly_name
        if self.extaddr:
            return f"…{self.extaddr[-6:]}"
        if self.rloc16:
            return f"RLOC {self.rloc16}"
        return "Unknown node"

    @property
    def is_sleepy(self) -> bool:
        return self.role == NodeRole.SLEEPY_CHILD

    @property
    def is_router(self) -> bool:
        return self.role in (NodeRole.LEADER, NodeRole.ROUTER, NodeRole.BORDER_ROUTER)
