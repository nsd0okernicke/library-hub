import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { LoanStatusBadge } from '@/components/loans/LoanStatusBadge';
import { useLoans } from '@/hooks/useLoans';
import { formatDate } from '@/lib/formatters';
import type { StoredUser } from '@/types';

const STORAGE_KEY = 'user';

function getStoredUser(): StoredUser | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredUser;
  } catch {
    return null;
  }
}

/** FE-4 – Loans list for the current user. */
export default function LoansPage(): JSX.Element {
  const user = getStoredUser();
  const { loans, loading, error } = useLoans(user?.userId ?? null);

  if (!user) {
    return (
      <ErrorBoundary>
        <main className="mx-auto max-w-4xl px-4 py-8">
          <h1 className="mb-6 text-2xl font-bold">My Loans</h1>
          <p className="text-gray-500">Please register or log in to view your loans.</p>
        </main>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <main className="mx-auto max-w-4xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">My Loans</h1>

        {loading && <p>Loading…</p>}

        {error && (
          <p role="alert" className="text-red-600">
            Error: {error}
          </p>
        )}

        {!loading && !error && loans.length === 0 && (
          <p className="text-gray-500">You have no loans.</p>
        )}

        {!loading && !error && loans.length > 0 && (
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="border-b p-2 text-left">ISBN</th>
                <th className="border-b p-2 text-left">Status</th>
                <th className="border-b p-2 text-left">Due Date</th>
                <th className="border-b p-2 text-left">Returned</th>
                <th className="border-b p-2 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loans.map((loan) => (
                <tr key={loan.loan_id}>
                  <td className="border-b p-2">{loan.isbn}</td>
                  <td className="border-b p-2">
                    <LoanStatusBadge status={loan.status} />
                  </td>
                  <td className="border-b p-2">{formatDate(loan.due_date)}</td>
                  <td className="border-b p-2">{formatDate(loan.returned_at)}</td>
                  <td className="border-b p-2">
                    {loan.status === 'ACTIVE' && (
                      <button
                        type="button"
                        className="rounded bg-red-600 px-3 py-1 text-sm text-white hover:bg-red-700"
                      >
                        Return
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </main>
    </ErrorBoundary>
  );
}


