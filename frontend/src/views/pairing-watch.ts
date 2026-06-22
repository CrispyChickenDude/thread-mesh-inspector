/**
 * Pairing Watch view — guided workflow for watching the mesh during Matter commissioning.
 * Step 4: full implementation. This is the scaffold.
 * All DOM manipulation uses textContent/DOM methods — no innerHTML with data.
 */
import { api, TopologyData } from "../api/client.js";

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  return e;
}

export async function renderPairingWatch(container: HTMLElement): Promise<void> {
  const card = el("div", "tmi-card");
  const title = el("h2");
  title.textContent = "Pairing Watch";
  card.appendChild(title);

  const intro = el("p");
  intro.style.cssText = "color:var(--secondary-text-color);margin-bottom:16px;font-size:14px;line-height:1.5";
  intro.textContent =
    "Pairing Watch monitors your Thread mesh in real time while you commission a new " +
    "Matter-over-Thread device. It detects when a device joins Thread and gives you a " +
    "plain-English verdict on whether the join succeeded.";
  card.appendChild(intro);

  // Pre-check: load current state
  const checking = el("p");
  checking.textContent = "Checking OTBR sources…";
  checking.style.color = "var(--secondary-text-color)";
  card.appendChild(checking);

  let topo: TopologyData;
  try {
    topo = await api.topology();
  } catch {
    card.removeChild(checking);
    const err = el("p");
    err.style.color = "var(--error-color)";
    err.textContent = "Cannot reach the backend. Is the add-on running?";
    card.appendChild(err);
    container.appendChild(card);
    return;
  }
  card.removeChild(checking);

  // Pre-flight checks
  const checks = el("div");
  checks.style.cssText = "margin-bottom:16px;";

  function checkRow(label: string, passed: boolean, note: string): HTMLElement {
    const r = el("div");
    r.style.cssText = "display:flex;align-items:flex-start;gap:8px;margin-bottom:8px";
    const icon = el("span");
    icon.textContent = passed ? "✓" : "✗";
    icon.style.color = passed ? "var(--success-color)" : "var(--error-color)";
    icon.style.fontWeight = "700";
    const text = el("div");
    const lblEl = el("strong");
    lblEl.textContent = label;
    const noteEl = el("p");
    noteEl.style.cssText = "font-size:12px;color:var(--secondary-text-color);margin-top:2px";
    noteEl.textContent = note;
    text.appendChild(lblEl);
    text.appendChild(noteEl);
    r.appendChild(icon);
    r.appendChild(text);
    return r;
  }

  const anySourceHealthy = topo.sources.some(s => s.is_healthy || s.is_partial);
  const datasetMatch = topo.dataset_match?.all_match;

  checks.appendChild(checkRow(
    "OTBR sources reachable",
    anySourceHealthy,
    anySourceHealthy
      ? `${topo.sources.length} source(s) responding.`
      : "No sources responding. Check Settings and add-on logs.",
  ));

  checks.appendChild(checkRow(
    "Thread datasets match",
    datasetMatch === true,
    datasetMatch === true
      ? "Both OTBRs are on the same dataset. ✓"
      : datasetMatch === false
      ? "⚠ Dataset mismatch! Fix this before pairing."
      : "Dataset match status unknown — check Sources.",
  ));

  checks.appendChild(checkRow(
    "No weak links",
    topo.weak_link_count === 0,
    topo.weak_link_count === 0
      ? "All links are good."
      : `${topo.weak_link_count} weak link(s) detected. Pairing may be slower.`,
  ));

  card.appendChild(checks);

  // Start button
  const canStart = anySourceHealthy;
  const startBtn = el("button");
  startBtn.style.cssText = [
    "display:block;width:100%;padding:14px;",
    "background:var(--primary-color);color:#fff;",
    "border:none;border-radius:var(--border-radius);",
    "font-size:15px;font-weight:600;cursor:pointer;",
    canStart ? "" : "opacity:0.5;cursor:not-allowed;",
  ].join("");
  startBtn.textContent = "▶ Start Pairing Watch";
  startBtn.disabled = !canStart;
  card.appendChild(startBtn);

  // Warning about diagnostic traffic
  const warning = el("p");
  warning.style.cssText = "font-size:12px;color:var(--secondary-text-color);margin-top:8px;text-align:center";
  warning.textContent =
    "⚠ Pairing Watch polls your OTBR every 3 seconds. This creates a small amount of " +
    "diagnostic traffic on the mesh. It stops automatically after 5 minutes.";
  card.appendChild(warning);

  // Timeline container (shown after start)
  const timeline = el("div");
  timeline.style.cssText = "margin-top:20px;display:none";
  const timelineTitle = el("h3");
  timelineTitle.textContent = "Event timeline";
  timeline.appendChild(timelineTitle);
  const eventList = el("div");
  eventList.style.cssText = "margin-top:8px;font-size:13px";
  timeline.appendChild(eventList);
  card.appendChild(timeline);

  let watchInterval: ReturnType<typeof setInterval> | null = null;
  let startTime: Date | null = null;
  let knownExtaddrs = new Set(topo.nodes.map(n => n.extaddr).filter(Boolean));

  function addEvent(text: string, kind: "info" | "success" | "warn" = "info") {
    const row = el("div");
    row.style.cssText = "padding:6px 0;border-bottom:1px solid var(--divider-color)";
    const elapsed = startTime
      ? Math.floor((Date.now() - startTime.getTime()) / 1000)
      : 0;
    const mm = String(Math.floor(elapsed / 60)).padStart(2, "0");
    const ss = String(elapsed % 60).padStart(2, "0");
    const time = el("span");
    time.style.cssText = "color:var(--secondary-text-color);font-family:monospace;margin-right:8px";
    time.textContent = `${mm}:${ss}`;
    const msg = el("span");
    msg.style.color =
      kind === "success" ? "var(--success-color)"
      : kind === "warn" ? "var(--warning-color)"
      : "var(--primary-text-color)";
    msg.textContent = text;
    row.appendChild(time);
    row.appendChild(msg);
    eventList.insertBefore(row, eventList.firstChild);
  }

  startBtn.addEventListener("click", async () => {
    if (watchInterval) {
      clearInterval(watchInterval);
      watchInterval = null;
      startBtn.textContent = "▶ Start Pairing Watch";
      addEvent("Pairing Watch stopped.", "info");
      return;
    }

    startTime = new Date();
    timeline.style.display = "block";
    startBtn.textContent = "■ Stop Pairing Watch";
    addEvent("Pairing Watch started. Start pairing your device from the HA mobile app now.", "info");

    let elapsed = 0;
    const MAX_SECONDS = 5 * 60;

    watchInterval = setInterval(async () => {
      elapsed += 3;
      if (elapsed >= MAX_SECONDS) {
        clearInterval(watchInterval!);
        watchInterval = null;
        startBtn.textContent = "▶ Start Pairing Watch";
        addEvent("Pairing Watch ended (5-minute limit reached).", "info");
        addEvent(
          knownExtaddrs.size === (topo?.nodes.length ?? 0)
            ? "No new devices joined Thread during this session. The device may not have received Thread credentials, or BLE commissioning may have failed."
            : "Session ended. Check the nodes that appeared above.",
          "warn"
        );
        return;
      }

      try {
        const current = await api.topology();
        const currentExtaddrs = new Set(current.nodes.map(n => n.extaddr).filter(Boolean) as string[]);

        // New nodes
        for (const addr of currentExtaddrs) {
          if (!knownExtaddrs.has(addr)) {
            const node = current.nodes.find(n => n.extaddr === addr);
            const name = node?.display_name ?? addr ?? "unknown";
            addEvent(`New node joined: ${name} (${addr})`, "success");
            knownExtaddrs.add(addr);
          }
        }

        // Disappeared nodes
        for (const addr of [...knownExtaddrs]) {
          if (!currentExtaddrs.has(addr)) {
            addEvent(`Node disappeared: ${addr}`, "warn");
            knownExtaddrs.delete(addr);
          }
        }
      } catch {
        addEvent("Poll failed — backend unreachable.", "warn");
      }
    }, 3000);
  });

  container.appendChild(card);

  // Step 4 note
  const note = el("div", "tmi-card");
  note.style.cssText = "margin-top:12px;font-size:12px;color:var(--secondary-text-color)";
  const noteText = el("p");
  noteText.textContent =
    "Step 4 (full implementation): adds Server-Sent Events streaming for instant detection, " +
    "parent-change tracking, and a plain-English verdict (joined-and-stayed / joined-then-dropped " +
    "/ never-appeared / joined-but-Matter-failed).";
  note.appendChild(noteText);
  container.appendChild(note);
}
