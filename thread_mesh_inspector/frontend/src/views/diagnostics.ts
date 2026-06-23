/** Diagnostics view — Step 5 stub. */
import { api } from "../api/client.js";

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  return e;
}

export async function renderDiagnostics(container: HTMLElement): Promise<void> {
  const card = el("div", "tmi-card");
  const h = el("h2");
  h.textContent = "Diagnostics";
  card.appendChild(h);

  let topo;
  try {
    topo = await api.topology();
  } catch {
    const err = el("p");
    err.style.color = "var(--error-color)";
    err.textContent = "Cannot load topology.";
    card.appendChild(err);
    container.appendChild(card);
    return;
  }

  // Node selector
  const label = el("label");
  label.textContent = "Select a device to diagnose:";
  label.style.cssText = "display:block;margin-bottom:8px;font-size:13px;color:var(--secondary-text-color)";
  card.appendChild(label);

  const select = el("select");
  select.style.cssText = "width:100%;padding:8px;border-radius:6px;border:1px solid var(--divider-color);background:var(--card-background-color);color:var(--primary-text-color);margin-bottom:16px;font-size:14px";

  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "— choose a node —";
  select.appendChild(placeholder);

  for (const node of topo.nodes) {
    const opt = document.createElement("option");
    opt.value = node.extaddr ?? "";
    opt.textContent = node.display_name;
    select.appendChild(opt);
  }
  card.appendChild(select);

  const detail = el("div");
  card.appendChild(detail);

  select.addEventListener("change", () => {
    detail.textContent = ""; // safe clear
    const extaddr = select.value;
    if (!extaddr) return;

    const node = topo.nodes.find(n => n.extaddr === extaddr);
    if (!node) return;

    // Per-node findings
    const relevant = topo.findings.filter(f => f.node_extaddr === extaddr);
    if (relevant.length === 0) {
      const ok = el("div", "tmi-badge tmi-badge-good");
      ok.textContent = "✓ No issues detected for this device";
      detail.appendChild(ok);
    } else {
      for (const f of relevant) {
        const row = el("div");
        row.style.cssText = "padding:10px 0;border-bottom:1px solid var(--divider-color)";
        const b = el("span", `tmi-badge tmi-badge-${f.severity === "error" ? "error" : f.severity === "warning" ? "warn" : "info"}`);
        b.textContent = f.severity.toUpperCase();
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
        detail.appendChild(row);
      }
    }

    // Step 5 note
    const note = el("p");
    note.style.cssText = "margin-top:16px;font-size:12px;color:var(--secondary-text-color)";
    note.textContent =
      "Step 5 (full implementation): adds hop-by-hop path to border router, " +
      "RSSI trend chart, flapping history, parent-change log.";
    detail.appendChild(note);
  });

  container.appendChild(card);
}
