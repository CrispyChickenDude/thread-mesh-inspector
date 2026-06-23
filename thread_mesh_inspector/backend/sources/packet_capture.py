"""
Phase 2 placeholder — Packet Capture Source.

⚠ NOT IMPLEMENTED. Phase 2 requires explicit approval before any code is written.

This stub exists so:
- The source interface and data model seam exists from day one
- The import path is stable (backend.sources.PacketCaptureSource)
- Phase 2 implementation can drop in without changing the merge layer
"""
from __future__ import annotations
from .base import OtbrSource, OtbrSourceConfig, SourceSnapshot


class PacketCaptureSource(OtbrSource):
    """
    Phase 2 stub: 802.15.4 packet capture via a dedicated sniffer radio.

    Requirements (Phase 2):
    - Separate, dedicated sniffer radio (MUST NOT be the production OTBR radio)
    - Channel selection matching the Thread network channel
    - Time-limited capture sessions with storage limits
    - PCAP/PCAPNG export compatible with Wireshark
    - Correlation with topology events (pairing watch, join/leave, weak links)
    - Decryption disabled by default; requires explicit user action and secret exposure
    - Clear UI warnings about encrypted payloads and limitations

    Limitations to document in Phase 2:
    - Thread traffic is encrypted; payload analysis requires Thread keys
    - Matter traffic is additionally encrypted at a higher layer
    - Captures cannot explain BLE commissioning, phone, or Matter controller failures
    - Production OTBR radio must never be repurposed as a sniffer

    Status: NOT IMPLEMENTED — awaiting explicit Phase 2 approval.
    """

    async def is_reachable(self) -> bool:
        raise NotImplementedError(
            "PacketCaptureSource is a Phase 2 feature and is not yet implemented. "
            "Enable Phase 2 by explicit approval. See DOCS.md."
        )

    async def collect(self) -> SourceSnapshot:
        raise NotImplementedError(
            "PacketCaptureSource is a Phase 2 feature and is not yet implemented."
        )
