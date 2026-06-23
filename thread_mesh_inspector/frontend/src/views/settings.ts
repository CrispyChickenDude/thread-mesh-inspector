/** Settings view — links to DOCS.md and shows current source health. */
import { api } from "../api/client.js";

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  return e;
}

export async function renderSettings(container: HTMLElement): Promise<void> {
  const card = el("div", "tmi-card");
  const h = el("h2");
  h.textContent = "Settings";
  card.appendChild(h);

  // Configuration file note
  const configNote = el("div");
  configNote.style.cssText = "background:var(--secondary-background-color);border-radius:8px;padding:12px;margin-bottom:16px;font-size:13px";
  const p1 = el("p");
  p1.textContent = "To configure OTBR sources and node aliases, edit /data/config.yaml on the add-on.";
  const p2 = el("p");
  p2.style.marginTop = "6px";
  p2.textContent = "Copy example_configuration.yaml from the add-on repository as a starting point.";
  configNote.appendChild(p1);
  configNote.appendChild(p2);
  card.appendChild(configNote);

  // Source health
  const srcTitle = el("h3");
  srcTitle.style.cssText = "margin-bottom:8px;font-size:14px";
  srcTitle.textContent = "Source status";
  card.appendChild(srcTitle);

  let health;
  try {
    health = await api.health();
  } catch {
    const err = el("p");
    err.style.color = "var(--error-color)";
    err.textContent = "Cannot reach backend.";
    card.appendChild(err);
    container.appendChild(card);
    return;
  }

  const status = el("div");
  status.style.cssText = "font-size:13px;";

  const rows: [string, string][] = [
    ["Backend", "Online"],
    ["Mode", health.mock ? "⚠ MOCK MODE — not real data" : "Live"],
    ["Nodes in topology", String(health.nodes)],
    ["Weak links", String(health.weak_links)],
  ];

  for (const [label, value] of rows) {
    const row = el("div");
    row.style.cssText = "display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--divider-color)";
    const lbl = el("span");
    lbl.style.color = "var(--secondary-text-color)";
    lbl.textContent = label;
    const val = el("span");
    val.style.fontWeight = "500";
    val.textContent = value;
    row.appendChild(lbl);
    row.appendChild(val);
    status.appendChild(row);
  }

  card.appendChild(status);

  // Docs link
  const docsNote = el("p");
  docsNote.style.cssText = "margin-top:16px;font-size:12px;color:var(--secondary-text-color)";
  docsNote.textContent = "Full documentation: see DOCS.md in the add-on repository, or the Documentation tab in the HA add-on UI.";
  card.appendChild(docsNote);

  container.appendChild(card);
}
