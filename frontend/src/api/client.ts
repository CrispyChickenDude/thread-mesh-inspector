/**
 * API client — typed wrappers around the backend REST endpoints.
 */

export interface NodeData {
  extaddr: string | null;
  rloc16: string | null;
  router_id: number | null;
  role: string;
  is_border_router: boolean;
  display_name: string;
  friendly_name: string | null;
  name_confidence: "high" | "medium" | "low" | "temporary";
  area: string | null;
  manufacturer: string | null;
  model: string | null;
  ha_device_id: string | null;
  ha_device_url: string | null;
  parent_extaddr: string | null;
  child_extaddrs: string[];
  omr_addresses: string[];
  srp_hostname: string | null;
  rssi: number | null;
  lq_in: number | null;
  lq_out: number | null;
  path_cost: number | null;
  age_seconds: number | null;
  timeout_seconds: number | null;
  is_stale: boolean;
  is_sleepy: boolean;
  source_names: string[];
  last_seen: string | null;
  first_seen: string | null;
}

export interface LinkData {
  source_extaddr: string | null;
  target_extaddr: string | null;
  rssi: number | null;
  lq_in: number | null;
  lq_out: number | null;
  quality: "good" | "marginal" | "weak" | "unknown";
  quality_label: string;
  is_weak: boolean;
  is_marginal: boolean;
  is_child_link: boolean;
  is_router_link: boolean;
  source_otbr: string | null;
  is_stale: boolean;
}

export interface FindingData {
  severity: "info" | "warning" | "error";
  title: string;
  description: string;
  suggested_action: string | null;
  node_extaddr: string | null;
}

export interface SourceData {
  source_name: string;
  collected_at: string | null;
  is_healthy: boolean;
  is_partial: boolean;
  errors: string[];
  node_count: number;
}

export interface TopologyData {
  merged_at: string | null;
  is_mock: boolean;
  router_count: number;
  child_count: number;
  sleepy_count: number;
  weak_link_count: number;
  stale_node_count: number;
  dataset_match: {
    all_match: boolean | null;
    summary: string;
    fingerprints: Record<string, string | null>;
  } | null;
  nodes: NodeData[];
  links: LinkData[];
  findings: FindingData[];
  sources: SourceData[];
}

const API_BASE = "/api/v1";

async function apiFetch<T>(path: string): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`);
  if (!r.ok) throw new Error(`API ${path} → HTTP ${r.status}`);
  return r.json() as Promise<T>;
}

export const api = {
  topology: () => apiFetch<TopologyData>("/topology"),
  nodeDetail: (extaddr: string) => apiFetch<NodeData>(`/topology/nodes/${extaddr}`),
  events: (limit = 100, extaddr?: string) => {
    const q = extaddr ? `?limit=${limit}&node_extaddr=${extaddr}` : `?limit=${limit}`;
    return apiFetch<unknown[]>(`/history/events${q}`);
  },
  metrics: (extaddr: string, limit = 500) =>
    apiFetch<unknown[]>(`/history/metrics/${extaddr}?limit=${limit}`),
  health: () => apiFetch<{ status: string; mock: boolean; nodes: number; weak_links: number }>("/health"),
};
