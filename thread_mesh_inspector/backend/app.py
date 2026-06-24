"""
Thread Mesh Inspector — main application entry point.

Starts the async polling scheduler, builds the FastAPI app,
and serves both the API and the frontend static bundle.
"""
from __future__ import annotations
import asyncio
import logging
import os
import sys
import yaml
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.sources.base import OtbrSourceConfig, SourceType, CommandMode
from backend.sources.local_docker import LocalDockerOtbrSource
from backend.sources.ssh_docker import SshDockerOtbrSource
from backend.sources.rest import RestOtbrSource
from backend.sources.mock import MockOtbrSource
from backend.merge.topology import TopologyMerger, MergedTopology
from backend.registry.mapper import HaRegistryMapper
from backend.aliases.resolver import AliasResolver
from backend.history.db import HistoryDb
from backend.api.routes import create_router

logging.basicConfig(
    level=os.environ.get("TMI_LOG_LEVEL", "info").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

DATA_DIR = os.environ.get("TMI_DATA_DIR", "/data")
CONFIG_FILE = os.environ.get("TMI_CONFIG_FILE", os.path.join(DATA_DIR, "config.yaml"))
MOCK_MODE = os.environ.get("TMI_MOCK_MODE", "false").lower() == "true"
POLL_INTERVAL = int(os.environ.get("TMI_POLL_INTERVAL", "60"))
LIVE_POLL_INTERVAL = int(os.environ.get("TMI_LIVE_POLL_INTERVAL", "3"))
INGRESS_PORT = int(os.environ.get("TMI_INGRESS_PORT", "8099"))

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


def load_config() -> dict:
    """Load /data/config.yaml, return empty dict if missing."""
    try:
        with open(CONFIG_FILE) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.info("No config file at %s — using defaults. See example_configuration.yaml.", CONFIG_FILE)
        return {}
    except Exception as e:
        logger.error("Failed to load config: %s", e)
        return {}


def build_sources(config: dict, mock_mode: bool) -> list:
    """Build OTBR source instances from configuration."""
    if mock_mode:
        logger.warning("⚠ MOCK MODE — no real OTBR data will be collected.")
        return [MockOtbrSource(OtbrSourceConfig(name="Mock", source_type=SourceType.MOCK))]

    sources = []
    for s in config.get("otbr_sources", []):
        name = s.get("name", "Unnamed OTBR")
        stype = s.get("type", "local_docker")
        cmd_mode_str = s.get("command_mode", "sudo_n_docker_exec")
        try:
            cmd_mode = CommandMode(cmd_mode_str)
        except ValueError:
            logger.warning("[%s] Unknown command_mode '%s', using sudo_n_docker_exec", name, cmd_mode_str)
            cmd_mode = CommandMode.SUDO_N_DOCKER_EXEC

        cfg = OtbrSourceConfig(
            name=name,
            source_type=SourceType(stype),
            container=s.get("container"),
            command_mode=cmd_mode,
            custom_prefix=s.get("custom_prefix"),
            host=s.get("host"),
            port=s.get("port", 22),
            user=s.get("user"),
            ssh_key_path=s.get("ssh_key_path"),
            rest_fallback_url=s.get("rest_fallback_url"),
            base_url=s.get("base_url"),
        )
        if stype == "local_docker":
            sources.append(LocalDockerOtbrSource(cfg))
        elif stype == "ssh_docker":
            sources.append(SshDockerOtbrSource(cfg))
        elif stype == "rest":
            sources.append(RestOtbrSource(cfg))
        else:
            logger.warning("[%s] Unknown source type '%s' — skipping", name, stype)

    if not sources:
        logger.warning("No OTBR sources configured. Add sources to %s", CONFIG_FILE)
    return sources


class ThreadMeshInspector:
    """Main application class — owns the poll loop and topology state."""

    def __init__(self):
        self.config = load_config()
        self.sources = build_sources(self.config, MOCK_MODE)
        self.merger = TopologyMerger(poll_interval_seconds=POLL_INTERVAL)
        self.registry = HaRegistryMapper()
        self.aliases = AliasResolver(self.config.get("node_aliases", {}))
        self.history = HistoryDb(DATA_DIR)
        self._topology: Optional[MergedTopology] = None
        self._poll_task: Optional[asyncio.Task] = None

    def get_topology(self) -> MergedTopology:
        if self._topology is None:
            # Return empty topology until first poll completes
            from backend.merge.topology import MergedTopology
            from datetime import datetime, timezone
            return MergedTopology(merged_at=datetime.now(timezone.utc))
        return self._topology

    def get_history(self) -> HistoryDb:
        return self.history

    async def _poll_once(self) -> None:
        """Collect from all sources and merge into topology."""
        snapshots = await asyncio.gather(
            *[source.collect() for source in self.sources],
            return_exceptions=True,
        )
        valid_snapshots = []
        for i, snap in enumerate(snapshots):
            if isinstance(snap, Exception):
                logger.error("Source %s raised: %s", self.sources[i].name, snap)
            else:
                valid_snapshots.append(snap)

        merged = self.merger.merge(valid_snapshots)

        # Enrich with HA registry (friendly names)
        await self.registry.enrich_nodes(merged.nodes)

        # Apply manual aliases (may override or fill in where registry failed)
        self.aliases.apply(merged.nodes)

        self._topology = merged
        logger.debug("Topology updated: %d nodes, %d links, %d findings",
                     len(merged.nodes), len(merged.links), len(merged.findings))

    async def _poll_loop(self) -> None:
        while True:
            try:
                await self._poll_once()
            except Exception as e:
                logger.error("Poll cycle failed: %s", e)
            await asyncio.sleep(POLL_INTERVAL)

    async def startup(self) -> None:
        await self.history.open()
        # Initial poll immediately, then start loop
        await self._poll_once()
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("Thread Mesh Inspector started. %d source(s) configured.", len(self.sources))

    async def shutdown(self) -> None:
        if self._poll_task:
            self._poll_task.cancel()
        await self.history.close()


def create_app() -> FastAPI:
    inspector = ThreadMeshInspector()

    app = FastAPI(
        title="Thread Mesh Inspector",
        version="0.1.0",
        description="Thread mesh topology visualiser for Home Assistant",
    )

    @app.on_event("startup")
    async def on_startup():
        await inspector.startup()

    @app.on_event("shutdown")
    async def on_shutdown():
        await inspector.shutdown()

    # API routes
    api_router = create_router(inspector.get_topology, inspector.get_history)
    app.include_router(api_router)

    # Serve the frontend SPA
    if FRONTEND_DIST.exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            """Serve index.html for all non-API routes (SPA routing)."""
            index = FRONTEND_DIST / "index.html"
            if index.exists():
                # index.html must never be cached: it references content-hashed
                # asset filenames that change every build. If the browser serves
                # a stale index.html, it loads stale JS and add-on updates appear
                # to "do nothing" until a manual hard refresh. The hashed /assets
                # files are themselves immutable, so only this entry needs no-cache.
                return FileResponse(str(index), headers={"Cache-Control": "no-cache"})
            return {"error": "Frontend not built. Run: cd frontend && npm run build"}
    else:
        logger.warning("Frontend dist not found at %s — serving API only. "
                       "Run 'cd frontend && npm run build' to build the UI.", FRONTEND_DIST)

    return app


if __name__ == "__main__":
    # CLI: python -m backend.app [--mock] [--dump-topology]
    args = set(sys.argv[1:])

    if "--dump-topology" in args:
        # Print the merged topology and exit — used for Step 2 validation
        async def dump():
            inspector = ThreadMeshInspector()
            await inspector.history.open()
            await inspector._poll_once()
            topo = inspector.get_topology()
            print(f"\n=== Thread Mesh Inspector — Topology Dump ===")
            print(f"Merged at: {topo.merged_at}")
            print(f"Mock mode: {topo.is_mock}")
            print(f"Nodes ({len(topo.nodes)}):")
            for node in topo.nodes:
                conf = node.name_confidence.value.upper()
                print(f"  [{conf:11}] {node.display_name:40} | {node.role.value:15} | "
                      f"extaddr={node.extaddr} rloc16={node.rloc16}")
            print(f"\nLinks ({len(topo.links)}):")
            for link in topo.links:
                quality = link.quality_label
                print(f"  {link.source_extaddr or '?':16} → {link.target_extaddr or '?':16} "
                      f"| {quality} (LQ={link.lq_in}, RSSI={link.rssi})")
            print(f"\nDataset: {topo.dataset_match.summary if topo.dataset_match else 'N/A'}")
            print(f"\nFindings ({len(topo.findings)}):")
            for f in topo.findings:
                print(f"  [{f.severity.value.upper():7}] {f.title}")
                print(f"           {f.description[:120]}")
            await inspector.history.close()

        asyncio.run(dump())
    else:
        app = create_app()
        uvicorn.run(app, host="0.0.0.0", port=INGRESS_PORT, log_level="info")
