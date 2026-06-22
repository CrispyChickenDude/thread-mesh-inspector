/** History view — Step 5 stub. */
import { api } from "../api/client.js";

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  return e;
}

export async function renderHistory(container: HTMLElement): Promise<void> {
  const card = el("div", "tmi-card");
  const h = el("h2");
  h.textContent = "Event History";
  card.appendChild(h);

  let events: unknown[];
  try {
    events = await api.events(50);
  } catch {
    const err = el("p");
    err.style.color = "var(--error-color)";
    err.textContent = "Cannot load history.";
    card.appendChild(err);
    container.appendChild(card);
    return;
  }

  if (!Array.isArray(events) || events.length === 0) {
    const empty = el("p");
    empty.style.color = "var(--secondary-text-color)";
    empty.textContent = "No events recorded yet. Events appear here as your mesh changes.";
    card.appendChild(empty);
  } else {
    for (const evt of events as Record<string, unknown>[]) {
      const row = el("div");
      row.style.cssText = "padding:8px 0;border-bottom:1px solid var(--divider-color);font-size:13px";

      const time = el("span");
      time.style.cssText = "color:var(--secondary-text-color);font-family:monospace;margin-right:8px";
      time.textContent = String(evt["timestamp"] ?? "");

      const kind = el("span");
      kind.style.fontWeight = "600";
      kind.textContent = String(evt["kind"] ?? "");

      const desc = el("span");
      desc.style.color = "var(--secondary-text-color)";
      desc.textContent = " — " + String(evt["description"] ?? "");

      row.appendChild(time);
      row.appendChild(kind);
      row.appendChild(desc);
      card.appendChild(row);
    }
  }

  const note = el("p");
  note.style.cssText = "margin-top:16px;font-size:12px;color:var(--secondary-text-color)";
  note.textContent =
    "Step 5 (full implementation): adds timeline filters, per-node RSSI trend charts (uPlot), " +
    "join/leave/parent-change history, and export.";
  card.appendChild(note);

  container.appendChild(card);
}
