import { useState } from 'react';
import { useNavigate, Navigate, Link } from 'react-router-dom';
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { useUser } from '@/hooks/useUser';
import type { StoredUser } from '@/types';

interface UserApiResponse {
  id: string;
  name: string;
  email: string;
}

/** FE-8 – E-mail login for returning users. */
export default function LoginPage(): JSX.Element {
  const { user, setUser } = useUser();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // If already logged in, redirect to catalogue immediately.
  if (user) {
    return <Navigate to="/" replace />;
  }

  const isValidEmail = (value: string): boolean =>
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setError(null);

    if (!isValidEmail(email)) {
      setError('Please enter a valid e-mail address.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch(
        `/api/loan/users?email=${encodeURIComponent(email)}`
      );
      if (res.status === 404) {
        setError('not_found');
        return;
      }
      if (!res.ok) {
        setError('Login failed. Please try again.');
        return;
      }
      const body = (await res.json()) as UserApiResponse;
      const storedUser: StoredUser = {
        userId: body.id,
        name: body.name,
        email: body.email,
      };
      setUser(storedUser);
      navigate('/');
    } catch {
      setError('Network error. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ErrorBoundary>
      <main className="mx-auto max-w-md px-4 py-12">
        <h1 className="mb-6 text-2xl font-bold">Login</h1>
        <form onSubmit={(e) => { void handleSubmit(e); }} noValidate>
          <div className="mb-4">
            <label htmlFor="email" className="block mb-1 font-medium">
              E-mail address
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-describedby={error ? 'login-error' : undefined}
            />
          </div>

          {error && error !== 'not_found' && (
            <p id="login-error" role="alert" className="mb-4 text-sm text-red-600">
              {error}
            </p>
          )}

          {error === 'not_found' && (
            <p id="login-error" role="alert" className="mb-4 text-sm text-red-600">
              No account found for this e-mail.{' '}
              <Link to="/register" className="underline">
                Register here.
              </Link>
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
          >
            {submitting ? 'Logging in…' : 'Login'}
          </button>
        </form>

        <p className="mt-4 text-sm text-gray-500">
          No account yet?{' '}
          <Link to="/register" className="text-blue-600 hover:underline">
            Register here
          </Link>
        </p>
      </main>
    </ErrorBoundary>
  );
}

