// =============================================================================
// === frontend/lib/api/commissions.ts ===
// =============================================================================
/**
 * DevelopIndo — Commission API
 * Commission Foundation Sprint 1 (flat rate only).
 */

import api from "@/lib/api";

export interface CommissionPolicy {
  id:          string;
  rate_type:   "percentage" | "flat_amount";
  rate_value:  string;
  is_active:   boolean;
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
