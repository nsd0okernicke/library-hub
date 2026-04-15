import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';

interface BookDetail {
  isbn: string;
  title: string;
  author: string;
  genre: string;
  description: string;
  available_count: number;
}

/** FE-2 – Book detail with availability and loan request. */
export default function BookDetailPage(): JSX.Element {
  const { isbn } = useParams();
  const navigate = useNavigate();
  const [book, setBook] = useState<BookDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`/api/catalog/books/${isbn}`)
      .then(async (res) => {
        if (res.status === 404) {
          navigate('/404', { replace: true });
          return;
        }
        if (!res.ok) {
          throw new Error('Failed to fetch book');
        }
        return res.json();
      })
      .then((data) => {
        if (data) setBook(data);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [isbn, navigate]);

  if (loading) {
    return (
      <ErrorBoundary>
        <main className="mx-auto max-w-3xl px-4 py-8">
          <h1 className="mb-6 text-2xl font-bold">Book Details</h1>
          <p>Loading…</p>
        </main>
      </ErrorBoundary>
    );
  }
  if (error) {
    return (
      <ErrorBoundary>
        <main className="mx-auto max-w-3xl px-4 py-8">
          <h1 className="mb-6 text-2xl font-bold">Book Details</h1>
          <p role="alert">Error: {error}</p>
        </main>
      </ErrorBoundary>
    );
  }
  if (!book) {
    return null;
  }
  return (
    <ErrorBoundary>
      <main className="mx-auto max-w-3xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">{book.title}</h1>
        <div className="mb-2">Author: {book.author}</div>
        <div className="mb-2">Genre: {book.genre}</div>
        <div className="mb-2">ISBN: {book.isbn}</div>
        <div className="mb-4">{book.description}</div>
        <div className="mb-4">
          {book.available_count > 0 ? (
            <span className="text-green-600">Available</span>
          ) : (
            <span className="text-red-600">Out of stock</span>
          )}
        </div>
        <button
          type="button"
          disabled={book.available_count === 0}
          className="rounded bg-blue-600 px-4 py-2 text-white disabled:bg-gray-400"
        >
          Request Loan
        </button>
      </main>
    </ErrorBoundary>
  );
}
