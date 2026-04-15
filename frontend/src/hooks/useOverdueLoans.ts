import { useState, useEffect } from 'react';
import type { OverdueLoan } from '@/types';

/**
 * Fetches all currently overdue loans from the Loan Service.
 * A loan is overdue when due_date < today and status is ACTIVE.
 */
export function useOverdueLoans(): {
  loans: OverdueLoan[];
  loading: boolean;
  error: string | null;
} {
  const [loans, setLoans] = useState<OverdueLoan[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch('/api/loan/loans/overdue')
      .then(async (res) => {
        if (!res.ok) {
          let msg = 'Failed to fetch overdue loans';
          try {
            const data = await res.json() as { error?: string };
            if (data.error) msg = data.error;
          } catch {
            // ignore JSON parse errors
          }
          throw new Error(msg);
        }
        return res.json() as Promise<OverdueLoan[]>;
      })
      .then((data) => setLoans(data))
      .catch((e: Error) => {
        setLoans([]);
        setError(e.message);
      })
      .finally(() => setLoading(false));
  }, []);

  return { loans, loading, error };
}

