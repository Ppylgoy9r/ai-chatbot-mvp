/**
 * Auth Context — provides user state and login/logout across the app.
 */

import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { auth as authApi } from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const userData = await authApi.me();
      setUser(userData);
    } catch {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = async (username, password) => {
    await authApi.login(username, password);
    await loadUser();
  };

  const logout = () => {
    authApi.logout();
    setUser(null);
  };

  const register = async (data) => {
    await authApi.register(data);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register, isAuthenticated: !!user, isAdmin: user?.role === "admin" }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
}
