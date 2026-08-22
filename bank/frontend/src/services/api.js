import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : "/api";

const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth ──
export const register = (data) => api.post("/auth/register", data);
export const login = (data) => api.post("/auth/login", data);
export const logout = () => api.post("/auth/logout");

// ── User ──
export const getProfile = () => api.get("/user/profile");
export const updateProfile = (data) => api.put("/user/profile", data);
export const changePassword = (data) => api.post("/user/change-password", data);
export const getTransactions = (params) => api.get("/user/transactions", { params });
export const getLoginHistory = (params) => api.get("/user/login-history", { params });

// ── Transactions ──
export const createTransfer = (data) => api.post("/transactions/transfer", data);

// ── Admin ──
export const adminLogin = (data) => api.post("/admin/login", data);
export const getAdminUsers = (params) => api.get("/admin/users", { params });
export const getAdminTransactions = (params) => api.get("/admin/transactions", { params });
export const getAdminSecurityEvents = (params) => api.get("/admin/security-events", { params });
export const getAdminLoginActivity = (params) => api.get("/admin/login-activity", { params });
export const getAdminStats = () => api.get("/admin/stats");
export const toggleUserStatus = (userId) => api.post(`/admin/users/${userId}/toggle-status`);

// ── Security Events (public SIEM endpoint) ──
export const getSecurityEvents = (params) => api.get("/security-events", { params });

// ── Health ──
export const getHealth = () => api.get("/health");

export default api;
