import { ErrorBoundary } from '@/components/shared/ErrorBoundary';

/** FE-1 – Book catalogue with search and filtering. */
export default function BooksPage(): JSX.Element {
  return (
    <ErrorBoundary>
      <main className="mx-auto max-w-5xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">Book Catalogue</h1>
        <p className="text-gray-500">Coming soon…</p>
      </main>
    </ErrorBoundary>
  );
}

