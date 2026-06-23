"""Parser for: ot-ctl counters mac / counters mle."""
from __future__ import annotations
import re
from typing import Optional


def parse_counters_mac(raw: str) -> dict:
    """
    Parse 'ot-ctl counters mac' output.

    Expected output (abbreviated):
        TxTotal: 1234
        TxUnicast: 890
        TxBroadcast: 344
        TxAckRequested: 890
        TxAcked: 887
        TxNoAckRequested: 344
        TxData: 1200
        TxDataPoll: 0
        TxBeacon: 0
        ...
        RxTotal: 2345
        RxUnicast: 1980
        ...
        RxErrNoFrame: 0
        RxErrUnknownNeighbor: 0

    Returns a flat dict of counter_name -> int.

    Step 2: implement using real fixture.
    """
    # TODO (Step 2): implement with real fixture
    return _parse_key_value_counters(raw)


def parse_counters_mle(raw: str) -> dict:
    """
    Parse 'ot-ctl counters mle' output.

    Returns a flat dict of counter_name -> int.

    Step 2: implement using real fixture.
    """
    # TODO (Step 2): implement with real fixture
    return _parse_key_value_counters(raw)


def _parse_key_value_counters(raw: str) -> dict:
    """Generic key: value counter parser."""
    result = {}
    for line in raw.strip().splitlines():
        m = re.match(r"^\s*(\w+):\s*(\d+)", line)
        if m:
            result[m.group(1)] = int(m.group(2))
    return result
