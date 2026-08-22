import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('siem_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('siem_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      if (token) {
        try {
          const res = await api.get('/auth/me');
          setUser(res.data.user);
          localStorage.setItem('siem_user', JSON.stringify(res.data.user));
        } catch (err) {
          logout();
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, [token]);

  const login = async (username, password) => {
    const res = await api.post('/auth/login', { username, password });
    const { token: jwtToken, user: userData } = res.data;
    setToken(jwtToken);
    setUser(userData);
    localStorage.setItem('siem_token', jwtToken);
    localStorage.setItem('siem_user', JSON.stringify(userData));
    return userData;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('siem_token');
    localStorage.removeItem('siem_user');
  };

  const hasRole = (roles) => {
    if (!user) return false;
    if (user.role === 'Admin') return true;
    if (Array.isArray(roles)) return roles.includes(user.role);
    return user.role === roles;
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, hasRole, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
