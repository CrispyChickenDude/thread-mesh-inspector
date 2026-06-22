"""SSH Docker source — runs ot-ctl on a remote host via SSH + docker exec."""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from .base import OtbrSource, OtbrSourceConfig, CommandMode, SourceSnapshot
from .local_docker import COLLECTION_COMMANDS
from backend import parsers

logger = logging.getLogger(__name__)


class SshDockerOtbrSource(OtbrSource):
    """
    Collects Thread data by SSHing to a remote host and running:
        sudo docker exec <container> ot-ctl <command>

    Requires an SSH key at config.ssh_key_path (never committed to git).
    The key should be scoped to only the ot-ctl docker exec command on the remote.
    See DOCS.md — Configuration — ssh_docker for key setup instructions.
    """

    def _build_command(self, otctl_command: str) -> list[str]:
        """Build the full SSH + docker exec + ot-ctl command."""
        container = self.config.container or "otbr-garage"
        mode = self.config.command_mode

        if mode == CommandMode.DOCKER_EXEC:
            docker_cmd = f"docker exec {container} ot-ctl {otctl_command}"
        elif mode == CommandMode.SUDO_DOCKER_EXEC:
            docker_cmd = f"sudo docker exec {container} ot-ctl {otctl_command}"
        elif mode == CommandMode.SUDO_N_DOCKER_EXEC:
            docker_cmd = f"sudo -n docker exec {container} ot-ctl {otctl_command}"
        elif mode == CommandMode.CUSTOM and self.config.custom_prefix:
            docker_cmd = f"{self.config.custom_prefix} {container} ot-ctl {otctl_command}"
        else:
            raise ValueError(f"Unknown command mode: {mode}")

        host = self.config.host
        port = self.config.port
        user = self.config.user or "alex"
        key_path = self.config.ssh_key_path

        ssh_cmd = ["ssh",
                   "-o", "BatchMode=yes",
                   "-o", "ConnectTimeout=8",
                   "-o", "StrictHostKeyChecking=accept-new",
                   "-p", str(port)]
        if key_path:
            ssh_cmd += ["-i", key_path]
        ssh_cmd += [f"{user}@{host}", docker_cmd]
        return ssh_cmd

    async def run_otctl_command(self, command: str) -> tuple[str, str]:
        cmd = self._build_command(command)
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15.0)
            return stdout.decode(), stderr.decode()
        except asyncio.TimeoutError:
            logger.warning("[%s] SSH ot-ctl '%s' timed out", self.name, command)
            return "", "timeout"

    async def is_reachable(self) -> bool:
        try:
            stdout, stderr = await self.run_otctl_command("state")
            return bool(stdout.strip()) and "Permission denied" not in stderr
        except Exception:
            return False

    async def collect(self) -> SourceSnapshot:
        snap = SourceSnapshot(source_name=self.name, collected_at=datetime.now(timezone.utc))
        try:
            results: dict[str, str] = {}
            for cmd in COLLECTION_COMMANDS:
                stdout, stderr = await self.run_otctl_command(cmd)
                if "Permission denied" in stderr:
                    return self._make_error_snapshot(
                        f"SSH authentication failed for {self.config.user}@{self.config.host}. "
                        f"Check that the SSH key at {self.config.ssh_key_path} is authorised "
                        f"on the remote host. See DOCS.md — Configuration — ssh_docker."
                    )
                if stderr and "sudo:" in stderr and "password" in stderr.lower():
                    return self._make_error_snapshot(
                        f"sudo requires a password on {self.config.host}. "
                        f"Configure passwordless sudo for 'docker exec {self.config.container} ot-ctl' "
                        f"on the remote, or switch command_mode to 'docker_exec'."
                    )
                results[cmd] = stdout

            snap = parsers.build_snapshot_from_results(self.name, results, snap)
            self._last_snapshot = snap
            self._clear_failure_count()
        except Exception as exc:
            snap = self._make_error_snapshot(str(exc))
        return snap
