import { useState, useEffect, useCallback } from 'react';
import type { Loan } from '@/types';

/**
 * Fetches all loans for the given user from the Loan Service.
 * Returns an empty list when userId is null (user not logged in).
 */
export function useLoans(userId: string | null): {
  loans: Loan[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
} {
  const [loans, setLoans] = useState<Loan[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState<number>(0);

  const refresh = useCallback(() => setRefreshTick((t) => t + 1), []);

  useEffect(() => {
    if (!userId) {
      setLoans([]);
      setLoading(false);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    fetch(`/api/loan/loans?user_id=${encodeURIComponent(userId)}`)
      .then(async (res) => {
        if (!res.ok) {
          let msg = 'Failed to fetch loans';
          try {
            const data = await res.json() as { error?: string };
            if (data.error) msg = data.error;
          } catch {
            // ignore parse errors
          }
          throw new Error(msg);
        }
        return res.json() as Promise<{ items: Loan[] }>;
      })
      .then((data) => setLoans(data.items ?? []))
      .catch((e: Error) => {
        setLoans([]);
        setError(e.message);
      })
      .finally(() => setLoading(false));
  }, [userId, refreshTick]);

  return { loans, loading, error, refresh };
}

