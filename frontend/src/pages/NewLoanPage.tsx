import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useUser } from '@/hooks/useUser';
interface LoanResponse {
  status: string;
  isbn: string;
  user_id: string;
}
const REDIRECT_DELAY_MS = 1500;
/** FE-3 – New loan request form. */
export default function NewLoanPage(): JSX.Element {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const isbnFromUrl = searchParams.get('isbn') ?? '';
  const [isbn, setIsbn] = useState(isbnFromUrl);
  const { user } = useUser();
  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setError(null);
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
      const data = await res.json() as LoanResponse | { error?: string };
      if (!res.ok) {
        setError(('error' in data && data.error) ? data.error : 'Request failed');
      } else {
        setSubmitted(true);
        setTimeout(() => { navigate('/loans'); }, REDIRECT_DELAY_MS);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Network error');
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
  if (submitted) {
    return (
      <ErrorBoundary>
        <main className="mx-auto max-w-lg px-4 py-8">
          <h1 className="mb-6 text-2xl font-bold">Request a Loan</h1>
          <p className="text-green-600 font-medium">
            ✓ Loan requested successfully! Redirecting to your loans…
          </p>
        </main>
      </ErrorBoundary>
    );
  }
  return (
    <ErrorBoundary>
      <main className="mx-auto max-w-lg px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">Request a Loan</h1>
        <form onSubmit={(e) => { void handleSubmit(e); }}>
          <div className="mb-4">
            <label htmlFor="isbn" className="block mb-1">ISBN</label>
            <input
              id="isbn"
              name="isbn"
              type="text"
              value={isbn}
              readOnly={!!isbnFromUrl}
              onChange={(e) => setIsbn(e.target.value)}
              placeholder="e.g. 978-3-16-148410-0"
              className={`w-full rounded border px-3 py-2 ${isbnFromUrl ? 'bg-gray-100' : 'focus:outline-none focus:ring-2 focus:ring-blue-500'}`}
            />
          </div>
          {error && <div role="alert" className="mb-2 text-red-600">{error}</div>}
          <button
            type="submit"
            disabled={loading}
            className="rounded bg-blue-600 px-4 py-2 text-white disabled:bg-gray-400 hover:bg-blue-700 transition-colors"
          >
            {loading ? 'Requesting…' : 'Request Loan'}
          </button>
        </form>
      </main>
    </ErrorBoundary>
  );
}