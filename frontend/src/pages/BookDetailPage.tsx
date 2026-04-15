import { ErrorBoundary } from '@/components/shared/ErrorBoundary';

/** FE-2 – Book detail with availability and loan request. */
export default function BookDetailPage(): JSX.Element {
  return (
    <ErrorBoundary>
      <main className="mx-auto max-w-3xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">Book Details</h1>
        <p className="text-gray-500">Coming soon…</p>
      </main>
    </ErrorBoundary>
  );
}

