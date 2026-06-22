"""Tests for the manual alias resolver."""
import pytest
from backend.aliases.resolver import AliasResolver
from backend.models.node import ThreadNode, NodeRole, NameConfidence


ALIAS_CONFIG = {
    "62e24d4b7e30e78c": {
        "name": "Environment - Garage [Ambient]",
        "area": "Garage",
    },
    "bea21efee32302ba": {
        "name": "Remote - Garage [Lights]",
        "area": "Garage",
    },
    "0x3c00": {
        "name": "Temporary RLOC alias",
    },
}


class TestAliasResolver:
    def setup_method(self):
        self.resolver = AliasResolver(ALIAS_CONFIG)

    def test_extaddr_alias_applied(self):
        node = ThreadNode(extaddr="62e24d4b7e30e78c", role=NodeRole.SLEEPY_CHILD)
        self.resolver.apply([node])
        assert node.friendly_name == "Environment - Garage [Ambient]"
        assert node.area == "Garage"

    def test_extaddr_alias_confidence_is_low(self):
        node = ThreadNode(extaddr="62e24d4b7e30e78c")
        self.resolver.apply([node])
        assert node.name_confidence == NameConfidence.LOW

    def test_rloc16_alias_applied(self):
        node = ThreadNode(rloc16="0x3c00")
        self.resolver.apply([node])
        assert node.friendly_name == "Temporary RLOC alias"

    def test_rloc16_alias_confidence_is_temporary(self):
        node = ThreadNode(rloc16="0x3c00")
        self.resolver.apply([node])
        assert node.name_confidence == NameConfidence.TEMPORARY

    def test_high_confidence_not_overridden(self):
        node = ThreadNode(
            extaddr="62e24d4b7e30e78c",
            friendly_name="Official HA Name",
            name_confidence=NameConfidence.HIGH,
        )
        self.resolver.apply([node])
        # HIGH confidence names must not be overridden by aliases
        assert node.friendly_name == "Official HA Name"
        assert node.name_confidence == NameConfidence.HIGH

    def test_unknown_extaddr_not_modified(self):
        node = ThreadNode(extaddr="aaaaaaaaaaaaaaaa")
        original_name = node.friendly_name
        self.resolver.apply([node])
        assert node.friendly_name == original_name

    def test_alias_count(self):
        assert self.resolver.alias_count == 3

    def test_empty_config(self):
        resolver = AliasResolver({})
        node = ThreadNode(extaddr="62e24d4b7e30e78c")
        resolver.apply([node])  # must not raise
        assert node.friendly_name is None
