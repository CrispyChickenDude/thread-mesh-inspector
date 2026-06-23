"""Home Assistant device/entity registry mapper for friendly names."""
from __future__ import annotations
import logging
import os
from typing import Optional

from backend.models.node import ThreadNode, NameConfidence

logger = logging.getLogger(__name__)

HA_API_BASE = "http://supervisor/core/api"


class HaRegistryMapper:
    """
    Queries the HA device and entity registries to map Thread nodes to friendly names.

    Uses the Supervisor token (auto-provided, never a user-managed long-lived token).

    Mapping strategy:
    1. Search entity registry for Thread/Matter entities; match by extaddr/OMR addr
    2. Fall back to SRP hostname → device name
    3. Fall back to manual alias (done by AliasResolver, not here)

    Note: HA does not always expose Thread extended MACs for Matter devices.
    When it does, confidence = HIGH. When matched via SRP/IPv6, confidence = MEDIUM.
    """

    def __init__(self):
        self._token = os.environ.get("TMI_SUPERVISOR_TOKEN", "")
        self._device_cache: Optional[list[dict]] = None
        self._entity_cache: Optional[list[dict]] = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def _fetch_devices(self) -> list[dict]:
        """Fetch all HA devices from the registry."""
        if self._device_cache is not None:
            return self._device_cache
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{HA_API_BASE}/config/device_registry/list",
                                     headers=self._headers(), timeout=8.0)
                if r.status_code == 200:
                    self._device_cache = r.json()
                    return self._device_cache
                logger.warning("HA device registry returned HTTP %d", r.status_code)
        except Exception as e:
            logger.warning("Could not reach HA device registry: %s", e)
        return []

    async def _fetch_entities(self) -> list[dict]:
        """Fetch all HA entities from the registry."""
        if self._entity_cache is not None:
            return self._entity_cache
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{HA_API_BASE}/config/entity_registry/list",
                                     headers=self._headers(), timeout=8.0)
                if r.status_code == 200:
                    self._entity_cache = r.json()
                    return self._entity_cache
        except Exception as e:
            logger.warning("Could not reach HA entity registry: %s", e)
        return []

    async def enrich_nodes(self, nodes: list[ThreadNode]) -> None:
        """
        Enrich a list of ThreadNode objects with HA friendly names in-place.
        Nodes already having a HIGH-confidence name are skipped.
        """
        if not self._token:
            logger.debug("No Supervisor token — skipping HA registry mapping")
            return

        devices = await self._fetch_devices()
        if not devices:
            return

        # Build lookup maps
        # HA Thread/Matter devices may have 'connections': [['mac', 'XX:XX:...'], ...]
        # or identifiers referencing the Thread MAC
        extaddr_to_device: dict[str, dict] = {}
        for device in devices:
            for conn_type, conn_value in device.get("connections", []):
                if conn_type in ("mac", "thread"):
                    # Normalise: strip colons, lowercase
                    clean = conn_value.replace(":", "").lower()
                    if len(clean) == 16:
                        extaddr_to_device[clean] = device

        for node in nodes:
            if node.name_confidence == NameConfidence.HIGH:
                continue

            ha_device = None
            matched_confidence = NameConfidence.MEDIUM

            # Try extaddr match (high confidence)
            if node.extaddr and node.extaddr in extaddr_to_device:
                ha_device = extaddr_to_device[node.extaddr]
                matched_confidence = NameConfidence.HIGH

            # Try SRP hostname match (medium confidence)
            if ha_device is None and node.srp_hostname:
                hostname_base = node.srp_hostname.rstrip(".").lower()
                for device in devices:
                    dev_name = (device.get("name") or "").lower().replace(" ", "-")
                    if hostname_base.startswith(dev_name) or dev_name in hostname_base:
                        ha_device = device
                        matched_confidence = NameConfidence.MEDIUM
                        break

            if ha_device:
                node.friendly_name = ha_device.get("name_by_user") or ha_device.get("name")
                node.name_confidence = matched_confidence
                node.ha_device_id = ha_device.get("id")
                node.manufacturer = ha_device.get("manufacturer")
                node.model = ha_device.get("model")
                node.area = node.area or ha_device.get("area_id")
                if ha_device.get("id"):
                    node.ha_device_url = f"/config/devices/device/{ha_device['id']}"

    def clear_cache(self) -> None:
        """Clear cached registry data (call after HA restart or config change)."""
        self._device_cache = None
        self._entity_cache = None
