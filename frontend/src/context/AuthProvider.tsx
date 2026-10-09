import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { getMeApi } from "../api/authApi";
import type { User } from "../types/auth";
import { AuthContext } from "./authContext";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("lumiere_token"));
  const [user, setUser] = useState<User | null>(() => {
    const raw = localStorage.getItem("lumiere_user");
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  });

  const login = useCallback((newToken: string, newUser: User) => {
    localStorage.setItem("lumiere_token", newToken);
    localStorage.setItem("lumiere_user", JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("lumiere_token");
    localStorage.removeItem("lumiere_user");
    setToken(null);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!token) return;
    try {
      const me = await getMeApi();
      setUser(me);
      localStorage.setItem("lumiere_user", JSON.stringify(me));
    } catch {
      // Token might be invalid or expired
      logout();
    }
  }, [token, logout]);

  useEffect(() => {
    if (token && !user) {
      refreshUser();
    }
  }, [token, user, refreshUser]);

  const value = useMemo(
    () => ({
      user,
      token,
      role: user?.role ?? null,
      isAuthenticated: Boolean(token && user),
      isOwner: user?.role === "shopowner",
      isCustomer: user?.role === "customer",
      login,
      logout,
      refreshUser,
    }),
    [user, token, login, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
