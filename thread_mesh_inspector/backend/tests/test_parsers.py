"""
Parser tests.

Basic sanity tests run with synthetic input now (Step 1).
Full validation against real ot-ctl fixtures happens in Step 2,
once you paste real output from both hubs.

To add real fixtures:
1. See tests/fixtures/README.md for collection instructions
2. Save redacted output as tests/fixtures/house_<cmd>.txt
3. Uncomment the @pytest.mark.real_fixture tests below and run pytest
"""
import pytest
from backend.parsers.state import parse_state, parse_extaddr, parse_rloc16, parse_partitionid, parse_channel, state_to_role
from backend.parsers.child_table import parse_child_table
from backend.parsers.neighbor_table import parse_neighbor_table
from backend.parsers.router_table import parse_router_table
from backend.parsers.dataset import parse_dataset_active
from backend.parsers.ipaddr import parse_ipaddr, parse_parent
from backend.models.node import NodeRole


# ── State parser ──────────────────────────────────────────────────────────────

class TestParseState:
    def test_leader(self):
        assert parse_state("leader\n") == "leader"

    def test_router(self):
        assert parse_state("router\n") == "router"

    def test_child(self):
        assert parse_state("child\n") == "child"

    def test_unknown_state(self):
        assert parse_state("junk\n") is None

    def test_state_to_role_leader(self):
        assert state_to_role("leader") == NodeRole.LEADER

    def test_state_to_role_router(self):
        assert state_to_role("router") == NodeRole.ROUTER

    def test_state_to_role_unknown(self):
        assert state_to_role(None) == NodeRole.UNKNOWN


class TestParseExtaddr:
    def test_valid(self):
        assert parse_extaddr("6e50644a86a9b7a4\n") == "6e50644a86a9b7a4"

    def test_uppercase_normalised(self):
        assert parse_extaddr("6E50644A86A9B7A4\n") == "6e50644a86a9b7a4"

    def test_too_short(self):
        assert parse_extaddr("abcd\n") is None

    def test_invalid_chars(self):
        assert parse_extaddr("ZZZZZZZZZZZZZZZZ\n") is None


class TestParseRloc16:
    def test_hex_prefix(self):
        assert parse_rloc16("0x9800\n") == "0x9800"

    def test_decimal_converted(self):
        result = parse_rloc16("38912\n")
        assert result == "0x9800"

    def test_invalid(self):
        assert parse_rloc16("junk\n") is None


class TestParseChannel:
    def test_channel_15(self):
        assert parse_channel("15\n") == 15

    def test_invalid(self):
        assert parse_channel("not a number\n") is None


# ── Child table parser ────────────────────────────────────────────────────────

SYNTHETIC_CHILD_TABLE = """\
| ID  | RLOC16 | Timeout    | Age        | LQ In | C_VN |R|D|N|Ver|CSL|QMsgCnt| Extended MAC     |
+-----+--------+------------+------------+-------+------+-+-+-+---+---+-------+------------------+
|   1 | 0x3401 |        240 |          5 |     3 |  225 |0|0|1|  4| 0 |     0 | 62e24d4b7e30e78c |
|   5 | 0x3405 |        240 |         12 |     3 |  114 |0|1|0|  4| 0 |     0 | bea21efee32302ba |
Done
"""

class TestParseChildTable:
    def setup_method(self):
        self.nodes = parse_child_table(SYNTHETIC_CHILD_TABLE, source_name="Test OTBR")

    def test_parses_two_children(self):
        assert len(self.nodes) == 2

    def test_extaddrs(self):
        extaddrs = {n.extaddr for n in self.nodes}
        assert "62e24d4b7e30e78c" in extaddrs
        assert "bea21efee32302ba" in extaddrs

    def test_rloc16s(self):
        rlocs = {n.rloc16 for n in self.nodes}
        assert "0x3401" in rlocs
        assert "0x3405" in rlocs

    def test_lq_in(self):
        for node in self.nodes:
            assert node.lq_in == 3

    def test_r_flag_0_is_sleepy(self):
        # R=0 means sleepy (RxOff)
        node_3401 = next(n for n in self.nodes if n.rloc16 == "0x3401")
        assert node_3401.role == NodeRole.SLEEPY_CHILD


