"""
Assembles a SourceSnapshot from the raw ot-ctl command results dict.
Called by LocalDockerOtbrSource and SshDockerOtbrSource after collection.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional

from .state import parse_state, state_to_role, parse_extaddr, parse_rloc16, parse_partitionid, parse_channel
from .child_table import parse_child_table
from .neighbor_table import parse_neighbor_table
from .router_table import parse_router_table
from .dataset import parse_dataset_active
from .netdata import parse_netdata
from .ipaddr import parse_ipaddr, parse_parent
from .counters import parse_counters_mac, parse_counters_mle
from .srp import parse_srp_server_host, parse_srp_server_service
from backend.models.node import ThreadNode, NodeRole
from backend.sources.base import SourceSnapshot

logger = logging.getLogger(__name__)


def build_snapshot_from_results(
    source_name: str,
    results: dict[str, str],
    snap: SourceSnapshot,
) -> SourceSnapshot:
    """
    Parse all ot-ctl results into a SourceSnapshot.

    `results` is a dict mapping command string → raw stdout.
    Populates snap in-place and returns it.
    """
    now = datetime.now(timezone.utc)
    snap.collected_at = now

    # ── Self identity ──────────────────────────────────────────────────────
    self_extaddr = parse_extaddr(results.get("extaddr", ""))
    self_rloc16 = parse_rloc16(results.get("rloc16", ""))
    self_state = parse_state(results.get("state", ""))
    self_role = state_to_role(self_state)
    partition_id = parse_partitionid(results.get("partitionid", ""))
    channel = parse_channel(results.get("channel", ""))

    snap.self_extaddr = self_extaddr
    snap.self_rloc16 = self_rloc16
    snap.self_role = self_state
    snap.partition_id = partition_id

    # Build self-node
    is_border_router = self_role in (NodeRole.LEADER, NodeRole.ROUTER)
    self_node = ThreadNode(
        extaddr=self_extaddr,
        rloc16=self_rloc16,
        role=self_role,
        is_border_router=is_border_router,
        partition_id=partition_id,
        source_names=[source_name],
        observed_at=now,
        last_seen=now,
    )

    # Addresses
    addr_data = parse_ipaddr(results.get("ipaddr", ""))
    self_node.rloc_address = addr_data.get("rloc_address")
    self_node.omr_addresses = addr_data.get("omr_addresses", [])
    self_node.link_local_address = addr_data.get("link_local_address")

    # Parent info (for children / end devices)
    parent_data = parse_parent(results.get("parent", ""))
    self_node.parent_extaddr = parent_data.get("parent_extaddr")
    self_node.parent_rloc16 = parent_data.get("parent_rloc16")
    if parent_data.get("lq_in"):
        self_node.lq_in = parent_data["lq_in"]

    # ── Topology tables ────────────────────────────────────────────────────
    children = parse_child_table(results.get("child table", ""), source_name)
    routers = parse_router_table(results.get("router table", ""), source_name)
    neighbors = parse_neighbor_table(results.get("neighbor table", ""), self_extaddr or "", source_name)

    # Set parent reference on children (they attach to this OTBR)
    for child in children:
        if not child.parent_extaddr and self_extaddr:
            child.parent_extaddr = self_extaddr
        child.observed_at = now
        child.last_seen = now

    # Update self-node with child extaddrs
    self_node.child_extaddrs = [c.extaddr for c in children if c.extaddr]

    # Collect all nodes
    all_nodes = [self_node] + children
    for r in routers:
        if r.extaddr != self_extaddr:  # skip self in router table
            r.observed_at = now
            r.last_seen = now
            all_nodes.append(r)

    snap.nodes = all_nodes
    snap.links = neighbors

    # ── Dataset ────────────────────────────────────────────────────────────
    snap.dataset = parse_dataset_active(results.get("dataset active", ""), source_name)
    if channel and snap.dataset:
        snap.dataset.channel = channel

    # ── SRP ────────────────────────────────────────────────────────────────
    srp_hosts = parse_srp_server_host(results.get("srp server host", ""))
    srp_services = parse_srp_server_service(results.get("srp server service", ""))

    # Annotate nodes with SRP hostnames
    host_map: dict[str, str] = {}  # IPv6 addr → hostname
    for host in srp_hosts:
        if not host.get("deleted", False):
            for addr in host.get("addresses", []):
                host_map[addr.lower()] = host["hostname"]

    for node in snap.nodes:
        for omr in node.omr_addresses:
            hostname = host_map.get(omr.lower())
            if hostname:
                node.srp_hostname = hostname
                node.srp_services = [
                    s["service_name"] for s in srp_services
                    if s.get("host", "").lower() == hostname.lower()
                ]
                break

    return snap
