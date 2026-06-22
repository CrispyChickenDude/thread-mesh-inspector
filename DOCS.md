# Thread Mesh Inspector — Documentation

## Quick start

1. Install the add-on from the custom repository (see README).
2. Copy `example_configuration.yaml` to `/data/config.yaml` via the HA file editor or SSH add-on.
3. Edit `/data/config.yaml` to match your OTBR sources and node aliases.
4. Start the add-on and open it from the HA sidebar.

---

## Configuration

The add-on has two levels of configuration:

### Add-on options (HA UI)

Accessible in Home Assistant under **Settings → Add-ons → Thread Mesh Inspector → Configuration**.

| Option | Default | Description |
|---|---|---|
| `poll_interval_seconds` | 60 | Normal topology poll interval |
| `live_poll_interval_seconds` | 3 | Poll interval during Pairing Watch |
| `log_level` | info | Logging level (trace/debug/info/warning/error) |
| `mock_mode` | false | Show mock data instead of live data (for dev/demo) |

### /data/config.yaml (advanced)

For OTBR sources, node aliases, and reachability configuration. See `example_configuration.yaml`
for the full schema with comments.

---

## OTBR data sources

### local_docker (house OTBR)

Runs `docker exec <container> ot-ctl <cmd>` on the HA host. Requires `protection_mode: false`.

Command mode options:
- `docker_exec` — plain `docker exec` (works if the add-on user has Docker access)
- `sudo_docker_exec` — `sudo docker exec` (prompts for password — use only if passwordless)
- `sudo_n_docker_exec` — `sudo -n docker exec` (non-interactive, preferred)
- `custom` — set `command_prefix` to any string

If this fails: set `command_mode: sudo_n_docker_exec` and ensure a sudoers rule permits
non-interactive `docker exec addon_core_openthread_border_router ot-ctl`.

### ssh_docker (garage OTBR)

SSHes to a remote host and runs `docker exec <container> ot-ctl <cmd>`.

SSH key setup (run from the HA terminal add-on):
```bash
mkdir -p /data/thread_mesh_inspector/ssh
ssh-keygen -t ed25519 -f /data/thread_mesh_inspector/ssh/garage_key -N ""
# Copy the public key to the garage VM:
ssh-copy-id -i /data/thread_mesh_inspector/ssh/garage_key.pub alex@192.168.1.234
```

Then set `ssh_key_path: /data/ssh/garage_key` in your config.

### rest (REST OTBR)

Queries the OTBR REST API directly. Provides identity and dataset only — no child/neighbor/
router tables. Used as a fallback when docker or SSH are unavailable.

---

## Security

### What requires elevated access

| Access | Why needed | Risk |
|---|---|---|
| `protection_mode: false` | Docker socket access for `docker exec` on house OTBR | Add-on can access all containers on the host |
| SSH key in `/data/` | Remote command execution on garage VM | Key must be kept in `/data/`, never committed |
| `homeassistant_api: true` | Friendly name lookup via HA entity/device registry | Read-only API access via Supervisor token |

### What is always protected

- Thread Network Key and PSKc are stripped before any data is stored or displayed.
- Dataset comparison uses a fingerprint hash only; raw dataset is never shown by default.
- Raw dataset is available only in **Settings → Advanced → Debug mode** with explicit warning.
- No write actions are implemented (no `dataset set active`, `factoryreset`, etc.).
- SSH private keys are stored in `/data/` (add-on-managed persistent storage), which is
  excluded from git by `.gitignore`.

### SSH key permissions

The SSH key for the garage OTBR should be narrowly scoped. On the garage VM, restrict the
key to only the `docker exec` command in `~/.ssh/authorized_keys`:

```
command="sudo docker exec otbr-garage ot-ctl $SSH_ORIGINAL_COMMAND",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-ed25519 AAAA... key-comment
```

---

## Mock mode

Set `mock_mode: true` in add-on options to run with a realistic fake topology — useful for
demoing the UI without a live Thread network. Mock mode is clearly labelled in the UI.
No real OTBR is queried in mock mode.

---

## Development

### Local backend development

```bash
cd backend
pip install -r requirements.txt
python -m backend.app --mock   # starts on http://localhost:8099
```

### Local frontend development

```bash
cd frontend
npm install
npm run dev   # Vite dev server with API proxy to localhost:8099
```

### Building the frontend bundle

```bash
cd frontend
npm run build   # output to frontend/dist/ — picked up by Dockerfile
```

### Running tests

```bash
cd backend
pytest tests/ -v
```

### Adding real ot-ctl fixtures (Step 2)

1. Run the ot-ctl commands listed in `tests/fixtures/README.md` on each hub.
2. Redact Network Key and PSKc from any `dataset active` output.
3. Save the output as `tests/fixtures/house_<command>.txt` and `tests/fixtures/garage_<command>.txt`.
4. Run `pytest tests/test_parsers.py -v` to verify parsers against real data.

---

## Installing in Home Assistant as a custom add-on repository

1. Go to **Settings → Add-ons → Add-on Store**
2. Click **⋮ (three dots)** in the top right → **Repositories**
3. Enter: `https://github.com/YOUR_USERNAME/thread-mesh-inspector`
4. Click **Add** → **Close**
5. Scroll down in the store to find **Thread Mesh Inspector** and install it

After installing, configure it under **Settings → Add-ons → Thread Mesh Inspector → Configuration**,
then start it and open the panel from the HA sidebar.
