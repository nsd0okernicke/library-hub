import { ErrorBoundary } from '@/components/shared/ErrorBoundary';

/** FE-3 – New loan request form. */
export default function NewLoanPage(): JSX.Element {
  return (
    <ErrorBoundary>
      <main className="mx-auto max-w-lg px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">Request a Loan</h1>
        <p className="text-gray-500">Coming soon…</p>
      </main>
    </ErrorBoundary>
  );
}

