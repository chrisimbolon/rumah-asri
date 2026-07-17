// =============================================================================
// === frontend/lib/api/organizations.ts ===
// =============================================================================
/**
 * DevelopIndo — Organizations API
 */
import api from "@/lib/api";

export interface OrgMemberUser {
  id:        string;
  email:     string;
  full_name: string;
  role:      string;
  is_active: boolean;
}

export interface OrgMembership {
  id:         string;
  user:       OrgMemberUser;
  role:       string;
  is_active:  boolean;
  created_at: string;
}

export interface Organization {
  id:            string;
  name:          string;
  plan:          string;
  is_active:     boolean;
  member_count:  number;
  project_count: number;
  created_at:    string;
}

export interface OrganizationDetail extends Organization {
  memberships: OrgMembership[];
}

export interface OrgListResponse {
  success: boolean;
  count:   number;
  results: Organization[];
}

export interface MyOrgResponse {
  success:      boolean;
  organization: Organization;
  role:         string;
}

export interface OrgDetailResponse {
  success:      boolean;
  organization: OrganizationDetail;
}

// Agent-picker fix (CRM Foundation): used by the Prospect assignment
// dropdown. Deliberately org-scoped, unlike BuyerListView's own
// platform-wide behavior — see AgentListView's docstring on the
// backend for why that distinction is real, not an oversight.
export interface OrgAgentSummary {
  id:        string;
  full_name: string;
  email:     string;
  role:      string;
}

export interface OrgAgentListResponse {
  success: boolean;
  count:   number;
  results: OrgAgentSummary[];
}

export const organizationsApi = {
  async list(): Promise<Organization[]> {
    const { data } = await api.get<OrgListResponse>("/api/organizations/");
    return data.results;
  },

  async mine(): Promise<MyOrgResponse> {
    const { data } = await api.get<MyOrgResponse>("/api/organizations/mine/");
    return data;
  },

  async get(id: string): Promise<OrganizationDetail> {
    const { data } = await api.get<OrgDetailResponse>(`/api/organizations/${id}/`);
    return data.organization;
  },

  async agents(): Promise<OrgAgentSummary[]> {
    const { data } = await api.get<OrgAgentListResponse>("/api/organizations/agents/");
    return data.results;
  },
};
