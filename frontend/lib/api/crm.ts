// =============================================================================
// === frontend/lib/api/crm.ts ===
// =============================================================================
/**
 * DevelopIndo — CRM (Prospect) API
 * Sprint 3: Prospect list, follow-up, and conversion hand-off.
 */

import api from "@/lib/api";

export interface Prospect {
  id:                   string;
  name:                 string;
  phone:                string;
  source:               string;
  interested_project:   string | null;
  project_name:         string | null;
  assigned_to:          string | null;
  assigned_to_name:     string | null;
  status:               "baru" | "follow_up" | "hilang" | "konversi";
  status_display:       string;
  next_followup_date:   string | null;
  notes:                string;
  converted_booking_id: string | null;
  created_at:           string;
  updated_at:           string;
}

export interface ProspectListResponse {
  success: boolean;
  count:   number;
  results: Prospect[];
}

export interface ProspectDetailResponse {
  success:  boolean;
  prospect: Prospect;
}

export interface CreateProspectPayload {
  name:                 string;
  phone:                string;
  source?:              string;
  interested_project?:  string | null;
  assigned_to?:         string | null;
  status?:              Prospect["status"];
  next_followup_date?:  string | null;
  notes?:               string;
}

export const prospectsApi = {
  async list(params?: { status?: string; project?: string }): Promise<Prospect[]> {
    const { data } = await api.get<ProspectListResponse>("/api/prospects/", {
      params,
    });
    return data.results;
  },

  async get(id: string): Promise<Prospect> {
    const { data } = await api.get<ProspectDetailResponse>(
      `/api/prospects/${id}/`
    );
    return data.prospect;
  },

  async create(payload: CreateProspectPayload): Promise<Prospect> {
    const { data } = await api.post<ProspectDetailResponse>(
      "/api/prospects/",
      payload
    );
    return data.prospect;
  },

  async update(id: string, payload: Partial<CreateProspectPayload>): Promise<Prospect> {
    const { data } = await api.put<ProspectDetailResponse>(
      `/api/prospects/${id}/`,
      payload
    );
    return data.prospect;
  },
};
