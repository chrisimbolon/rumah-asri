"use client";

/**
 * RumahAsri — Auth Context
 * Global authentication state — wraps the entire app
 * Provides: user, isLoading, login, logout, isAuthenticated
 */

import {
  AuthUser,
  LoginPayload,
  RegisterPayload,
  authApi,
  getRedirectPath,
  tokenStorage,
} from "@/lib/auth";
import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

// ── Context shape ─────────────────────────────────────────────
interface AuthContextType {
  user:            AuthUser | null;
  isLoading:       boolean;
  isAuthenticated: boolean;
  login:           (payload: LoginPayload) => Promise<void>;
  register:        (payload: RegisterPayload) => Promise<void>;
  logout:          () => Promise<void>;
  error:           string | null;
  clearError:      () => void;
}

// ── Create context ────────────────────────────────────────────
const AuthContext = createContext<AuthContextType | null>(null);

// ── Provider ──────────────────────────────────────────────────
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user,      setUser]      = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error,     setError]     = useState<string | null>(null);

  // ── On mount — restore user from localStorage ─────────────
  useEffect(() => {
    const storedUser = tokenStorage.getUser();
    if (storedUser && tokenStorage.isLoggedIn()) {
      setUser(storedUser);
    }
    setIsLoading(false);
  }, []);

  // ── Login ─────────────────────────────────────────────────
  const login = useCallback(async (payload: LoginPayload) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await authApi.login(payload);

      // Store tokens + user in localStorage AND cookie
      tokenStorage.set(response.access, response.refresh, response.user);
      setUser(response.user);

      // Full page navigation — proxy.ts picks up the cookie!!
      const redirectTo = getRedirectPath(response.user.role);
      window.location.href = redirectTo;

    } catch (err: unknown) {
      const axiosError = err as {
        response?: { data?: { errors?: { non_field_errors?: string[] } } };
      };
      const msg =
        axiosError.response?.data?.errors?.non_field_errors?.[0] ??
        "Login gagal. Periksa email dan kata sandi Anda.";
      setError(msg);
      setIsLoading(false);
    }
  }, []);

  // ── Register ──────────────────────────────────────────────
  const register = useCallback(async (payload: RegisterPayload) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await authApi.register(payload);

      // Store tokens + user in localStorage AND cookie
      tokenStorage.set(response.access, response.refresh, response.user);
      setUser(response.user);

      // Full page navigation — proxy.ts picks up the cookie!!
      const redirectTo = getRedirectPath(response.user.role);
      window.location.href = redirectTo;

    } catch (err: unknown) {
      const axiosError = err as {
        response?: { data?: { errors?: Record<string, string[]> } };
      };
      const errors = axiosError.response?.data?.errors;
      if (errors) {
        const firstError = Object.values(errors).flat()[0];
        setError(firstError ?? "Pendaftaran gagal. Coba lagi.");
      } else {
        setError("Pendaftaran gagal. Coba lagi.");
      }
      setIsLoading(false);
    }
  }, []);

  // ── Logout ────────────────────────────────────────────────
  const logout = useCallback(async () => {
    setIsLoading(true);

    const refreshToken = tokenStorage.getRefresh();
    if (refreshToken) {
      await authApi.logout(refreshToken);
    } else {
      tokenStorage.clear();
    }

    setUser(null);

    // Full page navigation — proxy.ts sees cookie is gone!!
    window.location.href = "/login";
  }, []);

  // ── Clear error ───────────────────────────────────────────
  const clearError = useCallback(() => setError(null), []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        error,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ── Hook ──────────────────────────────────────────────────────
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }
  return context;
}
