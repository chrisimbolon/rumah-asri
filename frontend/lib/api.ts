/**
 * RumahAsri — Axios API Instance
 * Handles JWT token attachment + auto-refresh on 401
 */

import axios from "axios";

// ── Base URL ──────────────────────────────────────────────────
const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Create axios instance ─────────────────────────────────────
const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 10000,
});

// ── Request interceptor — attach access token ─────────────────
api.interceptors.request.use(
  (config) => {
    // Only runs in browser
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response interceptor — auto refresh on 401 ───────────────
api.interceptors.response.use(
  // Success — pass through
  (response) => response,

  // Error — check if 401 and try refresh
  async (error) => {
    const originalRequest = error.config;

    // If 401 and we haven't retried yet
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      typeof window !== "undefined"
    ) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem("refresh_token");

      if (!refreshToken) {
        // No refresh token — clear storage and redirect to login
        localStorage.clear();
        window.location.href = "/login";
        return Promise.reject(error);
      }

      try {
        // Try to get a new access token
        const { data } = await axios.post(
          `${BASE_URL}/api/auth/refresh/`,
          { refresh: refreshToken }
        );

        // Save the new access token
        localStorage.setItem("access_token", data.access);

        // Retry the original request with new token
        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        return api(originalRequest);

      } catch (refreshError) {
        // Refresh failed — clear everything and redirect
        localStorage.clear();
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
