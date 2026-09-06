import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { api, getToken, setToken, onUnauthorized } from "./api";
import type { AuthUser } from "./types";

interface AuthState {
  ready: boolean;
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

function readToken(payload: Record<string, unknown> | undefined): string | null {
  if (!payload) return null;
  for (const key of ["access_token", "token", "accessToken", "jwt"]) {
    const value = payload[key];
    if (typeof value === "string" && value) return value;
  }
  return null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);

  const clear = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  // Restore the session on load (token lives in localStorage).
  useEffect(() => {
    let cancelled = false;
    const token = getToken();
    if (!token) {
      setReady(true);
      return;
    }
    api
      .me()
      .then((data) => {
        if (!cancelled) setUser((data as AuthUser) ?? {});
      })
      .catch(() => {
        if (!cancelled) clear();
      })
      .finally(() => {
        if (!cancelled) setReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, [clear]);

  // Any 401 from the backend ends the session.
  useEffect(() => onUnauthorized(clear), [clear]);

  const login = useCallback(async (email: string, password: string) => {
    const data = await api.login(email, password);
    const token = readToken(data);
    if (!token) {
      throw new Error("Sign-in succeeded but no access token was returned by the service.");
    }
    setToken(token);
    const me = await api.me();
    setUser((me as AuthUser) ?? {});
  }, []);

  const register = useCallback(
    async (email: string, password: string) => {
      await api.register(email, password);
      await login(email, password);
    },
    [login],
  );

  const value = useMemo<AuthState>(
    () => ({
      ready,
      user,
      isAuthenticated: !!user,
      login,
      register,
      logout: clear,
    }),
    [ready, user, login, register, clear],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
