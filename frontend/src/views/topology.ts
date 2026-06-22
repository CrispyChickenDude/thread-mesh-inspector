/**
 * Topology view — Cytoscape.js graph of the full Thread mesh.
 * Step 3: full implementation. This file is the scaffold/stub.
 */
import { api, TopologyData, NodeData, LinkData } from "../api/client.js";
import { renderNodeDetail } from "../components/node-detail.js";

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  return e;
}

/** Map a node role to a colour for the graph. */
function roleColor(role: string): string {
  const map: Record<string, string> = {
    leader: "#1565c0",        // dark blue
    border_router: "#2e7d32", // dark green
    router: "#0288d1",        // blue
    reed: "#0097a7",          // teal
    child: "#546e7a",         // blue-grey
    sleepy_child: "#7b1fa2",  // purple
    unknown: "#9e9e9e",       // grey
  };
  return map[role] ?? "#9e9e9e";
}

/** Build the Cytoscape elements array from topology data. */
function buildElements(topo: TopologyData): object[] {
  const elements: object[] = [];

  for (const node of topo.nodes) {
    elements.push({
      data: {
        id: node.extaddr ?? node.rloc16 ?? "unknown",
        label: node.display_name,
        role: node.role,
        color: roleColor(node.role),
        borderColor: node.is_stale ? "#bdbdbd" : roleColor(node.role),
        borderStyle: node.is_stale ? "dashed" : "solid",
        opacity: node.is_stale ? 0.5 : 1,
        extaddr: node.extaddr,
        // All display data via textContent — no HTML injection
        displayName: node.display_name,
        confidence: node.name_confidence,
        isSleepy: node.is_sleepy,
        isStale: node.is_stale,
      },
      classes: [
        node.role,
        node.is_stale ? "stale" : "",
        node.is_sleepy ? "sleepy" : "",
        node.is_border_router ? "border-router" : "",
      ].filter(Boolean).join(" "),
    });
  }

  for (const link of topo.links) {
    if (!link.source_extaddr || !link.target_extaddr) continue;
    const edgeColor =
      link.quality === "good" ? "#43a047"
      : link.quality === "marginal" ? "#ff9800"
      : link.quality === "weak" ? "#e53935"
      : "#9e9e9e";
    elements.push({
      data: {
        id: `${link.source_extaddr}-${link.target_extaddr}`,
        source: link.source_extaddr,
        target: link.target_extaddr,
        quality: link.quality,
        label: link.lq_in != null ? `LQ ${link.lq_in}` : "",
        color: edgeColor,
        width: link.is_weak ? 1 : link.is_marginal ? 2 : 3,
      },
      classes: link.quality,
    });
  }

  return elements;
}

export async function renderTopology(container: HTMLElement): Promise<void> {
  // Layout: graph on left, detail panel on right
  const shell = el("div");
  shell.style.cssText = "display:flex;gap:16px;height:calc(100vh - 80px)";

  const graphContainer = el("div");
  graphContainer.id = "tmi-cy-container";
  graphContainer.style.cssText = "flex:1;background:var(--card-background-color);border-radius:var(--border-radius);min-height:400px;";
  shell.appendChild(graphContainer);

  const detailPanel = el("div");
  detailPanel.style.cssText = "width:300px;overflow-y:auto;";
  shell.appendChild(detailPanel);

  container.appendChild(shell);

  const loading = el("p");
  loading.textContent = "Loading topology…";
  loading.style.cssText = "padding:24px;color:var(--secondary-text-color)";
  graphContainer.appendChild(loading);

  let topo: TopologyData;
  try {
    topo = await api.topology();
  } catch {
    graphContainer.removeChild(loading);
    const err = el("p");
    err.style.cssText = "padding:24px;color:var(--error-color)";
    err.textContent = "Could not load topology. Is the add-on running?";
    graphContainer.appendChild(err);
    return;
  }
  graphContainer.removeChild(loading);

  if (topo.is_mock) {
    const banner = el("div", "tmi-mock-banner");
    banner.textContent = "⚠ MOCK MODE";
    graphContainer.appendChild(banner);
  }

  // Load Cytoscape dynamically
  let cytoscape: typeof import("cytoscape").default;
  try {
    const mod = await import("cytoscape");
    cytoscape = mod.default;
  } catch {
    const msg = el("p");
    msg.style.cssText = "padding:24px;color:var(--error-color)";
    msg.textContent = "Cytoscape.js not available. Run: cd frontend && npm install";
    graphContainer.appendChild(msg);
    return;
  }

  const elements = buildElements(topo);

  if (elements.length === 0) {
    const empty = el("p");
    empty.style.cssText = "padding:24px;color:var(--secondary-text-color)";
    empty.textContent = "No nodes found. Check your OTBR sources in Settings.";
    graphContainer.appendChild(empty);
    return;
  }

  const cy = cytoscape({
    container: graphContainer,
    elements,
    layout: { name: "fcose" } as object,
    style: [
      {
        selector: "node",
        style: {
          "background-color": "data(color)",
          "border-color": "data(borderColor)",
          "border-width": 3,
          "border-style": "data(borderStyle)",
          label: "data(label)",
          "font-size": 11,
          "text-valign": "bottom",
          "text-halign": "center",
          "text-margin-y": 4,
          color: "var(--primary-text-color)",
          width: 36,
          height: 36,
          opacity: "data(opacity)",
        } as object,
      },
      {
        selector: "edge",
        style: {
          width: "data(width)",
          "line-color": "data(color)",
          "target-arrow-color": "data(color)",
          "target-arrow-shape": "triangle",
          "curve-style": "bezier",
          label: "data(label)",
          "font-size": 9,
          "text-background-color": "var(--card-background-color)",
          "text-background-opacity": 0.8,
          "text-background-padding": "2px",
        } as object,
      },
      {
        selector: "node.border-router",
        style: { "border-width": 5 } as object,
      },
      {
        selector: "node:selected",
        style: { "border-color": "#ff6f00", "border-width": 5 } as object,
      },
    ],
  });

  // Node click → show detail panel
  cy.on("tap", "node", (evt) => {
    const extaddr: string = evt.target.data("extaddr");
    if (!extaddr) return;
    const node = topo.nodes.find(n => n.extaddr === extaddr);
    if (node) {
      detailPanel.textContent = ""; // safe clear
      renderNodeDetail(node, detailPanel);
    }
  });

  // Show legend
  const legend = el("div");
  legend.style.cssText = "position:absolute;top:8px;right:8px;background:var(--card-background-color);padding:8px 12px;border-radius:8px;font-size:11px;";
  const roles: [string, string][] = [
    ["Leader / BR", roleColor("leader")],
    ["Border Router", roleColor("border_router")],
    ["Router", roleColor("router")],
    ["Child", roleColor("child")],
    ["Sleepy", roleColor("sleepy_child")],
  ];
  for (const [role, color] of roles) {
    const row = el("div");
    row.style.cssText = "display:flex;align-items:center;gap:6px;margin-bottom:3px";
    const dot = el("span");
    dot.style.cssText = `width:10px;height:10px;border-radius:50%;background:${color};display:inline-block`;
    const label = el("span");
    label.textContent = role;
    row.appendChild(dot);
    row.appendChild(label);
    legend.appendChild(row);
  }
  graphContainer.style.position = "relative";
  graphContainer.appendChild(legend);
}
