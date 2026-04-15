import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { useSearchParams } from 'react-router-dom';
import { useState } from 'react';

interface LoanResponse {
  status: string;
  isbn: string;
  user_id: string;
}

/** FE-3 – New loan request form. */
export default function NewLoanPage(): JSX.Element {
  const [searchParams] = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const isbn = searchParams.get('isbn') || '';
  const userRaw = localStorage.getItem('user');
  const user = userRaw ? JSON.parse(userRaw) : null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    if (!user) {
      setError('Please register or log in first.');
      return;
    }
    if (!isbn) {
      setError('ISBN is required');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('/api/loan/loans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isbn, user_id: user.userId }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Request failed');
      } else {
        setPending(true);
        setSuccess(true);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <ErrorBoundary>
        <main className="mx-auto max-w-lg px-4 py-8">
          <h1 className="mb-6 text-2xl font-bold">Request a Loan</h1>
          <p>Please register or log in to request a loan.</p>
        </main>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <main className="mx-auto max-w-lg px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">Request a Loan</h1>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="isbn" className="block mb-1">ISBN</label>
            <input
              id="isbn"
              name="isbn"
              type="text"
              value={isbn}
              readOnly
              className="w-full rounded border px-3 py-2 bg-gray-100"
            />
          </div>
          {error && <div role="alert" className="mb-2 text-red-600">{error}</div>}
          <button
            type="submit"
            disabled={loading}
            className="rounded bg-blue-600 px-4 py-2 text-white disabled:bg-gray-400"
          >
            Request Loan
          </button>
        </form>
        {pending && success && (
          <div className="mt-4 text-yellow-700">Pending – Your loan request is being processed.</div>
        )}
      </main>
    </ErrorBoundary>
  );
}
