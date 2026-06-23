"""Local Docker source — runs ot-ctl via docker exec on the HA host."""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from .base import OtbrSource, OtbrSourceConfig, CommandMode, SourceSnapshot
from backend import parsers

logger = logging.getLogger(__name__)

# Commands to run in a standard full collection cycle
COLLECTION_COMMANDS = [
    "state",
    "extaddr",
    "rloc16",
    "partitionid",
    "version",
    "channel",
    "child table",
    "neighbor table",
    "router table",
    "netdata show",
    "ipaddr",
    "parent",
    "counters mac",
    "counters mle",
    "srp server host",
    "srp server service",
    "dataset active",   # human-readable; Network Key / PSKc stripped by parser
]


class LocalDockerOtbrSource(OtbrSource):
    """
    Collects Thread data by running:
        docker exec <container> ot-ctl <command>
    (or sudo / sudo -n variant per command_mode)

    Requires protection_mode: false in the add-on config so the Docker
    socket is accessible from the add-on container.
    """

    def _build_exec_prefix(self) -> list[str]:
        """Build the command prefix based on configured command mode."""
        container = self.config.container or "addon_core_openthread_border_router"
        mode = self.config.command_mode
        if mode == CommandMode.DOCKER_EXEC:
            return ["docker", "exec", container]
        if mode == CommandMode.SUDO_DOCKER_EXEC:
            return ["sudo", "docker", "exec", container]
        if mode == CommandMode.SUDO_N_DOCKER_EXEC:
            return ["sudo", "-n", "docker", "exec", container]
        if mode == CommandMode.CUSTOM and self.config.custom_prefix:
            return self.config.custom_prefix.split() + [container]
        raise ValueError(f"Unknown command mode: {mode}")

    async def run_otctl_command(self, command: str) -> tuple[str, str]:
        """Run a single ot-ctl command via docker exec, return (stdout, stderr)."""
        prefix = self._build_exec_prefix()
        cmd = prefix + ["ot-ctl"] + command.split()
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
            return stdout.decode(), stderr.decode()
        except asyncio.TimeoutError:
            logger.warning("[%s] ot-ctl '%s' timed out", self.name, command)
            return "", "timeout"
        except PermissionError as e:
            raise PermissionError(
                f"[{self.name}] Docker exec failed with PermissionError. "
                f"Ensure protection_mode: false is set in config.yaml and the Docker "
                f"socket is accessible. Original error: {e}"
            ) from e
        except FileNotFoundError:
            raise RuntimeError(
                f"[{self.name}] 'docker' command not found in the add-on container. "
                f"The Dockerfile must install docker-cli. Check your build."
            )

    async def is_reachable(self) -> bool:
        try:
            stdout, _ = await self.run_otctl_command("state")
            return bool(stdout.strip())
        except Exception:
            return False

    async def collect(self) -> SourceSnapshot:
        """Run all collection commands and parse the results."""
        snap = SourceSnapshot(source_name=self.name, collected_at=datetime.now(timezone.utc))
        try:
            results: dict[str, str] = {}
            for cmd in COLLECTION_COMMANDS:
                stdout, stderr = await self.run_otctl_command(cmd)
                if stderr and "sudo:" in stderr and "password" in stderr.lower():
                    return self._make_error_snapshot(
                        f"sudo requires a password for '{cmd}'. "
                        f"Configure passwordless sudo for 'docker exec {self.config.container} ot-ctl' "
                        f"or switch command_mode to 'docker_exec'. "
                        f"See DOCS.md — Configuration — local_docker."
                    )
                results[cmd] = stdout

            snap = parsers.build_snapshot_from_results(self.name, results, snap)
            self._last_snapshot = snap
            self._clear_failure_count()
        except Exception as exc:
            snap = self._make_error_snapshot(str(exc))
        return snap
