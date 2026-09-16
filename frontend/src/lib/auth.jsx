import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api, setAuthToken, ApiError } from './api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const restoreSession = useCallback(async () => {
    const stored = localStorage.getItem('evidence_desk_token');
    if (!stored) {
      setLoading(false);
      return;
    }
    setAuthToken(stored);
    try {
      const me = await api.me();
      setUser({ ...me, token: stored });
    } catch {
      localStorage.removeItem('evidence_desk_token');
      setAuthToken(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  async function login(email, password) {
    const res = await api.login(email, password);
    localStorage.setItem('evidence_desk_token', res.access_token);
    setAuthToken(res.access_token);
    const me = await api.me();
    setUser({ ...me, token: res.access_token });
    return me;
  }

  async function register(email, password) {
    await api.register(email, password);
    return login(email, password);
  }

  function logout() {
    localStorage.removeItem('evidence_desk_token');
    setAuthToken(null);
    setUser(null);
  }

  const canReview = user && (user.role === 'reviewer' || user.role === 'admin');
  const isAdmin = user && user.role === 'admin';

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, canReview, isAdmin }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export { ApiError };