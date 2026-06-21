// =============================================================================
// === frontend/lib/api/units.ts ===
// =============================================================================
/**
 * DevelopIndo — Units API
 */

import api from "@/lib/api";

export interface Unit {
  id:                 string;
  unit_number:        string;
  unit_type:          string;
  land_area:          string;
  building_area:      string;
  price:              number;
  status:             string;
  status_display:     string;
  progress:           number;
  current_phase:      string;
  target_completion:  string | null;
  payment_method:     string;
  bank:               string;
  project:            string;   // UUID
  project_name:       string;
  buyer:              string | null;  // UUID
  buyer_name:         string | null;
  buyer_email:        string | null;
  created_at:         string;
}

export interface UnitListResponse {
  success: boolean;
  count:   number;
  results: Unit[];
}

export interface UnitDetailResponse {
  success: boolean;
  unit:    Unit;
}

export interface CreateUnitPayload {
  project:           string;
  unit_number:       string;
  unit_type:         string;
  land_area:         number;
  building_area:     number;
  price:             number;
  status?:           string;
  progress?:         number;
  current_phase?:    string;
  target_completion?: string;
  payment_method?:   string;
  bank?:             string;
  buyer?:            string | null;
}

export const unitsApi = {
  async list(params?: { project?: string; status?: string }): Promise<Unit[]> {
    const { data } = await api.get<UnitListResponse>("/api/units/", { params });
    return data.results;
  },

  async get(id: string): Promise<Unit> {
    const { data } = await api.get<UnitDetailResponse>(`/api/units/${id}/`);
    return data.unit;
  },

  async create(payload: CreateUnitPayload): Promise<Unit> {
    const { data } = await api.post<UnitDetailResponse>("/api/units/", payload);
    return data.unit;
  },

  async update(id: string, payload: Partial<CreateUnitPayload>): Promise<Unit> {
    const { data } = await api.put<UnitDetailResponse>(
      `/api/units/${id}/`,
      payload
    );
    return data.unit;
  },
};
