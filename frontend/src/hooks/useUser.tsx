import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import type { StoredUser } from '@/types';

const USER_STORAGE_KEY = 'user';

interface UserContextValue {
  user: StoredUser | null;
  setUser: (user: StoredUser) => void;
  clearUser: () => void;
}

const UserContext = createContext<UserContextValue | null>(null);

/** Persists user to localStorage and provides it via context. */
export function UserProvider({ children }: { children: ReactNode }): JSX.Element {
  const [user, setUserState] = useState<StoredUser | null>(() => {
    const stored = localStorage.getItem(USER_STORAGE_KEY);
    if (!stored) return null;
    try {
      return JSON.parse(stored) as StoredUser;
    } catch {
      return null;
    }
  });

  const setUser = useCallback((newUser: StoredUser) => {
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(newUser));
    setUserState(newUser);
  }, []);

  const clearUser = useCallback(() => {
    localStorage.removeItem(USER_STORAGE_KEY);
    setUserState(null);
  }, []);

  return <UserContext.Provider value={{ user, setUser, clearUser }}>{children}</UserContext.Provider>;
}

/** Returns the current user context. Must be used within UserProvider. */
export function useUser(): UserContextValue {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error('useUser must be used within a UserProvider');
  return ctx;
}


