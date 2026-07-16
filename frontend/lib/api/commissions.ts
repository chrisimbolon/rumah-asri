// =============================================================================
// === frontend/lib/api/commissions.ts ===
// =============================================================================
/**
 * DevelopIndo — Commission API
 * Commission Foundation Sprint 1 (flat rate only).
 */

import api from "@/lib/api";

export interface CommissionTier {
  id:          string;
  policy:      string;
  min_amount:  string;
  max_amount:  string | null;
  rate_value:  string;
}

export interface CommissionPolicy {
  id:          string;
  // Sprint 2 (Commission Foundation): "tiered" added.
  rate_type:   "percentage" | "flat_amount" | "tiered";
  rate_value:  string;
  is_active:   boolean;
  tiers:       CommissionTier[];
  created_at:  string;
  updated_at:  string;
}

export interface CommissionPolicyResponse {
  success: boolean;
  policy:  CommissionPolicy;
}

export interface UpdateCommissionPolicyPayload {
  rate_type?:  CommissionPolicy["rate_type"];
  rate_value?: string;
  is_active?:  boolean;
}

export interface Commission {
  id:              string;
  booking:         string;
  booking_spr:     string;
  unit_number:     string | null;
  agent:           string;
  agent_name:      string;
  agent_email:     string;
  amount:          string;
  status:          "pending" | "earned" | "paid";
  status_display:  string;
  computed_at:     string;
  updated_at:      string;
}

export interface CommissionListResponse {
  success: boolean;
  count:   number;
  results: Commission[];
}

export interface CommissionDetailResponse {
  success:    boolean;
  commission: Commission;
}

export const commissionPolicyApi = {
  async get(): Promise<CommissionPolicy> {
    const { data } = await api.get<CommissionPolicyResponse>("/api/commissions/policy/");
    return data.policy;
  },

  async update(payload: UpdateCommissionPolicyPayload): Promise<CommissionPolicy> {
    const { data } = await api.put<CommissionPolicyResponse>("/api/commissions/policy/", payload);
    return data.policy;
  },
};

export const commissionsApi = {
  async list(params?: { status?: string }): Promise<Commission[]> {
    const { data } = await api.get<CommissionListResponse>("/api/commissions/", { params });
    return data.results;
  },

  async get(id: string): Promise<Commission> {
    const { data } = await api.get<CommissionDetailResponse>(`/api/commissions/${id}/`);
    return data.commission;
  },

  async updateStatus(id: string, newStatus: Commission["status"]): Promise<Commission> {
    const { data } = await api.put<CommissionDetailResponse>(
      `/api/commissions/${id}/`,
      { status: newStatus }
    );
    return data.commission;
  },
};

// =============================================================================
// Sprint 2 (Commission Foundation): Commission Tiers
// =============================================================================

export interface CommissionTierListResponse {
  success: boolean;
  count:   number;
  results: CommissionTier[];
}

export interface CommissionTierDetailResponse {
  success: boolean;
  tier:    CommissionTier;
}

export interface CreateCommissionTierPayload {
  min_amount:  string;
  max_amount:  string | null;
  rate_value:  string;
}

export const commissionTiersApi = {
  async list(): Promise<CommissionTier[]> {
    const { data } = await api.get<CommissionTierListResponse>("/api/commissions/policy/tiers/");
    return data.results;
  },

  async create(payload: CreateCommissionTierPayload): Promise<CommissionTier> {
    const { data } = await api.post<CommissionTierDetailResponse>(
      "/api/commissions/policy/tiers/", payload
    );
    return data.tier;
  },

  async update(id: string, payload: Partial<CreateCommissionTierPayload>): Promise<CommissionTier> {
    const { data } = await api.put<CommissionTierDetailResponse>(
      `/api/commissions/policy/tiers/${id}/`, payload
    );
    return data.tier;
  },

  async remove(id: string): Promise<void> {
    await api.delete(`/api/commissions/policy/tiers/${id}/`);
  },
};
