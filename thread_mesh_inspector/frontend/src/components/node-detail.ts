/**
 * Node detail panel — shown when clicking a node in the topology graph.
 * Uses only textContent/DOM methods — no innerHTML with data.
 */
import { NodeData } from "../api/client.js";

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  return e;
}

function row(label: string, value: string | null | undefined): HTMLElement {
  if (!value) return el("div"); // empty — omit from panel
  const r = el("div");
  r.style.cssText = "display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--divider-color);font-size:13px";
  const lbl = el("span");
  lbl.style.color = "var(--secondary-text-color)";
  lbl.textContent = label;
  const val = el("span");
  val.style.cssText = "font-weight:500;text-align:right;max-width:60%;word-break:break-all";
  val.textContent = value;
  r.appendChild(lbl);
  r.appendChild(val);
  return r;
}

function confidenceBadge(confidence: string): HTMLElement {
  const labels: Record<string, { text: string; cls: string }> = {
    high:      { text: "✓ High confidence name",         cls: "tmi-badge tmi-badge-good" },
    medium:    { text: "~ Medium confidence name",        cls: "tmi-badge tmi-badge-info" },
    low:       { text: "⚠ Manual alias",                  cls: "tmi-badge tmi-badge-warn" },
    temporary: { text: "⏳ Temporary (RLOC16-only name)", cls: "tmi-badge tmi-badge-temp" },
  };
  const { text, cls } = labels[confidence] ?? labels.temporary;
  const b = el("span", cls);
  b.textContent = text;
  return b;
}

function lqLabel(lq: number | null | undefined): string {
  if (lq == null) return "—";
  if (lq >= 3) return `${lq} (Good)`;
  if (lq === 2) return `${lq} (Marginal)`;
  return `${lq} (Weak)`;
}

function rssiLabel(rssi: number | null | undefined): string {
  if (rssi == null) return "—";
  if (rssi >= -70) return `${rssi} dBm (Good)`;
  if (rssi >= -85) return `${rssi} dBm (Marginal)`;
  return `${rssi} dBm (Weak)`;
}

function roleLabel(role: string): string {
  const labels: Record<string, string> = {
    leader: "Leader",
    border_router: "Border Router",
    router: "Router",
    reed: "REED (Router-Eligible End Device)",
    child: "Child (end device, always-on)",
    sleepy_child: "Sleepy end device (wakes on schedule)",
    unknown: "Unknown",
  };
  return labels[role] ?? role;
}

export function renderNodeDetail(node: NodeData, container: HTMLElement): void {
  const panel = el("div", "tmi-card");

  // Header
  const header = el("div");
  header.style.cssText = "margin-bottom:12px";
  const name = el("h3");
  name.style.cssText = "font-size:15px;font-weight:600;margin-bottom:6px";
  name.textContent = node.display_name;
  header.appendChild(name);
  header.appendChild(confidenceBadge(node.name_confidence));
  panel.appendChild(header);

  // HA device link
  if (node.ha_device_url) {
    const link = document.createElement("a");
    link.href = node.ha_device_url;
    link.target = "_top"; // open in HA frame
    link.style.cssText = "font-size:12px;color:var(--primary-color);display:block;margin-bottom:12px";
    link.textContent = "→ Open in Home Assistant";
    panel.appendChild(link);
  }

  // Alerts
  if (node.is_stale) {
    const stale = el("div", "tmi-badge tmi-badge-warn");
    stale.style.display = "block";
    stale.style.marginBottom = "8px";
    stale.textContent = "⚠ Data is stale — node may have gone offline";
    panel.appendChild(stale);
  }
  if (node.is_sleepy) {
    const sleepy = el("div", "tmi-badge tmi-badge-info");
    sleepy.style.display = "block";
    sleepy.style.marginBottom = "8px";
    sleepy.textContent = "💤 Sleepy device — ping non-response is normal";
    panel.appendChild(sleepy);
  }

  // Core fields
  const fields: [string, string | null | undefined][] = [
    ["Role", roleLabel(node.role)],
    ["Area", node.area],
    ["Manufacturer", node.manufacturer],
    ["Model", node.model],
    ["Extended MAC", node.extaddr],
    ["RLOC16", node.rloc16],
    ["Router ID", node.router_id != null ? String(node.router_id) : null],
    ["Partition", null], // filled from topology if available
    ["Parent", node.parent_extaddr],
    ["LQ In (to parent)", lqLabel(node.lq_in)],
    ["LQ Out", lqLabel(node.lq_out)],
    ["RSSI", rssiLabel(node.rssi)],
    ["Path cost", node.path_cost != null ? String(node.path_cost) : null],
    ["Age", node.age_seconds != null ? `${node.age_seconds}s ago` : null],
    ["Timeout", node.timeout_seconds != null ? `${node.timeout_seconds}s` : null],
    ["First seen", node.first_seen ? new Date(node.first_seen).toLocaleString() : null],
    ["Last seen", node.last_seen ? new Date(node.last_seen).toLocaleString() : null],
    ["Sources", node.source_names.join(", ")],
    ["SRP hostname", node.srp_hostname],
  ];

  for (const [label, value] of fields) {
    const r = row(label, value ?? null);
    if (r.childElementCount > 0) panel.appendChild(r);
  }

  // OMR addresses
  if (node.omr_addresses.length > 0) {
    const section = el("div");
    section.style.marginTop = "8px";
    const lbl = el("div");
    lbl.style.cssText = "font-size:12px;color:var(--secondary-text-color);margin-bottom:4px";
    lbl.textContent = "OMR addresses (mesh-routable)";
    section.appendChild(lbl);
    for (const addr of node.omr_addresses) {
      const addrEl = el("div");
      addrEl.style.cssText = "font-size:11px;font-family:monospace;color:var(--primary-text-color)";
      addrEl.textContent = addr; // textContent — safe
      section.appendChild(addrEl);
    }
    panel.appendChild(section);
  }

  container.appendChild(panel);
}
