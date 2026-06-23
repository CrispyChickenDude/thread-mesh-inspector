"""Manual alias resolver — maps extaddr/rloc16/IPv6 to friendly names."""
from __future__ import annotations
import logging
import re
from dataclasses import dataclass
from typing import Optional

from backend.models.node import ThreadNode, NameConfidence

logger = logging.getLogger(__name__)


@dataclass
class NodeAlias:
    """A manually configured alias for a Thread node."""
    key: str            # extaddr (hex) | rloc16 (0x...) | IPv6 address
    key_type: str       # "extaddr" | "rloc16" | "ipv6"
    name: str
    area: Optional[str] = None
    note: Optional[str] = None

    @property
    def confidence(self) -> NameConfidence:
        if self.key_type == "extaddr":
            # extaddr is stable — treat manual extaddr aliases as LOW
            # (not HIGH because they weren't verified via HA registry)
            return NameConfidence.LOW
        if self.key_type == "rloc16":
            return NameConfidence.TEMPORARY  # RLOC can change
        return NameConfidence.LOW  # IPv6 is fairly stable but not as reliable as extaddr


class AliasResolver:
    """
    Applies manual node_aliases config to ThreadNode objects.

    Alias resolution happens AFTER HA registry mapping. It overrides the name
    for any node where the HA registry did not produce a HIGH-confidence match.
    Manual extaddr aliases take precedence over automatic SRP/IPv6 matches.

    Config format (from /data/config.yaml):
        node_aliases:
          "62e24d4b7e30e78c":
            name: "Environment - Garage [Ambient]"
            area: "Garage"
    """

    def __init__(self, raw_config: dict):
        """
        raw_config: the node_aliases section from /data/config.yaml.
        """
        self._aliases: list[NodeAlias] = []
        self._load(raw_config)

    def _load(self, raw_config: dict) -> None:
        """Parse alias config into NodeAlias objects."""
        if not raw_config:
            return
        for key, value in raw_config.items():
            if not isinstance(value, dict) or "name" not in value:
                logger.warning("Invalid alias entry for key '%s' — expected {name: ...}", key)
                continue
            key_type = self._detect_key_type(key)
            if key_type is None:
                logger.warning("Unrecognised alias key format: '%s' — skipping", key)
                continue
            self._aliases.append(NodeAlias(
                key=key.strip().lower(),
                key_type=key_type,
                name=value["name"],
                area=value.get("area"),
                note=value.get("note"),
            ))
        logger.info("Loaded %d manual node alias(es)", len(self._aliases))

    def _detect_key_type(self, key: str) -> Optional[str]:
        """Determine whether a key is an extaddr, rloc16, or IPv6 address."""
        k = key.strip()
        if re.fullmatch(r"[0-9a-fA-F]{16}", k):
            return "extaddr"
        if re.fullmatch(r"0x[0-9a-fA-F]{4}", k, re.IGNORECASE):
            return "rloc16"
        if ":" in k and len(k) > 10:
            return "ipv6"
        return None

    def apply(self, nodes: list[ThreadNode]) -> None:
        """
        Apply aliases to a list of ThreadNode objects in-place.
        Does not overwrite HIGH-confidence names (from HA registry with extaddr match).
        """
        if not self._aliases:
            return

        # Build per-type lookup sets
        extaddr_aliases = {a.key: a for a in self._aliases if a.key_type == "extaddr"}
        rloc16_aliases = {a.key: a for a in self._aliases if a.key_type == "rloc16"}
        ipv6_aliases = {a.key: a for a in self._aliases if a.key_type == "ipv6"}

        for node in nodes:
            if node.name_confidence == NameConfidence.HIGH:
                continue  # Don't override HA registry high-confidence matches

            alias: Optional[NodeAlias] = None

            # Extaddr match (most stable)
            if node.extaddr and node.extaddr.lower() in extaddr_aliases:
                alias = extaddr_aliases[node.extaddr.lower()]

            # RLOC16 match (temporary — warn the user via confidence badge)
            elif node.rloc16 and node.rloc16.lower() in rloc16_aliases:
                alias = rloc16_aliases[node.rloc16.lower()]

            # IPv6 / OMR address match
            elif any(addr.lower() in ipv6_aliases for addr in node.omr_addresses):
                for addr in node.omr_addresses:
                    if addr.lower() in ipv6_aliases:
                        alias = ipv6_aliases[addr.lower()]
                        break

            if alias:
                node.friendly_name = alias.name
                node.name_confidence = alias.confidence
                if alias.area and not node.area:
                    node.area = alias.area

    @property
    def alias_count(self) -> int:
        return len(self._aliases)
