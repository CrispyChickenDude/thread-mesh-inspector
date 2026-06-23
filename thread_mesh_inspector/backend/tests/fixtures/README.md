# Test fixtures — real ot-ctl output

Place real ot-ctl command output here as plain text files.

## File naming convention

```
<hub>_<command_slug>.txt
```

Examples:
- `house_state.txt`
- `house_child_table.txt`
- `house_neighbor_table.txt`
- `house_router_table.txt`
- `house_dataset_active.txt`   ← ⚠ MUST be redacted (see below)
- `garage_state.txt`
- `garage_child_table.txt`
- etc.

## How to collect

**House OTBR** (run from the HA terminal add-on or SSH add-on):
```bash
docker exec addon_core_openthread_border_router ot-ctl state
docker exec addon_core_openthread_border_router ot-ctl child table
docker exec addon_core_openthread_border_router ot-ctl neighbor table
docker exec addon_core_openthread_border_router ot-ctl router table
docker exec addon_core_openthread_border_router ot-ctl netdata show
docker exec addon_core_openthread_border_router ot-ctl ipaddr
docker exec addon_core_openthread_border_router ot-ctl parent
docker exec addon_core_openthread_border_router ot-ctl counters mac
docker exec addon_core_openthread_border_router ot-ctl counters mle
docker exec addon_core_openthread_border_router ot-ctl srp server host
docker exec addon_core_openthread_border_router ot-ctl srp server service
docker exec addon_core_openthread_border_router ot-ctl dataset active
```

**Garage OTBR** (run from a shell on 192.168.1.234):
```bash
sudo docker exec otbr-garage ot-ctl state
# ... same commands with otbr-garage container name
```

## ⚠ Secret safety — CRITICAL

Before saving `dataset active` output as a fixture:

1. Find the `Network Key:` line and replace its value with `xxxx`
2. Find the `PSKc:` line and replace its value with `xxxx`
3. Do NOT save `dataset active -x` (raw hex) — never needed for tests

The `.gitignore` excludes `real_*` prefixed files as extra protection,
but the safest approach is manual redaction before saving ANY fixture file.

## Status (Step 2)

These fixture files do not exist yet. They will be created after you paste
real ot-ctl output from your hubs during Step 2 of implementation.

The parsers in `backend/parsers/` have TODO (Step 2) comments indicating
exactly which fixture each parser will be validated against.
