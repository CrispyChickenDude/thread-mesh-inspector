"""
Parser for: ot-ctl dataset active (human-readable form only).

⚠ SECURITY: This parser MUST strip Network Key, PSKc, and raw hex before
returning. The raw dataset hex (from 'dataset active -x') is NEVER used here.
"""
from __future__ import annotations
import re
from typing import Optional
from backend.models.dataset import DatasetFingerprint


# Fields that contain Thread credentials — must be stripped / never stored
SECRET_FIELD_PATTERNS = [
    r"Network Key:\s*\S+",
    r"PSKc:\s*\S+",
    r"Security Policy:.*",     # may contain key flags
]

SAFE_FIELD_RE = {
    "network_name": re.compile(r"Network Name:\s*(.+)", re.IGNORECASE),
    "channel": re.compile(r"Channel:\s*(\d+)", re.IGNORECASE),
    # Use ^\s*PAN ID (multiline) so "Ext PAN ID" lines are not matched
    "pan_id": re.compile(r"^\s*PAN ID:\s*(0x[0-9a-fA-F]+|\d+)", re.IGNORECASE | re.MULTILINE),
    "ext_pan_id": re.compile(r"Extended PAN ID:\s*([0-9a-fA-F]+)", re.IGNORECASE),
    "mesh_local_prefix": re.compile(r"Mesh Local Prefix:\s*(\S+)", re.IGNORECASE),
}


def parse_dataset_active(raw: str, source_name: str = "") -> DatasetFingerprint:
    """
    Parse 'ot-ctl dataset active' (human-readable, NOT -x hex form).

    Extracts safe fields only (network name, channel, PAN ID, mesh local prefix).
    Network Key and PSKc are explicitly not extracted and not stored.

    For fingerprinting: callers should use DatasetFingerprint.from_raw_hex()
    with the output of 'ot-ctl dataset active -x' separately, and then discard
    the raw hex immediately.

    Step 2: implement using real fixture from tests/fixtures/house_dataset_active.txt
             (⚠ fixture must have Network Key and PSKc replaced with 'xxxx')
    """
    # TODO (Step 2): implement with real fixture
    fp = DatasetFingerprint(source_name=source_name)

    for field_name, pattern in SAFE_FIELD_RE.items():
        m = pattern.search(raw)
        if m:
            value = m.group(1).strip()
            if field_name == "channel":
                try:
                    fp.channel = int(value)
                except ValueError:
                    pass
            else:
                setattr(fp, field_name, value)

    return fp
