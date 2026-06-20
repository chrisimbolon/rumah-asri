// =============================================================================
// === frontend/lib/api/construction.ts ===
// =============================================================================
/**
 * RumahAsri — Construction Phases API
 */

import api from "@/lib/api";

export interface ConstructionPhoto {
  id:              string;
  image:           string;
  caption:         string;
  uploaded_by_name: string;
  uploaded_at:     string;
}

export interface ConstructionPhase {
  id:              string;
  phase_order:     number;
  phase_name:      string;
  phase_date:      string;
  status:          string;
  status_display:  string;
  notes:           string;
  updated_by_name: string;
  photos:          ConstructionPhoto[];
  created_at:      string;
  updated_at:      string;
}

export interface PhaseListResponse {
  success:       boolean;
  unit_id:       string;
  unit_number:   string;
  progress:      number;
  phases:        ConstructionPhase[];
}

export interface PhaseDetailResponse {
  success: boolean;
  phase:   ConstructionPhase;
}

export interface UpdatePhasePayload {
  phase_date?: string;
  status?:     string;
  notes?:      string;
}

export const constructionApi = {
  async listPhases(unitId: string): Promise<PhaseListResponse> {
    const { data } = await api.get<PhaseListResponse>(
      `/api/construction/${unitId}/phases/`
    );
    return data;
  },

  async updatePhase(
    phaseId: string,
    payload: UpdatePhasePayload
  ): Promise<ConstructionPhase> {
    const { data } = await api.put<PhaseDetailResponse>(
      `/api/construction/phases/${phaseId}/`,
      payload
    );
    return data.phase;
  },
};