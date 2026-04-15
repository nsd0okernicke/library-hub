import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { useOverdueLoans } from '@/hooks/useOverdueLoans';
import { formatDate, daysOverdue } from '@/lib/formatters';

/** FE-7 – Overdue loans admin view. */
export default function AdminPage(): JSX.Element {
  const { loans, loading, error } = useOverdueLoans();

  return (
    <ErrorBoundary>
      <main className="mx-auto max-w-5xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">Overdue Loans</h1>

        {loading && <p>Loading…</p>}

        {error && (
          <p role="alert" className="text-red-600">
            Error: {error}
          </p>
        )}

        {!loading && !error && loans.length === 0 && (
          <p className="text-gray-500">No overdue loans.</p>
        )}

        {!loading && !error && loans.length > 0 && (
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="border-b p-2 text-left">User ID</th>
                <th className="border-b p-2 text-left">ISBN</th>
                <th className="border-b p-2 text-left">Due Date</th>
                <th className="border-b p-2 text-left">Days Overdue</th>
              </tr>
            </thead>
            <tbody>
              {loans.map((loan) => {
                const days = daysOverdue(loan.due_date ?? '');
                return (
                  <tr key={loan.loan_id}>
                    <td className="border-b p-2">{loan.user_id}</td>
                    <td className="border-b p-2">{loan.isbn}</td>
                    <td className="border-b p-2">{formatDate(loan.due_date)}</td>
                    <td className="border-b p-2">
                      <span className={days > 0 ? 'font-medium text-red-600' : ''}>
                        {days}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </main>
    </ErrorBoundary>
  );
}


