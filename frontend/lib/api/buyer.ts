/**
 * RumahAsri — Buyer API
 * All frontend API calls for the Buyer Portal
 * Connects to Django /api/buyer/* endpoints
 */

import api from "@/lib/api";

// ── Types ─────────────────────────────────────────────────────

export interface BuyerInfo {
  id:        string;
  full_name: string;
  email:     string;
  phone:     string;
}

export interface ProjectInfo {
  id:       string;
  name:     string;
  location: string;
  status:   string;
}

export interface UnitInfo {
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
  project_name:       string;
}

export interface BuyerMeResponse {
  success:  boolean;
  buyer:    BuyerInfo;
  unit:     UnitInfo;
  project:  ProjectInfo;
}

export interface ConstructionPhase {
  id:             string;
  phase_order:    number;
  phase_name:     string;
  phase_date:     string;
  status:         "selesai" | "proses" | "menunggu";
  status_display: string;
  notes:          string;
  updated_by_name:string;
  photos:         ConstructionPhoto[];
  created_at:     string;
  updated_at:     string;
}

export interface ConstructionPhoto {
  id:              string;
  image:           string;
  caption:         string;
  uploaded_by_name:string;
  uploaded_at:     string;
}

export interface BuyerTimelineResponse {
  success:       boolean;
  unit_number:   string;
  progress:      number;
  done_count:    number;
  total_phases:  number;
  current_phase: string;
  phases:        ConstructionPhase[];
}

export interface PaymentRecord {
  id:             string;
  payment_type:   string;
  due_date:       string;
  amount:         number;
  status:         string;
  status_display: string;
  bank:           string;
  unit_number:    string;
  buyer_name:     string;
  paid_at:        string | null;
  created_at:     string;
}

export interface BuyerPaymentsResponse {
  success:        boolean;
  unit_number:    string;
  payment_method: string;
  bank:           string;
  total_amount:   number;
  paid_amount:    number;
  overdue_count:  number;
  total_count:    number;
  payments:       PaymentRecord[];
}

export interface DocumentRecord {
  id:               string;
  name:             string;
  doc_type:         string;
  doc_type_display: string;
  status:           string;
  status_display:   string;
  file:             string | null;
  file_url:         string | null;
  issued_date:      string;
  unit_number:      string;
  created_at:       string;
}

export interface BuyerDocumentsResponse {
  success:         boolean;
  unit_number:     string;
  total_documents: number;
  available_count: number;
  documents:       DocumentRecord[];
}

// ── API calls ─────────────────────────────────────────────────

export const buyerApi = {
  /**
   * GET /api/buyer/me/
   * Returns the buyer's unit, project and personal info
   */
  async getMe(): Promise<BuyerMeResponse> {
    const { data } = await api.get<BuyerMeResponse>("/api/buyer/me/");
    return data;
  },

  /**
   * GET /api/buyer/timeline/
   * Returns the 7-phase construction timeline
   */
  async getTimeline(): Promise<BuyerTimelineResponse> {
    const { data } = await api.get<BuyerTimelineResponse>(
      "/api/buyer/timeline/"
    );
    return data;
  },

  /**
   * GET /api/buyer/payments/
   * Returns payment schedule and status
   */
  async getPayments(): Promise<BuyerPaymentsResponse> {
    const { data } = await api.get<BuyerPaymentsResponse>(
      "/api/buyer/payments/"
    );
    return data;
  },

  /**
   * GET /api/buyer/documents/
   * Returns all documents for the buyer's unit
   */
  async getDocuments(): Promise<BuyerDocumentsResponse> {
    const { data } = await api.get<BuyerDocumentsResponse>(
      "/api/buyer/documents/"
    );
    return data;
  },
};