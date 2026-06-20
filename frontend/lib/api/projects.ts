// =============================================================================
// === frontend/lib/api/projects.ts ===
// =============================================================================
/**
 * DevelopIndo — Projects API
 * Typed wrappers around the real Django backend.
 * Field names match what the backend actually returns (English),
 * NOT the old Bahasa mock-data field names.
 */

import api from "@/lib/api";

// ── Types ─────────────────────────────────────────────────────
export interface Project {
  id:                string;
  name:              string;
  location:          string;
  description:       string;
  status:            string;
  status_display:    string;
  total_units:       number;
  units_sold:        number;
  overall_progress:  number;
  start_date:        string;  // "YYYY-MM-DD"
  end_date:          string;
  organization_name: string;
  created_at:        string;
}

export interface ProjectListResponse {
  success: boolean;
  count:   number;
  results: Project[];
}

export interface ProjectDetailResponse {
  success: boolean;
  project: Project;
}

export interface CreateProjectPayload {
  name:        string;
  location:    string;
  description?: string;
  status:      string;
  total_units: number;
  start_date:  string;
  end_date:    string;
}

// ── API calls ─────────────────────────────────────────────────
export const projectsApi = {
  async list(params?: { status?: string }): Promise<Project[]> {
    const { data } = await api.get<ProjectListResponse>("/api/projects/", {
      params,
    });
    return data.results;
  },

  async get(id: string): Promise<Project> {
    const { data } = await api.get<ProjectDetailResponse>(
      `/api/projects/${id}/`
    );
    return data.project;
  },

  async create(payload: CreateProjectPayload): Promise<Project> {
    const { data } = await api.post<ProjectDetailResponse>(
      "/api/projects/",
      payload
    );
    return data.project;
  },

  async update(id: string, payload: Partial<CreateProjectPayload>): Promise<Project> {
    const { data } = await api.put<ProjectDetailResponse>(
      `/api/projects/${id}/`,
      payload
    );
    return data.project;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/api/projects/${id}/`);
  },
};

// ── Derived stats (computed from project list — no separate stats endpoint yet) ──
export function deriveStats(projects: Project[]) {
  const total_units   = projects.reduce((s, p) => s + p.total_units,   0);
  const units_sold    = projects.reduce((s, p) => s + p.units_sold,    0);
  const units_active  = projects.filter((p) => p.status === "aktif").length;
  const units_available = total_units - units_sold;
  return { total_units, units_sold, units_active, units_available };
}
