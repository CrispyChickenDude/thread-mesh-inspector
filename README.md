# Thread Mesh Inspector

> ## ⚠️ Deprecated — this project is retired
>
> **Matter 9.0 now provides this Thread mesh topology and diagnostics functionality
> natively**, so there is no longer a reason to maintain a separate add-on. This
> repository is archived and **no longer developed or supported**. Please use the
> built-in Matter/Thread tooling instead.
>
> The code remains available, read-only, for reference. The last functional release
> is tagged [`v0.1.4-eol`](../../releases). Issues and PRs are closed.

A polished Home Assistant add-on that visualises your real Thread mesh network, shows
per-device health, and helps diagnose why Matter-over-Thread devices won't pair, stay
online, or update.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## What it does

| Question | Answer |
|---|---|
| Is my Thread network healthy? | Overview dashboard — OTBR status, dataset match, weak links, node counts |
| Are both OTBRs on the same dataset? | Dataset fingerprint comparison — no credentials exposed |
| Which device is attached to which parent? | Topology graph with parent/child edges |
| Why is my device dropping or updating slowly? | Per-device diagnostics — path, link quality, flapping |
| Did my device actually join Thread during pairing? | Pairing Watch — live event timeline, plain-English verdict |

## Features

- **Topology graph** — force-directed, pan/zoom, friendly names, colour-coded roles and link quality
- **Pairing Watch** — guided workflow that watches the mesh in real time during Matter commissioning
- **Per-device diagnostics** — hop path, RSSI/LQ, flapping history, plain-English cause suggestions
- **History & trends** — SQLite-backed RSSI/LQ trend charts, join/leave timeline
- **Manual node aliases** — map any extaddr to a friendly name when HA doesn't expose the Thread MAC
- **Confidence badges** — High / Medium / Low / Temporary on every node label
- **Export** — topology JSON, diagnostic summary, PNG/SVG, Markdown (secrets redacted)
- **Read-only** — never modifies your Thread network

## Architecture

The add-on runs alongside Home Assistant OS and collects Thread data from:

- **House OTBR** — via `docker exec addon_core_openthread_border_router ot-ctl …`
- **Garage OTBR** — via SSH → `sudo docker exec otbr-garage ot-ctl …` (plus REST fallback)
- **HA device registry** — for friendly names, areas, and device page links

The ingress web UI is served from the add-on and appears as a panel in the HA sidebar.

## Installation

1. In Home Assistant: **Settings → Add-ons → Add-on Store → ⋮ → Repositories**
2. Add: `https://github.com/alex/thread-mesh-inspector`
3. Find **Thread Mesh Inspector** in the store and click **Install**
4. Configure (see [DOCS.md](DOCS.md)) and start the add-on
5. Open it from the HA sidebar

## Requirements

- Home Assistant OS / Supervised (add-on support required)
- At least one OTBR (add-on or standalone container)
- `protection_mode: false` in add-on config (for `docker exec` access to house OTBR)
- SSH key at `/data/ssh/garage_key` for the garage OTBR (if used)

## Security

- Read-only by default — no write actions implemented
- Thread credentials (Network Key, PSKc) are stripped at collection and never stored or displayed
- Dataset comparison uses a fingerprint hash only
- Docker socket access and SSH are documented trade-offs (see [DOCS.md](DOCS.md) — Security)
- No raw `ot-ctl` output is ever committed to this repository

## Development

See [DOCS.md](DOCS.md) for local development setup, mock mode, and the data-layer build
process (Step 2 — requires real `ot-ctl` output fixtures from your hubs).

## Phase roadmap

- **Phase 1** (this release): Topology, Pairing Watch, Diagnostics, History
- **Phase 2** (pending explicit approval): Packet capture design with a dedicated sniffer radio

## License

MIT — see [LICENSE](LICENSE)
