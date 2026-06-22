"""REST OTBR source — queries the OTBR REST API."""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional

from .base import OtbrSource, OtbrSourceConfig, SourceSnapshot
from backend.models.node import ThreadNode, NodeRole
from backend.models.dataset import DatasetFingerprint

logger = logging.getLogger(__name__)

# REST provides identity + dataset only (no child/neighbor/router tables).
# Used as a fallback for OTBRs where docker exec and SSH are unavailable.
REST_LIMITATION_NOTE = (
    "REST source provides identity and dataset fingerprint only. "
    "Child, neighbor, and router tables require docker exec or SSH access."
)


class RestOtbrSource(OtbrSource):
    """
    Collects Thread identity and dataset from the OTBR REST API.

    Endpoints used (all read-only):
        GET /node          — full node info (state, extaddr, rloc16, networkName, leaderData)
        GET /node/state
        GET /node/ext-address
        GET /node/rloc16
        GET /node/network-name
        GET /node/leader-data
        GET /node/dataset/active  — for fingerprint only; raw hex NOT stored
        GET /node/coprocessor/version

    Note: /diagnostics (POST) and child/neighbor/router table endpoints
    are not available in the bnutzer/otbr-tcp image used for the garage OTBR.
    """

    def __init__(self, config: OtbrSourceConfig):
        super().__init__(config)
        try:
            import httpx
            self._client = httpx.AsyncClient(base_url=config.base_url, timeout=6.0)
        except ImportError:
            raise RuntimeError("httpx is required for RestOtbrSource. Add it to requirements.txt.")

    async def _get(self, path: str) -> Optional[object]:
        try:
            import httpx
            r = await self._client.get(path)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.debug("[%s] REST GET %s failed: %s", self.name, path, e)
            return None

    async def is_reachable(self) -> bool:
        result = await self._get("/node/state")
        return result is not None

    async def collect(self) -> SourceSnapshot:
        snap = SourceSnapshot(source_name=self.name, collected_at=datetime.now(timezone.utc))
        try:
            node_data = await self._get("/node")
            if node_data is None:
                return self._make_error_snapshot(
                    f"REST API at {self.config.base_url} is not reachable."
                )

            # Parse identity from /node response
            self_node = ThreadNode(
                extaddr=node_data.get("extAddress"),
                rloc16=hex(node_data.get("rloc16", 0)) if node_data.get("rloc16") else None,
                router_id=node_data.get("routerId"),
                source_names=[self.name],
                observed_at=snap.collected_at,
            )
            # Map state to role
            state = node_data.get("state", "").lower()
            role_map = {
                "leader": NodeRole.LEADER,
                "router": NodeRole.ROUTER,
                "child": NodeRole.CHILD,
                "detached": NodeRole.UNKNOWN,
                "disabled": NodeRole.UNKNOWN,
            }
            self_node.role = role_map.get(state, NodeRole.UNKNOWN)
            snap.self_extaddr = self_node.extaddr
            snap.self_rloc16 = self_node.rloc16
            snap.self_role = state
            snap.nodes = [self_node]

            # Dataset fingerprint — hash only, raw hex discarded
            dataset_raw = await self._get("/node/dataset/active")
            if isinstance(dataset_raw, str) and dataset_raw:
                snap.dataset = DatasetFingerprint.from_raw_hex(
                    dataset_raw,
                    source_name=self.name,
                    network_name=node_data.get("networkName"),
                )

            snap.errors.append(REST_LIMITATION_NOTE)
            snap.is_partial = True  # REST always partial — no topology tables
            self._last_snapshot = snap
            self._clear_failure_count()
        except Exception as exc:
            snap = self._make_error_snapshot(str(exc))
        return snap
