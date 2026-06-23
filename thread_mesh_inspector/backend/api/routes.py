"""FastAPI routes — JSON endpoints and SSE for the frontend SPA."""
from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from backend.merge.topology import MergedTopology

logger = logging.getLogger(__name__)


def create_router(get_topology, get_history) -> APIRouter:
    """
    Create the API router.

    get_topology: callable() -> MergedTopology
    get_history:  callable() -> HistoryDb
    """
    router = APIRouter(prefix="/api/v1")

    def _topology_to_dict(topo: MergedTopology) -> dict:
        """Serialise a MergedTopology to a JSON-safe dict."""
        return {
            "merged_at": topo.merged_at.isoformat() if topo.merged_at else None,
            "is_mock": topo.is_mock,
            "router_count": topo.router_count,
            "child_count": topo.child_count,
            "sleepy_count": topo.sleepy_count,
            "weak_link_count": topo.weak_link_count,
            "stale_node_count": topo.stale_node_count,
            "dataset_match": {
                "all_match": topo.dataset_match.all_match if topo.dataset_match else None,
                "summary": topo.dataset_match.summary if topo.dataset_match else "Unknown",
                "fingerprints": topo.dataset_match.fingerprints if topo.dataset_match else {},
            } if topo.dataset_match else None,
            "nodes": [_node_to_dict(n) for n in topo.nodes],
            "links": [_link_to_dict(l) for l in topo.links],
            "findings": [_finding_to_dict(f) for f in topo.findings],
            "sources": [_source_to_dict(s) for s in topo.source_snapshots],
        }

    def _node_to_dict(n) -> dict:
        return {
            "extaddr": n.extaddr,
            "rloc16": n.rloc16,
            "router_id": n.router_id,
            "role": n.role.value if n.role else "unknown",
            "is_border_router": n.is_border_router,
            "display_name": n.display_name,
            "friendly_name": n.friendly_name,
            "name_confidence": n.name_confidence.value if n.name_confidence else "temporary",
            "area": n.area,
            "manufacturer": n.manufacturer,
            "model": n.model,
            "ha_device_id": n.ha_device_id,
            "ha_device_url": n.ha_device_url,
            "parent_extaddr": n.parent_extaddr,
            "child_extaddrs": n.child_extaddrs,
            "omr_addresses": n.omr_addresses,
            "srp_hostname": n.srp_hostname,
            "rssi": n.rssi,
            "lq_in": n.lq_in,
            "lq_out": n.lq_out,
            "path_cost": n.path_cost,
            "age_seconds": n.age_seconds,
            "timeout_seconds": n.timeout_seconds,
            "is_stale": n.is_stale,
            "is_sleepy": n.is_sleepy,
            "source_names": n.source_names,
            "last_seen": n.last_seen.isoformat() if n.last_seen else None,
            "first_seen": n.first_seen.isoformat() if n.first_seen else None,
        }

    def _link_to_dict(l) -> dict:
        return {
            "source_extaddr": l.source_extaddr,
            "target_extaddr": l.target_extaddr,
            "source_rloc16": l.source_rloc16,
            "target_rloc16": l.target_rloc16,
            "rssi": l.rssi,
            "lq_in": l.lq_in,
            "lq_out": l.lq_out,
            "path_cost": l.path_cost,
            "age_seconds": l.age_seconds,
            "quality": l.quality.value,
            "quality_label": l.quality_label,
            "is_weak": l.is_weak,
            "is_marginal": l.is_marginal,
            "is_child_link": l.is_child_link,
            "is_router_link": l.is_router_link,
            "source_otbr": l.source_otbr,
            "is_stale": l.is_stale,
        }

    def _finding_to_dict(f) -> dict:
        return {
            "severity": f.severity.value,
            "title": f.title,
            "description": f.description,
            "suggested_action": f.suggested_action,
            "node_extaddr": f.node_extaddr,
        }

    def _source_to_dict(s) -> dict:
        return {
            "source_name": s.source_name,
            "collected_at": s.collected_at.isoformat() if s.collected_at else None,
            "is_healthy": s.is_healthy,
            "is_partial": s.is_partial,
            "errors": s.errors,
            "node_count": len(s.nodes),
        }

    @router.get("/topology")
    async def get_topology_endpoint():
        """Full topology snapshot — used by Overview and Topology views."""
        topo = get_topology()
        return _topology_to_dict(topo)

    @router.get("/topology/nodes/{extaddr}")
    async def get_node_detail(extaddr: str):
        """Detail for a single node."""
        topo = get_topology()
        node = topo.node_by_extaddr(extaddr)
        if not node:
            from fastapi import HTTPException
            raise HTTPException(404, f"Node {extaddr} not found")
        return _node_to_dict(node)

    @router.get("/health")
    async def health():
        """Quick health check — used by the Overview status card."""
        topo = get_topology()
        return {
            "status": "ok",
            "mock": topo.is_mock,
            "sources": len(topo.source_snapshots),
            "nodes": len(topo.nodes),
            "weak_links": topo.weak_link_count,
        }

    @router.get("/history/events")
    async def get_events(limit: int = 100, node_extaddr: Optional[str] = None):
        """Recent mesh events for the History view."""
        db = get_history()
        return await db.get_recent_events(limit=limit, node_extaddr=node_extaddr)

    @router.get("/history/metrics/{extaddr}")
    async def get_metrics(extaddr: str, limit: int = 500):
        """Node RSSI/LQ metric history for trend charts."""
        db = get_history()
        return await db.get_node_metrics(node_extaddr=extaddr, limit=limit)

    @router.get("/events/stream")
    async def event_stream(request: Request):
        """
        Server-Sent Events stream for Pairing Watch and live updates.
        Streams topology change events as they occur.
        """
        async def generator() -> AsyncGenerator[str, None]:
            yield f"data: {json.dumps({'type': 'connected', 'ts': datetime.now(timezone.utc).isoformat()})}\n\n"
            # Step 4: implement real event streaming via a shared event queue
            # For now, send a heartbeat every 5 seconds
            while not await request.is_disconnected():
                await asyncio.sleep(5)
                topo = get_topology()
                yield f"data: {json.dumps({'type': 'heartbeat', 'nodes': len(topo.nodes), 'ts': datetime.now(timezone.utc).isoformat()})}\n\n"

        return StreamingResponse(generator(), media_type="text/event-stream")

    return router
