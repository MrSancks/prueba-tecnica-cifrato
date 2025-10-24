import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginRequest, meRequest } from '../services/apiClient';

interface AuthContextState {
  token: string | null;
  userEmail: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextState | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const navigate = useNavigate();
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('auth_token'));
  const [userEmail, setUserEmail] = useState<string | null>(() => localStorage.getItem('auth_email'));

  useEffect(() => {
    if (!token) {
      return;
    }

    meRequest(token)
      .then((user) => {
        setUserEmail(user.email);
        localStorage.setItem('auth_email', user.email);
      })
      .catch(() => {
        setToken(null);
        setUserEmail(null);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_email');
      });
  }, [token]);

  const login = useCallback(
    async (email: string, password: string) => {
      const result = await loginRequest(email, password);
      setToken(result.access_token);
      setUserEmail(email);
      localStorage.setItem('auth_token', result.access_token);
      localStorage.setItem('auth_email', email);
      navigate('/', { replace: true });
    },
    [navigate]
  );

  const logout = useCallback(() => {
    setToken(null);
    setUserEmail(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_email');
    navigate('/login', { replace: true });
  }, [navigate]);

  const value = useMemo(
    () => ({
      token,
      userEmail,
      isAuthenticated: Boolean(token),
      login,
      logout
    }),
    [token, userEmail, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
