/**
 * Overview view — the first screen.
 * Answers: healthy? OTBRs up? same dataset? weak links? unexpected events?
 * Uses DOM methods throughout — no innerHTML with data-derived content.
 */
import { api, TopologyData, SourceData, FindingData } from "../api/client.js";

function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  cls?: string,
  text?: string
): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

function badge(text: string, kind: "good" | "warn" | "error" | "info" | "temp"): HTMLElement {
  const b = el("span", `tmi-badge tmi-badge-${kind}`);
  b.textContent = text;
  return b;
}

function card(title: string): { card: HTMLElement; body: HTMLElement } {
  const c = el("div", "tmi-card");
  c.appendChild(el("h2", undefined, title));
  const body = el("div");
  c.appendChild(body);
  return { card: c, body };
}

function sourceCard(source: SourceData): HTMLElement {
  const { card: c, body } = card(source.source_name);
  c.style.cssText = "display:inline-block;min-width:200px;margin-right:12px;vertical-align:top";

  const status = source.is_healthy
    ? badge("Online", "good")
    : source.is_partial
    ? badge("Partial", "warn")
    : badge("Offline", "error");
  body.appendChild(status);

  const count = el("p");
  count.style.marginTop = "8px";
  count.textContent = `${source.node_count} nodes visible`;
  body.appendChild(count);

  if (source.errors.length > 0 && source.errors[0] !== "") {
    for (const err of source.errors.slice(0, 2)) {
      const note = el("p");
      note.style.cssText = "font-size:12px;color:var(--secondary-text-color);margin-top:4px";
      note.textContent = err;
      body.appendChild(note);
    }
  }
  return c;
}

function findingRow(f: FindingData): HTMLElement {
  const row = el("div");
  row.style.cssText = "padding:10px 0;border-bottom:1px solid var(--divider-color)";

  const kind = f.severity === "error" ? "error" : f.severity === "warning" ? "warn" : "info";
  const b = badge(f.severity.toUpperCase(), kind);
  b.style.marginRight = "8px";

  const title = el("strong");
  title.textContent = f.title;

  const desc = el("p");
  desc.style.cssText = "margin-top:4px;font-size:13px;color:var(--secondary-text-color)";
  desc.textContent = f.description;

  row.appendChild(b);
  row.appendChild(title);
  row.appendChild(desc);

  if (f.suggested_action) {
    const action = el("p");
    action.style.cssText = "margin-top:4px;font-size:12px;font-style:italic;color:var(--secondary-text-color)";
    action.textContent = `→ ${f.suggested_action}`;
    row.appendChild(action);
  }
  return row;
}

export async function renderOverview(container: HTMLElement): Promise<void> {
  const loading = el("p", undefined, "Loading mesh data…");
  container.appendChild(loading);

  let topo: TopologyData;
  try {
    topo = await api.topology();
  } catch {
    container.removeChild(loading);
    const err = el("p");
    err.style.color = "var(--error-color)";
    err.textContent = "Could not reach the backend API. Is the add-on running?";
    container.appendChild(err);
    return;
  }
  container.removeChild(loading);

  // Mock banner
  if (topo.is_mock) {
    const banner = el("div", "tmi-mock-banner");
    banner.textContent = "⚠ MOCK MODE — showing example data, not your real mesh";
    container.appendChild(banner);
  }

  // Dataset match card (most important at a glance)
  {
    const { card: c, body } = card("Thread Dataset");
    if (topo.dataset_match) {
      const matchBadge =
        topo.dataset_match.all_match === true
          ? badge("✓ Datasets match — do not re-key Thread", "good")
          : topo.dataset_match.all_match === false
          ? badge("⚠ Dataset mismatch!", "error")
          : badge("Dataset status unknown", "warn");
      body.appendChild(matchBadge);
      const summary = el("p");
      summary.style.marginTop = "8px";
      summary.textContent = topo.dataset_match.summary;
      body.appendChild(summary);
    } else {
      body.textContent = "Dataset data not yet available.";
    }
    container.appendChild(c);
  }

  // OTBR sources row
  {
    const { card: c, body } = card("OTBR Sources");
    body.style.display = "flex";
    body.style.flexWrap = "wrap";
    body.style.gap = "12px";
    for (const src of topo.sources) {
      body.appendChild(sourceCard(src));
    }
    if (topo.sources.length === 0) {
      body.textContent = "No sources configured. See Settings.";
    }
    container.appendChild(c);
  }

  // Mesh summary stats
  {
    const { card: c, body } = card("Mesh Summary");
    const stats: [string, string | number, "good" | "warn" | "error" | "info"][] = [
      ["Routers", topo.router_count, "good"],
      ["Children", topo.child_count, "info"],
      ["Sleepy devices", topo.sleepy_count, "info"],
      ["Weak links", topo.weak_link_count, topo.weak_link_count > 0 ? "warn" : "good"],
      ["Stale nodes", topo.stale_node_count, topo.stale_node_count > 0 ? "warn" : "good"],
    ];
    const grid = el("div");
    grid.style.cssText = "display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px";
    for (const [label, value, kind] of stats) {
      const cell = el("div");
      cell.style.cssText = "text-align:center;padding:12px;background:var(--secondary-background-color);border-radius:8px";
      const num = el("div");
      num.style.cssText = "font-size:28px;font-weight:700";
      if (kind === "warn") num.style.color = "var(--warning-color)";
      else if (kind === "error") num.style.color = "var(--error-color)";
      num.textContent = String(value);
      const lbl = el("div");
      lbl.style.cssText = "font-size:12px;color:var(--secondary-text-color);margin-top:4px";
      lbl.textContent = label;
      cell.appendChild(num);
      cell.appendChild(lbl);
      grid.appendChild(cell);
    }
    body.appendChild(grid);
    container.appendChild(c);
  }

  // Findings
  if (topo.findings.length > 0) {
    const { card: c, body } = card(`Issues (${topo.findings.length})`);
    for (const f of topo.findings) {
      body.appendChild(findingRow(f));
    }
    container.appendChild(c);
  } else {
    const { card: c, body } = card("Issues");
    body.appendChild(badge("✓ No issues detected", "good"));
    container.appendChild(c);
  }

  // Primary action
  const pairingBtn = el("button");
  pairingBtn.style.cssText = [
    "display:block;width:100%;padding:16px;",
    "background:var(--primary-color);color:#fff;",
    "border:none;border-radius:var(--border-radius);",
    "font-size:16px;font-weight:600;cursor:pointer;",
    "margin-top:8px;",
  ].join("");
  pairingBtn.textContent = "▶ Start Pairing Watch";
  pairingBtn.addEventListener("click", () => {
    window.location.hash = "#pairing";
  });
  container.appendChild(pairingBtn);
}
