"""Tests for data models — pass immediately, no fixtures needed."""
import pytest
from backend.models.node import ThreadNode, NodeRole, NameConfidence
from backend.models.link import ThreadLink, LinkQuality
from backend.models.dataset import DatasetFingerprint


class TestThreadNode:
    def test_display_name_friendly(self):
        n = ThreadNode(friendly_name="My Sensor", extaddr="aabbccddeeff0011")
        assert n.display_name == "My Sensor"

    def test_display_name_extaddr_fallback(self):
        n = ThreadNode(extaddr="aabbccddeeff0011")
        assert "0011" in n.display_name  # last 6 chars of extaddr

    def test_display_name_rloc_fallback(self):
        n = ThreadNode(rloc16="0x3400")
        assert "0x3400" in n.display_name

    def test_display_name_unknown(self):
        n = ThreadNode()
        assert n.display_name == "Unknown node"

    def test_is_sleepy(self):
        n = ThreadNode(role=NodeRole.SLEEPY_CHILD)
        assert n.is_sleepy is True

    def test_is_not_sleepy(self):
        n = ThreadNode(role=NodeRole.CHILD)
        assert n.is_sleepy is False

    def test_is_router(self):
        for role in (NodeRole.LEADER, NodeRole.ROUTER, NodeRole.BORDER_ROUTER):
            n = ThreadNode(role=role)
            assert n.is_router is True

    def test_is_not_router(self):
        for role in (NodeRole.CHILD, NodeRole.SLEEPY_CHILD, NodeRole.REED):
            n = ThreadNode(role=role)
            assert n.is_router is False


class TestThreadLink:
    def test_quality_from_lq(self):
        assert ThreadLink(lq_in=3).quality == LinkQuality.GOOD
        assert ThreadLink(lq_in=2).quality == LinkQuality.MARGINAL
        assert ThreadLink(lq_in=1).quality == LinkQuality.WEAK
        assert ThreadLink(lq_in=0).quality == LinkQuality.WEAK

    def test_quality_from_rssi(self):
        assert ThreadLink(rssi=-60).quality == LinkQuality.GOOD
        assert ThreadLink(rssi=-78).quality == LinkQuality.MARGINAL
        assert ThreadLink(rssi=-90).quality == LinkQuality.WEAK

    def test_lq_takes_priority_over_rssi(self):
        # lq_in is preferred over rssi
        assert ThreadLink(lq_in=3, rssi=-95).quality == LinkQuality.GOOD

    def test_quality_unknown_when_no_metrics(self):
        assert ThreadLink().quality == LinkQuality.UNKNOWN

    def test_is_weak(self):
        assert ThreadLink(lq_in=1).is_weak is True
        assert ThreadLink(lq_in=3).is_weak is False

    def test_is_marginal(self):
        assert ThreadLink(lq_in=2).is_marginal is True


class TestDatasetFingerprint:
    def test_from_raw_hex_produces_fingerprint(self):
        fp = DatasetFingerprint.from_raw_hex("deadbeef1234abcd", source_name="Test")
        assert fp.fingerprint_hash is not None
        assert len(fp.fingerprint_hash) == 16  # truncated SHA-256

    def test_same_hex_same_fingerprint(self):
        a = DatasetFingerprint.from_raw_hex("deadbeef1234abcd", source_name="A")
        b = DatasetFingerprint.from_raw_hex("deadbeef1234abcd", source_name="B")
        assert a.matches(b) is True

    def test_different_hex_different_fingerprint(self):
        a = DatasetFingerprint.from_raw_hex("deadbeef1234abcd", source_name="A")
        b = DatasetFingerprint.from_raw_hex("cafebabe98765432", source_name="B")
        assert a.matches(b) is False

    def test_matches_returns_none_when_unknown(self):
        a = DatasetFingerprint(fingerprint_hash=None)
        b = DatasetFingerprint(fingerprint_hash="abcd1234ef567890")
        assert a.matches(b) is None
