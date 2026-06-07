/**
 * utils/api.js  –  Pre-configured Axios instance.
 * Automatically attaches JWT token from localStorage on every request.
 */
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api/v1",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT on every request
api.interceptors.request.use((config) => {
  try {
    const stored = JSON.parse(localStorage.getItem("sevasetu-store") || "{}");
    const token  = stored?.state?.token;
    if (token) config.headers.Authorization = `Bearer ${token}`;
  } catch (_) {}
  return config;
});

// Global error handler
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      // Clear stale session
      localStorage.removeItem("sevasetu-store");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;
