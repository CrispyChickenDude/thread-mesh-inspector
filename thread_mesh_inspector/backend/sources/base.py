"""Abstract base class for all OTBR data sources."""
from __future__ import annotations
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from backend.models.node import ThreadNode
from backend.models.link import ThreadLink
from backend.models.dataset import DatasetFingerprint
from backend.models.event import MeshEvent

logger = logging.getLogger(__name__)


class SourceType(str, Enum):
    LOCAL_DOCKER = "local_docker"
    SSH_DOCKER = "ssh_docker"
    REST = "rest"
    MOCK = "mock"
    PACKET_CAPTURE = "packet_capture"  # Phase 2


class CommandMode(str, Enum):
    """How to invoke docker exec for ot-ctl commands."""
    DOCKER_EXEC = "docker_exec"               # docker exec <container> ot-ctl <cmd>
    SUDO_DOCKER_EXEC = "sudo_docker_exec"     # sudo docker exec ...
    SUDO_N_DOCKER_EXEC = "sudo_n_docker_exec" # sudo -n docker exec ... (non-interactive)
    CUSTOM = "custom"                          # custom_prefix + ot-ctl <cmd>


@dataclass
class OtbrSourceConfig:
    """Configuration for a single OTBR source."""
    name: str
    source_type: SourceType
    container: Optional[str] = None
    command_mode: CommandMode = CommandMode.SUDO_N_DOCKER_EXEC
    custom_prefix: Optional[str] = None
    # SSH fields
    host: Optional[str] = None
    port: int = 22
    user: Optional[str] = None
    ssh_key_path: Optional[str] = None
    # REST fallback
    rest_fallback_url: Optional[str] = None
    # REST primary
    base_url: Optional[str] = None


@dataclass
class SourceSnapshot:
    """Everything collected from a single OTBR in one poll cycle."""
    source_name: str
    collected_at: datetime
    # Node identity
    self_extaddr: Optional[str] = None
    self_rloc16: Optional[str] = None
    self_role: Optional[str] = None
    partition_id: Optional[int] = None
    # Topology tables
    nodes: list[ThreadNode] = field(default_factory=list)
    links: list[ThreadLink] = field(default_factory=list)
    # Dataset
    dataset: Optional[DatasetFingerprint] = None
    # Events generated during this collection
    events: list[MeshEvent] = field(default_factory=list)
    # Collection health
    errors: list[str] = field(default_factory=list)
    is_partial: bool = False   # True if some commands failed

    @property
    def is_healthy(self) -> bool:
        return len(self.errors) == 0 and not self.is_partial


class OtbrSource(ABC):
    """
    Abstract base class for all OTBR data sources.

    Each implementation collects Thread data via a different access method
    (docker exec, SSH, REST) but returns the same SourceSnapshot type.
    The merge layer and UI never care which access method was used.
    """

    def __init__(self, config: OtbrSourceConfig):
        self.config = config
        self.name = config.name
        self._last_snapshot: Optional[SourceSnapshot] = None
        self._consecutive_failures: int = 0

    @abstractmethod
    async def collect(self) -> SourceSnapshot:
        """
        Collect a full topology snapshot from this OTBR.
        Must never raise — catches all exceptions internally and returns
        a partial/error snapshot so the caller can keep running.
        """
        ...

    @abstractmethod
    async def is_reachable(self) -> bool:
        """Quick reachability check (no full collection)."""
        ...

    async def run_otctl_command(self, command: str) -> tuple[str, str]:
        """
        Run a single ot-ctl command and return (stdout, stderr).
        Must be implemented by concrete subclasses that use command execution.
        Raises NotImplementedError for REST-only sources.
        """
        raise NotImplementedError(f"{type(self).__name__} does not support ot-ctl commands directly")

    def _make_error_snapshot(self, error: str) -> SourceSnapshot:
        """Return a snapshot indicating a collection failure."""
        self._consecutive_failures += 1
        logger.warning("[%s] Collection failed: %s (failure #%d)",
                       self.name, error, self._consecutive_failures)
        snap = SourceSnapshot(
            source_name=self.name,
            collected_at=datetime.now(timezone.utc),
            errors=[error],
            is_partial=True,
        )
        # Carry forward last known nodes as stale
        if self._last_snapshot:
            for node in self._last_snapshot.nodes:
                node.is_stale = True
            snap.nodes = self._last_snapshot.nodes
            snap.dataset = self._last_snapshot.dataset
        return snap

    def _clear_failure_count(self) -> None:
        if self._consecutive_failures > 0:
            logger.info("[%s] Collection recovered after %d failure(s)",
                        self.name, self._consecutive_failures)
        self._consecutive_failures = 0
