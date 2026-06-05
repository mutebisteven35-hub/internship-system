import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api, getToken, setToken } from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(getToken()));

  useEffect(() => {
    if (!getToken()) return;
    api
      .me()
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  async function login(username, password) {
    const data = await api.login(username, password);
    setToken(data.token);
    setUser(data.user);
  }

  function loginWithToken(token, nextUser) {
    setToken(token);
    setUser(nextUser);
  }

  async function logout() {
    try {
      await api.logout();
    } catch {
      // Local logout still matters if the token was already invalidated.
    }
    setToken(null);
    setUser(null);
  }

  const value = useMemo(() => ({ user, loading, login, loginWithToken, logout }), [user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
