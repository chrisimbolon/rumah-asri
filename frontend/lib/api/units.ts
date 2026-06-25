// =============================================================================
// === frontend/lib/api/units.ts ===
// =============================================================================
/**
 * DevelopIndo — Units API
 * Updated for Sprint 6: Tambah Unit + Booking flow
 */
import api from "@/lib/api";

export interface Booking {
  id:             string;
  spr_number:     string;
  booking_fee:    number;
  booking_date:   string;
  payment_method: string;
  bank:           string;
  status:         "active" | "cancelled" | "converted";
  status_display: string;
  notes:          string;
  buyer:          string;
  buyer_name:     string;
  buyer_email:    string;
  unit_number:    string;
  created_at:     string;
}

export interface Unit {
  id:                string;
  unit_number:       string;
  unit_type:         string;
  land_area:         string;
  building_area:     string;
  price:             number;
  status:            "tersedia" | "dipesan" | "proses" | "terjual" | "serah_terima";
  status_display:    string;
  progress:          number;
  current_phase:     string;
  target_completion: string | null;
  payment_method:    string;
  bank:              string;
  project:           string;
  project_name:      string;
  buyer:             string | null;
  buyer_name:        string | null;
  buyer_email:       string | null;
  booking:           Booking | null;
  created_at:        string;
}

export interface CreateUnitPayload {
  project:            string;
  unit_number:        string;
  unit_type:          string;
  land_area:          number;
  building_area:      number;
  price:              number;
  status?:            string;
  target_completion?: string;
  payment_method?:    string;
  bank?:              string;
}

export interface BookingPayload {
  buyer_id:       string;
  booking_fee:    number;
  booking_date?:  string;
  payment_method?: string;
  bank?:          string;
  notes?:         string;
}

export const UNIT_TYPE_OPTIONS = [
  "Tipe 21", "Tipe 36", "Tipe 45", "Tipe 54",
  "Tipe 60", "Tipe 72", "Tipe 90", "Tipe 120",
];

export const unitsApi = {
  async list(params?: { project?: string; status?: string }): Promise<Unit[]> {
    const { data } = await api.get("/api/units/", { params });
    return data.results;
  },

  async get(id: string): Promise<Unit> {
    const { data } = await api.get(`/api/units/${id}/`);
    return data.unit;
  },

  async create(payload: CreateUnitPayload): Promise<Unit> {
    const { data } = await api.post("/api/units/", payload);
    return data.unit;
  },

  async update(id: string, payload: Partial<CreateUnitPayload>): Promise<Unit> {
    const { data } = await api.put(`/api/units/${id}/`, payload);
    return data.unit;
  },

  async book(unitId: string, payload: BookingPayload): Promise<{ unit: Unit; booking: Booking; message: string }> {
    const { data } = await api.post(`/api/units/${unitId}/book/`, payload);
    return data;
  },

  async cancelBooking(bookingId: string, reason?: string): Promise<Unit> {
    const { data } = await api.post(
      `/api/units/bookings/${bookingId}/cancel/`,
      { reason: reason ?? "" }
    );
    return data.unit;
  },
};
