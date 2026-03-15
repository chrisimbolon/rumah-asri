/**
 * RumahAsri — Auth Helper Functions
 * Token storage, user management, role checks
 */

import api from "./api";

// ── Types ─────────────────────────────────────────────────────
export type UserRole =
  | "super_admin"
  | "developer"
  | "agent"
  | "buyer";

export interface AuthUser {
  id:           string;
  email:        string;
  full_name:    string;
  phone:        string;
  role:         UserRole;
  role_display: string;
  is_active:    boolean;
  created_at:   string;
}

export interface LoginPayload {
  email:    string;
  password: string;
}

export interface RegisterPayload {
  email:     string;
  full_name: string;
  phone?:    string;
  password:  string;
  password2: string;
  role:      "developer" | "buyer";
}

export interface AuthResponse {
  success:  boolean;
  message:  string;
  access:   string;
  refresh:  string;
  user:     AuthUser;
}

// ── Token storage ─────────────────────────────────────────────
export const tokenStorage = {
  set(access: string, refresh: string, user: AuthUser) {
    localStorage.setItem("access_token",  access);
    localStorage.setItem("refresh_token", refresh);
    localStorage.setItem("user",          JSON.stringify(user));
    // Also set cookie so proxy.ts can read it!!
    document.cookie = `access_token=${access}; path=/; max-age=3600; SameSite=Lax`;
  },

  clear() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    // Also clear the cookie!!
    document.cookie = "access_token=; path=/; max-age=0";
  },

  getAccess():  string | null { return localStorage.getItem("access_token");  },
  getRefresh(): string | null { return localStorage.getItem("refresh_token"); },

  getUser(): AuthUser | null {
    const raw = localStorage.getItem("user");
    if (!raw) return null;
    try { return JSON.parse(raw) as AuthUser; }
    catch { return null; }
  },

  isLoggedIn(): boolean {
    return !!localStorage.getItem("access_token");
  },
};
// ── API calls ─────────────────────────────────────────────────
export const authApi = {
  async login(payload: LoginPayload): Promise<AuthResponse> {
    const { data } = await api.post<AuthResponse>(
      "/api/auth/login/",
      payload
    );
    return data;
  },

  async register(payload: RegisterPayload): Promise<AuthResponse> {
    const { data } = await api.post<AuthResponse>(
      "/api/auth/register/",
      payload
    );
    return data;
  },

  async logout(refreshToken: string): Promise<void> {
    try {
      await api.post("/api/auth/logout/", { refresh: refreshToken });
    } catch {
      // Even if logout API fails, clear local storage
    } finally {
      tokenStorage.clear();
    }
  },

  async me(): Promise<AuthUser> {
    const { data } = await api.get<{ success: boolean; user: AuthUser }>(
      "/api/auth/me/"
    );
    return data.user;
  },
};

// ── Role-based redirect helper ────────────────────────────────
export function getRedirectPath(role: UserRole): string {
  switch (role) {
    case "super_admin": return "/dashboard";
    case "developer":   return "/dashboard";
    case "agent":       return "/dashboard/sales";
    case "buyer":       return "/buyer";
    default:            return "/dashboard";
  }
}

// ── Role display helper ───────────────────────────────────────
export function getRoleLabel(role: UserRole): string {
  const labels: Record<UserRole, string> = {
    super_admin: "Super Admin",
    developer:   "Developer / Admin",
    agent:       "Agen Penjualan",
    buyer:       "Pembeli",
  };
  return labels[role] ?? role;
}
