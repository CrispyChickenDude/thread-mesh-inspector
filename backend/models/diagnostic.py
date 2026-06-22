"""Diagnostic finding model — plain-English issues with suggested actions."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class DiagnosticFinding:
    """
    A single diagnostic finding — a problem or observation, explained in plain English.
    Never just shows raw values; always provides human meaning and suggested action.
    """
    severity: Severity
    title: str                          # Short label, e.g. "Weak link to parent"
    description: str                    # Plain-English explanation
    suggested_action: Optional[str] = None
    node_extaddr: Optional[str] = None  # Node this finding relates to (if node-specific)
    link_source: Optional[str] = None   # Link source extaddr (if link-specific)
    link_target: Optional[str] = None
    raw_values: dict = field(default_factory=dict)  # Hidden in UI by default

    # Examples of findings the engine should produce:
    #
    # "Weak link to parent"
    #   "This device has LQ 1 to its parent. OTA updates may fail or be very slow.
    #    Try moving the device closer to a router, or add a router between them."
    #
    # "Sleepy device — offline is normal"
    #   "This device is a sleepy end device (MED/ICD). It may not respond to pings.
    #    Treat lack of ping response as normal, not as offline."
    #
    # "Dataset mismatch detected"
    #   "The House OTBR and Garage OTBR have different active datasets.
    #    This will prevent devices from roaming between them.
    #    Do NOT re-key Thread without understanding the impact."
    #
    # "No route to border router"
    #   "This device has no visible path to any border router. It may be isolated.
    #    Check parent link quality and whether its parent can reach the border router."
