import { ErrorBoundary } from '@/components/shared/ErrorBoundary';

/** FE-6 – New user registration form. */
export default function RegisterPage(): JSX.Element {
  return (
    <ErrorBoundary>
      <main className="mx-auto max-w-lg px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">Register</h1>
        <p className="text-gray-500">Coming soon…</p>
      </main>
    </ErrorBoundary>
  );
}

