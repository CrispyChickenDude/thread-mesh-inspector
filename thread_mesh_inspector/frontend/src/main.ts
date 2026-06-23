/**
 * Thread Mesh Inspector — main entry point.
 * Simple hash-based router; no framework needed for this SPA.
 */
import { renderOverview } from "./views/overview.js";
import { renderTopology } from "./views/topology.js";
import { renderPairingWatch } from "./views/pairing-watch.js";
import { renderDiagnostics } from "./views/diagnostics.js";
import { renderHistory } from "./views/history.js";
import { renderSettings } from "./views/settings.js";

type Route = {
  path: string;
  label: string;
  icon: string;
  render: (container: HTMLElement) => void | Promise<void>;
};

const ROUTES: Route[] = [
  { path: "#overview",     label: "Overview",      icon: "mdi:view-dashboard-outline", render: renderOverview },
  { path: "#topology",     label: "Topology",      icon: "mdi:network-outline",        render: renderTopology },
  { path: "#pairing",      label: "Pairing Watch", icon: "mdi:radar",                  render: renderPairingWatch },
  { path: "#diagnostics",  label: "Diagnostics",   icon: "mdi:stethoscope",            render: renderDiagnostics },
  { path: "#history",      label: "History",       icon: "mdi:history",                render: renderHistory },
  { path: "#settings",     label: "Settings",      icon: "mdi:cog-outline",            render: renderSettings },
];

function buildNav(): HTMLElement {
  const nav = document.createElement("nav");
  nav.className = "tmi-nav";
  nav.innerHTML = `<div class="tmi-nav-title">Thread Mesh Inspector</div>`;
  for (const route of ROUTES) {
    const a = document.createElement("a");
    a.href = route.path;
    a.className = "tmi-nav-item";
    a.textContent = route.label;
    a.dataset.path = route.path;
    nav.appendChild(a);
  }
  return nav;
}

function buildStyles(): HTMLStyleElement {
  const style = document.createElement("style");
  style.textContent = `
    .tmi-shell { display: flex; height: 100vh; overflow: hidden; }
    .tmi-nav {
      width: 200px; min-width: 200px;
      background: var(--card-background-color);
      border-right: 1px solid var(--divider-color);
      display: flex; flex-direction: column;
      padding: 16px 0;
    }
    .tmi-nav-title {
      font-weight: 600; font-size: 14px;
      padding: 0 16px 16px;
      color: var(--secondary-text-color);
      border-bottom: 1px solid var(--divider-color);
      margin-bottom: 8px;
    }
    .tmi-nav-item {
      display: block; padding: 10px 20px;
      text-decoration: none;
      color: var(--secondary-text-color);
      font-size: 14px; border-radius: 0;
      transition: background 0.15s, color 0.15s;
    }
    .tmi-nav-item:hover { background: var(--secondary-background-color); color: var(--primary-text-color); }
    .tmi-nav-item.active { background: var(--primary-color); color: #fff; }
    .tmi-content { flex: 1; overflow-y: auto; padding: 24px; }
    .tmi-card {
      background: var(--card-background-color);
      border-radius: var(--border-radius);
      padding: 20px; margin-bottom: 16px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    .tmi-card h2 { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
    .tmi-badge {
      display: inline-flex; align-items: center; gap: 4px;
      padding: 2px 8px; border-radius: 12px;
      font-size: 12px; font-weight: 500;
    }
    .tmi-badge-good    { background: #e8f5e9; color: #2e7d32; }
    .tmi-badge-warn    { background: #fff3e0; color: #e65100; }
    .tmi-badge-error   { background: #ffebee; color: #c62828; }
    .tmi-badge-info    { background: #e3f2fd; color: #0277bd; }
    .tmi-badge-temp    { background: #f3e5f5; color: #6a1b9a; }
    .tmi-mock-banner {
      background: #fff3cd; color: #856404;
      padding: 8px 16px; text-align: center;
      font-size: 13px; font-weight: 500;
    }
    @media (max-width: 600px) {
      .tmi-shell { flex-direction: column; }
      .tmi-nav { width: 100%; min-width: unset; flex-direction: row; overflow-x: auto; padding: 0; }
      .tmi-nav-title { display: none; }
      .tmi-nav-item { white-space: nowrap; padding: 12px 16px; }
    }
  `;
  return style;
}

async function route() {
  const hash = window.location.hash || "#overview";
  const matched = ROUTES.find(r => r.path === hash) ?? ROUTES[0];

  document.querySelectorAll(".tmi-nav-item").forEach(el => {
    el.classList.toggle("active", (el as HTMLElement).dataset.path === matched.path);
  });

  const content = document.getElementById("tmi-content")!;
  content.innerHTML = "";
  try {
    await matched.render(content);
  } catch (err) {
    // Use DOM methods — never innerHTML with error messages (XSS risk)
    const card = document.createElement("div");
    card.className = "tmi-card";
    const heading = document.createElement("h2");
    heading.textContent = "Error loading view";
    const msg = document.createElement("p");
    msg.style.color = "var(--error-color)";
    msg.textContent = err instanceof Error ? err.message : String(err);
    card.appendChild(heading);
    card.appendChild(msg);
    content.appendChild(card);
  }
}

function init() {
  const app = document.getElementById("app")!;
  app.appendChild(buildStyles());

  const shell = document.createElement("div");
  shell.className = "tmi-shell";
  shell.appendChild(buildNav());

  const content = document.createElement("main");
  content.id = "tmi-content";
  content.className = "tmi-content";
  shell.appendChild(content);
  app.appendChild(shell);

  window.addEventListener("hashchange", route);
  route();
}

init();
