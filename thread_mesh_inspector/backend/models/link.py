"""Thread link/edge data model."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class LinkQuality(str, Enum):
    """Human-readable link quality classification."""
    GOOD = "good"           # LQ 3, RSSI >= -70
    MARGINAL = "marginal"   # LQ 2, RSSI -70 to -85
    WEAK = "weak"           # LQ <= 1 or RSSI < -85
    UNKNOWN = "unknown"


@dataclass
class ThreadLink:
    """
    A directed link between two Thread nodes.

    source_extaddr → target_extaddr represents a neighbour/child relationship.
    For child-to-parent links: source = child, target = parent.
    For router-to-router links: source = lower RLOC16, target = higher (bidirectional).
    """
    source_extaddr: Optional[str] = None
    source_rloc16: Optional[str] = None
    target_extaddr: Optional[str] = None
    target_rloc16: Optional[str] = None

    # Metrics
    rssi: Optional[int] = None           # dBm
    lq_in: Optional[int] = None          # 0-3 (received by target from source)
    lq_out: Optional[int] = None         # 0-3 (sent by source, received by target)
    link_margin: Optional[int] = None
    path_cost: Optional[int] = None
    age_seconds: Optional[int] = None

    # Relationship type
    is_child_link: bool = False          # child → parent
    is_router_link: bool = False         # router ↔ router

    # Source / freshness
    source_otbr: Optional[str] = None
    observed_at: Optional[datetime] = None
    is_stale: bool = False

    @property
    def quality(self) -> LinkQuality:
        """Classify link quality from available metrics."""
        if self.lq_in is not None:
            if self.lq_in >= 3:
                return LinkQuality.GOOD
            if self.lq_in == 2:
                return LinkQuality.MARGINAL
            return LinkQuality.WEAK
        if self.rssi is not None:
            if self.rssi >= -70:
                return LinkQuality.GOOD
            if self.rssi >= -85:
                return LinkQuality.MARGINAL
            return LinkQuality.WEAK
        return LinkQuality.UNKNOWN

    @property
    def quality_label(self) -> str:
        """Plain-English quality label for the UI."""
        labels = {
            LinkQuality.GOOD: "Good",
            LinkQuality.MARGINAL: "Marginal",
            LinkQuality.WEAK: "Weak — may affect updates",
            LinkQuality.UNKNOWN: "Unknown",
        }
        return labels[self.quality]

    @property
    def is_weak(self) -> bool:
        return self.quality == LinkQuality.WEAK

    @property
    def is_marginal(self) -> bool:
        return self.quality == LinkQuality.MARGINAL
