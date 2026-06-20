// =============================================================================
// === frontend/lib/api/payments.ts ===
// =============================================================================
/**
 * DevelopIndo — Payments API
 */

import api from "@/lib/api";

export interface Payment {
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

export interface PaymentListResponse {
  success: boolean;
  count:   number;
  results: Payment[];
}

export interface PaymentDetailResponse {
  success: boolean;
  payment: Payment;
}

export interface CreatePaymentPayload {
  unit:         string;
  payment_type: string;
  due_date:     string;
  amount:       number;
  status?:      string;
  bank?:        string;
}

export const paymentsApi = {
  async list(params?: { status?: string }): Promise<Payment[]> {
    const { data } = await api.get<PaymentListResponse>("/api/payments/", {
      params,
    });
    return data.results;
  },

  async get(id: string): Promise<Payment> {
    const { data } = await api.get<PaymentDetailResponse>(
      `/api/payments/${id}/`
    );
    return data.payment;
  },

  async create(payload: CreatePaymentPayload): Promise<Payment> {
    const { data } = await api.post<PaymentDetailResponse>(
      "/api/payments/",
      payload
    );
    return data.payment;
  },

  async update(id: string, payload: Partial<CreatePaymentPayload>): Promise<Payment> {
    const { data } = await api.put<PaymentDetailResponse>(
      `/api/payments/${id}/`,
      payload
    );
    return data.payment;
  },
};