# ── Neighbor table parser ─────────────────────────────────────────────────────

SYNTHETIC_NEIGHBOR_TABLE = """\
| Role | RLOC16 | Age | Avg RSSI | Last RSSI |R|D|N| Extended MAC     |
+------+--------+-----+----------+-----------+-+-+-+------------------+
|   R  | 0x9800 |  45 |      -55 |       -52 |1|1|1| 6e50644a86a9b7a4 |
|   C  | 0x3401 |   5 |      -72 |       -70 |0|0|1| 62e24d4b7e30e78c |
Done
"""

class TestParseNeighborTable:
    def setup_method(self):
        self.links = parse_neighbor_table(
            SYNTHETIC_NEIGHBOR_TABLE,
            self_extaddr="4232f2a613d2a61a",
            source_name="Test OTBR",
        )

    def test_parses_two_links(self):
        assert len(self.links) == 2

    def test_router_link_detected(self):
        router_link = next(l for l in self.links if l.target_rloc16 == "0x9800")
        assert router_link.is_router_link is True

    def test_child_link_detected(self):
        child_link = next(l for l in self.links if l.target_rloc16 == "0x3401")
        assert child_link.is_child_link is True

    def test_rssi_parsed(self):
        router_link = next(l for l in self.links if l.target_extaddr == "6e50644a86a9b7a4")
        assert router_link.rssi == -55


# ── Dataset parser ────────────────────────────────────────────────────────────

SYNTHETIC_DATASET = """\
Active Timestamp: 1
Channel: 15
Channel Mask: 0x07fff800
Ext PAN ID: 1122334455667788
Mesh Local Prefix: fd13:810b:b3b3:1::/64
Network Key: xxxx
Network Name: ha-thread-1c20
PAN ID: 0x1c20
PSKc: xxxx
Security Policy: 672 onrcb 0
Done
"""

class TestParseDataset:
    def setup_method(self):
        self.fp = parse_dataset_active(SYNTHETIC_DATASET, source_name="Test")

    def test_network_name(self):
        assert self.fp.network_name == "ha-thread-1c20"

    def test_channel(self):
        assert self.fp.channel == 15

    def test_pan_id(self):
        assert self.fp.pan_id == "0x1c20"

    def test_network_key_not_present(self):
        # Sanity check: the parser should never expose the Network Key
        assert not hasattr(self.fp, "network_key") or getattr(self.fp, "network_key", None) is None


# ── Merge / mock source integration ──────────────────────────────────────────

class TestMockSource:
    """Smoke test: MockOtbrSource collects and merge works."""

    @pytest.mark.asyncio
    async def test_mock_collect_returns_snapshot(self):
        from backend.sources.base import OtbrSourceConfig, SourceType
        from backend.sources.mock import MockOtbrSource
        cfg = OtbrSourceConfig(name="Test Mock", source_type=SourceType.MOCK)
        source = MockOtbrSource(cfg)
        snap = await source.collect()
        assert len(snap.nodes) > 0
        assert snap.is_healthy or "MOCK" in str(snap.errors)

    @pytest.mark.asyncio
    async def test_mock_merge_produces_topology(self):
        from backend.sources.base import OtbrSourceConfig, SourceType
        from backend.sources.mock import MockOtbrSource
        from backend.merge.topology import TopologyMerger
        cfg = OtbrSourceConfig(name="Test Mock", source_type=SourceType.MOCK)
        source = MockOtbrSource(cfg)
        snap = await source.collect()
        merger = TopologyMerger()
        topo = merger.merge([snap])
        assert topo.is_mock is True
        assert len(topo.nodes) > 0
        assert topo.dataset_match is not None
