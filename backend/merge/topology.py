"""Merge snapshots from multiple OTBR sources into a unified topology."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

from backend.models.node import ThreadNode, NodeRole
from backend.models.link import ThreadLink
from backend.models.dataset import DatasetFingerprint
from backend.models.diagnostic import DiagnosticFinding, Severity
from backend.sources.base import SourceSnapshot

logger = logging.getLogger(__name__)

STALE_THRESHOLD_MULTIPLIER = 3  # node is stale after this many poll intervals


@dataclass
class DatasetMatchResult:
    """Dataset comparison across all OTBRs."""
    sources_checked: list[str] = field(default_factory=list)
    fingerprints: dict[str, Optional[str]] = field(default_factory=dict)  # name → hash
    all_match: Optional[bool] = None  # None if any fingerprint is unknown
    mismatch_sources: list[str] = field(default_factory=list)
    checked_at: Optional[datetime] = None

    @property
    def summary(self) -> str:
        if self.all_match is None:
            return "Dataset comparison incomplete — some OTBRs did not respond."
        if self.all_match:
            return "✓ All OTBRs are on the same Thread dataset. Do not re-key Thread."
        sources = " and ".join(self.mismatch_sources)
        return f"⚠ Dataset mismatch detected between {sources}. Devices may not roam."


@dataclass
class MergedTopology:
    """Unified Thread topology merged from all OTBR sources."""
    nodes: list[ThreadNode] = field(default_factory=list)
    links: list[ThreadLink] = field(default_factory=list)
    dataset_match: Optional[DatasetMatchResult] = None
    source_snapshots: list[SourceSnapshot] = field(default_factory=list)
    findings: list[DiagnosticFinding] = field(default_factory=list)
    merged_at: Optional[datetime] = None
    is_mock: bool = False

    @property
    def router_count(self) -> int:
        return sum(1 for n in self.nodes if n.is_router)

    @property
    def child_count(self) -> int:
        return sum(1 for n in self.nodes if not n.is_router)

    @property
    def sleepy_count(self) -> int:
        return sum(1 for n in self.nodes if n.is_sleepy)

    @property
    def weak_link_count(self) -> int:
        return sum(1 for l in self.links if l.is_weak)

    @property
    def stale_node_count(self) -> int:
        return sum(1 for n in self.nodes if n.is_stale)

    @property
    def otbr_sources(self) -> list[SourceSnapshot]:
        return self.source_snapshots

    def node_by_extaddr(self, extaddr: str) -> Optional[ThreadNode]:
        return next((n for n in self.nodes if n.extaddr == extaddr), None)


class TopologyMerger:
    """Merges SourceSnapshots from multiple OTBRs into a single MergedTopology."""

    def __init__(self, poll_interval_seconds: int = 60):
        self.poll_interval = poll_interval_seconds
        self._stale_after = timedelta(seconds=poll_interval_seconds * STALE_THRESHOLD_MULTIPLIER)

    def merge(self, snapshots: list[SourceSnapshot]) -> MergedTopology:
        """Merge all snapshots into a unified topology."""
        now = datetime.now(timezone.utc)
        merged = MergedTopology(merged_at=now, source_snapshots=snapshots)

        # Check mock mode
        merged.is_mock = any(
            "MOCK" in snap.source_name.upper() for snap in snapshots
        )

        # Merge nodes — de-duplicate by extaddr (prefer higher-confidence entry)
        node_map: dict[str, ThreadNode] = {}
        for snap in snapshots:
            for node in snap.nodes:
                key = node.extaddr or node.rloc16 or id(node)
                if key not in node_map:
                    node_map[str(key)] = node
                else:
                    # Merge: update missing fields from additional sources
                    existing = node_map[str(key)]
                    for src in node.source_names:
                        if src not in existing.source_names:
                            existing.source_names.append(src)
                    # Keep the more-detailed version (more fields set)
                    if node.friendly_name and not existing.friendly_name:
                        existing.friendly_name = node.friendly_name
                    if node.lq_in is not None and existing.lq_in is None:
                        existing.lq_in = node.lq_in
                    if node.rssi is not None and existing.rssi is None:
                        existing.rssi = node.rssi

        # Mark stale nodes
        for node in node_map.values():
            if node.observed_at and (now - node.observed_at) > self._stale_after:
                node.is_stale = True

        merged.nodes = list(node_map.values())

        # Merge links — de-duplicate by (source, target) pair
        link_map: dict[tuple, ThreadLink] = {}
        for snap in snapshots:
            for link in snap.links:
                key = (link.source_extaddr, link.target_extaddr)
                if key not in link_map:
                    link_map[key] = link

        merged.links = list(link_map.values())

        # Dataset comparison
        merged.dataset_match = self._compare_datasets(snapshots, now)

        # Generate diagnostic findings
        merged.findings = self._generate_findings(merged)

        return merged

    def _compare_datasets(self, snapshots: list[SourceSnapshot], now: datetime) -> DatasetMatchResult:
        result = DatasetMatchResult(checked_at=now)
        for snap in snapshots:
            result.sources_checked.append(snap.source_name)
            if snap.dataset:
                result.fingerprints[snap.source_name] = snap.dataset.fingerprint_hash
            else:
                result.fingerprints[snap.source_name] = None

        hashes = [h for h in result.fingerprints.values() if h is not None]
        if len(hashes) < 2:
            result.all_match = None
            return result

        first = hashes[0]
        result.all_match = all(h == first for h in hashes)
        if not result.all_match:
            result.mismatch_sources = [
                name for name, h in result.fingerprints.items()
                if h != first and h is not None
            ]
        return result

    def _generate_findings(self, topo: MergedTopology) -> list[DiagnosticFinding]:
        findings = []

        # Dataset mismatch
        if topo.dataset_match and topo.dataset_match.all_match is False:
            findings.append(DiagnosticFinding(
                severity=Severity.ERROR,
                title="Dataset mismatch detected",
                description=(
                    "Your OTBRs are on different Thread datasets. "
                    "Devices paired through one OTBR cannot roam to the other. "
                    "Do NOT run 'dataset set active' or re-key Thread without fully "
                    "understanding the impact on all paired devices."
                ),
                suggested_action=(
                    "Verify which dataset is correct. Check each OTBR's 'dataset active' "
                    "output (channel, network name, PAN ID) and resolve the mismatch. "
                    "Contact support before re-keying."
                ),
            ))

        # Weak links
        for link in topo.links:
            if link.is_weak:
                source_node = topo.node_by_extaddr(link.source_extaddr or "")
                target_node = topo.node_by_extaddr(link.target_extaddr or "")
                src_name = source_node.display_name if source_node else link.source_extaddr or "Unknown"
                tgt_name = target_node.display_name if target_node else link.target_extaddr or "Unknown"
                lq_detail = f"LQ {link.lq_in}" if link.lq_in is not None else ""
                rssi_detail = f"RSSI {link.rssi} dBm" if link.rssi is not None else ""
                metrics = " / ".join(filter(None, [lq_detail, rssi_detail]))
                findings.append(DiagnosticFinding(
                    severity=Severity.WARNING,
                    title=f"Weak link: {src_name} → {tgt_name}",
                    description=(
                        f"The link from {src_name} to {tgt_name} is weak ({metrics}). "
                        f"OTA firmware updates may be unreliable on this path. "
                        f"The device may drop off the mesh or fail to receive commands."
                    ),
                    suggested_action=(
                        "Try moving the device or a router closer to improve signal. "
                        "Check for interference on the Thread channel."
                    ),
                    node_extaddr=link.source_extaddr,
                    link_source=link.source_extaddr,
                    link_target=link.target_extaddr,
                    raw_values={"lq_in": link.lq_in, "rssi": link.rssi},
                ))

        # Sleepy device note (informational — not a problem)
        for node in topo.nodes:
            if node.is_sleepy:
                findings.append(DiagnosticFinding(
                    severity=Severity.INFO,
                    title=f"{node.display_name} is a sleepy device",
                    description=(
                        f"{node.display_name} is a sleepy end device (MED/ICD). "
                        f"It wakes on a schedule and may not respond to pings. "
                        f"Lack of ping response is normal — do not interpret as offline."
                    ),
                    node_extaddr=node.extaddr,
                ))

        # Stale nodes
        for node in topo.nodes:
            if node.is_stale and not node.is_sleepy:
                findings.append(DiagnosticFinding(
                    severity=Severity.WARNING,
                    title=f"{node.display_name} — data is stale",
                    description=(
                        f"{node.display_name} has not been seen for longer than expected. "
                        f"It may have left the mesh, lost power, or have a connectivity issue."
                    ),
                    node_extaddr=node.extaddr,
                ))

        return findings
