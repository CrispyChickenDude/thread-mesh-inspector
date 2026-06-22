"""Mesh event model — records topology changes over time."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class EventKind(str, Enum):
    """Type of mesh event."""
    NODE_JOINED = "node_joined"
    NODE_LEFT = "node_left"
    NODE_PARENT_CHANGED = "node_parent_changed"
    NODE_ROLE_CHANGED = "node_role_changed"
    NODE_RLOC_CHANGED = "node_rloc_changed"
    LINK_QUALITY_CHANGED = "link_quality_changed"
    OTBR_ONLINE = "otbr_online"
    OTBR_OFFLINE = "otbr_offline"
    OTBR_STATE_CHANGED = "otbr_state_changed"
    DATASET_MISMATCH = "dataset_mismatch"
    DATASET_MATCH_RESTORED = "dataset_match_restored"
    PAIRING_WATCH_STARTED = "pairing_watch_started"
    PAIRING_WATCH_STOPPED = "pairing_watch_stopped"
    COLLECTION_ERROR = "collection_error"


@dataclass
class MeshEvent:
    """A single recorded mesh event."""
    kind: EventKind
    timestamp: datetime
    source_name: Optional[str] = None       # which OTBR source detected this
    node_extaddr: Optional[str] = None      # node this event relates to
    node_display_name: Optional[str] = None
    description: str = ""                   # plain-English description
    detail: Optional[dict] = None           # structured extra data (old/new values etc)
    severity: str = "info"                  # info | warning | error

    @property
    def is_pairing_related(self) -> bool:
        return self.kind in (EventKind.NODE_JOINED, EventKind.NODE_LEFT,
                             EventKind.PAIRING_WATCH_STARTED, EventKind.PAIRING_WATCH_STOPPED)
