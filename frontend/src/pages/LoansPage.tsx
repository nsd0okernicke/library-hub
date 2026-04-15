import { ErrorBoundary } from '@/components/shared/ErrorBoundary';

/** FE-4 – Loans list for the current user. */
export default function LoansPage(): JSX.Element {
  return (
    <ErrorBoundary>
      <main className="mx-auto max-w-4xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">My Loans</h1>
        <p className="text-gray-500">Coming soon…</p>
      </main>
    </ErrorBoundary>
  );
}

