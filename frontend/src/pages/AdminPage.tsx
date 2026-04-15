import { ErrorBoundary } from '@/components/shared/ErrorBoundary';

/** FE-7 – Overdue loans admin view. */
export default function AdminPage(): JSX.Element {
  return (
    <ErrorBoundary>
      <main className="mx-auto max-w-5xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">Overdue Loans</h1>
        <p className="text-gray-500">Coming soon…</p>
      </main>
    </ErrorBoundary>
  );
}

