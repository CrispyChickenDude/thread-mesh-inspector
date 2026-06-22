"""Thread dataset fingerprint model — stores a safe summary, never raw keys."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import hashlib


@dataclass
class DatasetFingerprint:
    """
    A safe, non-secret summary of a Thread active dataset.

    Raw dataset secrets (Network Key, PSKc, etc.) are NEVER stored here.
    Comparison between OTBRs uses the fingerprint_hash only.
    """
    # Safe fields (not secret)
    network_name: Optional[str] = None    # e.g. "ha-thread-1c20"
    channel: Optional[int] = None         # e.g. 15
    pan_id: Optional[str] = None          # e.g. "0xabcd" (public, in beacon)
    ext_pan_id: Optional[str] = None      # extended PAN ID (public)
    mesh_local_prefix: Optional[str] = None

    # Fingerprint computed over the raw hex dataset (dataset active -x)
    # but only the fingerprint is stored — raw hex is discarded immediately
    fingerprint_hash: Optional[str] = None  # SHA-256 of raw dataset hex

    # Source
    source_name: Optional[str] = None
    observed_at: Optional[datetime] = None
    is_stale: bool = False

    @classmethod
    def from_raw_hex(cls, raw_hex: str, source_name: str, **safe_fields) -> "DatasetFingerprint":
        """
        Create a fingerprint from a raw dataset hex string.
        The raw hex is hashed and then discarded — it is never stored.
        """
        fingerprint = hashlib.sha256(raw_hex.strip().encode()).hexdigest()[:16]
        return cls(
            fingerprint_hash=fingerprint,
            source_name=source_name,
            observed_at=datetime.now(timezone.utc),
            **safe_fields,
        )

    def matches(self, other: "DatasetFingerprint") -> Optional[bool]:
        """
        Compare datasets by fingerprint.
        Returns None if either fingerprint is unknown.
        Returns True if they match (same dataset), False if they differ.
        """
        if self.fingerprint_hash is None or other.fingerprint_hash is None:
            return None
        return self.fingerprint_hash == other.fingerprint_hash

    @property
    def match_summary(self) -> str:
        """Plain-English dataset match summary for two-OTBR comparison."""
        if self.fingerprint_hash is None:
            return "Dataset unknown — could not read from this OTBR"
        return f"Dataset fingerprint: {self.fingerprint_hash}"
