import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { getProfile } from "../services/api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Validate token against backend on initialization
  useEffect(() => {
    const token = localStorage.getItem("token");
    const storedUser = localStorage.getItem("user");

    if (!token || !storedUser) {
      // No token stored — definitely unauthenticated
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      setLoading(false);
      return;
    }

    // Token exists — parse stored user data first for immediate rendering,
    // then validate against backend
    let parsedUser;
    try {
      parsedUser = JSON.parse(storedUser);
    } catch {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      setLoading(false);
      return;
    }

    // Optimistically set user so ProtectedRoute can render while we validate
    setUser(parsedUser);

    // Validate the token against the backend
    getProfile()
      .then((res) => {
        // Token is valid — update user data from backend (may have changed)
        setUser(res.data);
        localStorage.setItem("user", JSON.stringify(res.data));
      })
      .catch(() => {
        // Token is invalid, expired, or user deleted — clear everything
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const loginUser = useCallback((token, userData) => {
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
  }, []);

  const logoutUser = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const res = await getProfile();
      localStorage.setItem("user", JSON.stringify(res.data));
      setUser(res.data);
    } catch {
      // Token expired — clear auth
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, loginUser, logoutUser, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
}
