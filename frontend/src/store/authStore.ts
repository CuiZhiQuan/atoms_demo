import { create } from 'zustand';

export interface User {
  id: string;
  username: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  setAuth: (user: User, token: string) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
}

const TOKEN_KEY = 'atoms_token';

function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getToken(): string | null {
  return getStoredToken();
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: getStoredToken(),
  isAuthenticated: false,
  isLoading: true,

  setAuth: (user, token) => {
    localStorage.setItem(TOKEN_KEY, token);
    set({ user, token, isAuthenticated: true, isLoading: false });
  },

  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    set({ user: null, token: null, isAuthenticated: false, isLoading: false });
  },

  setLoading: (loading) => set({ isLoading: loading }),
}));