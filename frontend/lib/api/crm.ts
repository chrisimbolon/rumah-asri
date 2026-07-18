// =============================================================================
// === frontend/lib/api/crm.ts ===
// =============================================================================
/**
 * DevelopIndo — CRM (Prospect) API
 * Sprint 3: Prospect list, follow-up, and conversion hand-off. - prospects need to be changed to LEAD
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
  // Sprint 5 (CRM Foundation Phase B): expanded from the original
  // 4 values. BOOKING deliberately excluded — see Decision 1 in the
  // Phase B roadmap; "Won" already implies a real Booking exists.
  status:               "lead" | "qualified" | "follow_up" | "site_visit" | "negotiation" | "won" | "lost";
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

// =============================================================================
// Sprint 4 (CRM Foundation Phase B): Activity Timeline
// =============================================================================

export interface Activity {
  id:                     string;
  activity_type:          "call" | "whatsapp" | "meeting" | "note";
  activity_type_display:  string;
  notes:                  string;
  created_by:             string | null;
  created_by_name:        string | null;
  created_at:             string;
}

export interface ActivityListResponse {
  success: boolean;
  count:   number;
  results: Activity[];
}

export interface ActivityDetailResponse {
  success:  boolean;
  activity: Activity;
}

export interface CreateActivityPayload {
  activity_type: Activity["activity_type"];
  notes?:        string;
}

export const activitiesApi = {
  async list(prospectId: string): Promise<Activity[]> {
    const { data } = await api.get<ActivityListResponse>(
      `/api/prospects/${prospectId}/activities/`
    );
    return data.results;
  },

  async create(prospectId: string, payload: CreateActivityPayload): Promise<Activity> {
    const { data } = await api.post<ActivityDetailResponse>(
      `/api/prospects/${prospectId}/activities/`,
      payload
    );
    return data.activity;
  },
};

// =============================================================================
// Sprint 6 (CRM Foundation Phase B): Site Visit Scheduling
// =============================================================================

export interface SiteVisit {
  id:                string;
  unit:              string | null;
  unit_number:       string | null;
  scheduled_at:      string;
  status:            "scheduled" | "completed" | "no_show" | "cancelled";
  status_display:    string;
  notes:             string;
  created_by:        string | null;
  created_by_name:   string | null;
  created_at:        string;
}

export interface SiteVisitListResponse {
  success: boolean;
  count:   number;
  results: SiteVisit[];
}

export interface SiteVisitDetailResponse {
  success:    boolean;
  site_visit: SiteVisit;
}

export interface CreateSiteVisitPayload {
  unit?:         string | null;
  scheduled_at:  string;
  notes?:        string;
}

export interface UpdateSiteVisitPayload {
  status?:       SiteVisit["status"];
  scheduled_at?: string;
  notes?:        string;
}

export const siteVisitsApi = {
  async list(prospectId: string): Promise<SiteVisit[]> {
    const { data } = await api.get<SiteVisitListResponse>(
      `/api/prospects/${prospectId}/site-visits/`
    );
    return data.results;
  },

  async create(prospectId: string, payload: CreateSiteVisitPayload): Promise<SiteVisit> {
    const { data } = await api.post<SiteVisitDetailResponse>(
      `/api/prospects/${prospectId}/site-visits/`,
      payload
    );
    return data.site_visit;
  },

  async update(prospectId: string, visitId: string, payload: UpdateSiteVisitPayload): Promise<SiteVisit> {
    const { data } = await api.put<SiteVisitDetailResponse>(
      `/api/prospects/${prospectId}/site-visits/${visitId}/`,
      payload
    );
    return data.site_visit;
  },
};

// =============================================================================
// Sprint 8 (CRM Foundation Phase B): Customer Profile
// Deliberately a separate top-level resource — /api/customers/, not
// nested under /api/prospects/ — same reasoning apps/crm/customer_urls.py
// documents on the backend: a customer isn't owned by any one prospect.
// =============================================================================

export interface CustomerProfile {
  id:              string;
  user:            string;
  user_name:       string;
  user_email:      string;
  budget:          number | null;
  family_notes:    string;
  timeline_notes:  string;
  unit_number:     string | null;
  project_name:    string | null;
  created_at:      string;
  updated_at:      string;
}

export interface CustomerProfileListResponse {
  success: boolean;
  count:   number;
  results: CustomerProfile[];
}

export interface CustomerProfileDetailResponse {
  success:  boolean;
  customer: CustomerProfile;
}

export interface UpdateCustomerProfilePayload {
  budget?:          number | null;
  family_notes?:    string;
  timeline_notes?:  string;
}

export const customerProfilesApi = {
  async list(): Promise<CustomerProfile[]> {
    const { data } = await api.get<CustomerProfileListResponse>("/api/customers/");
    return data.results;
  },

  async get(id: string): Promise<CustomerProfile> {
    const { data } = await api.get<CustomerProfileDetailResponse>(`/api/customers/${id}/`);
    return data.customer;
  },

  async update(id: string, payload: UpdateCustomerProfilePayload): Promise<CustomerProfile> {
    const { data } = await api.put<CustomerProfileDetailResponse>(`/api/customers/${id}/`, payload);
    return data.customer;
  },
};
