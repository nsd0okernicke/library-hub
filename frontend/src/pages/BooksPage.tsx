import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { useState } from 'react';
import { useBooks } from '@/hooks/useBooks';

/** FE-1 – Book catalogue with search and filtering. */
export default function BooksPage(): JSX.Element {
  const [search, setSearch] = useState('');
  const { books, loading, error } = useBooks(search);

  // Filterung erfolgt im Backend-Mock, daher hier keine Filterung mehr
  const filteredBooks = books;

  return (
    <ErrorBoundary>
      <main className="mx-auto max-w-5xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold">Book Catalogue</h1>
        <input
          type="text"
          placeholder="Search by title, author, genre"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="mb-4 w-full rounded border px-3 py-2"
          aria-label="Search books"
        />
        {loading && <div data-testid="books-loading">Loading...</div>}
        {error && <div role="alert">Error: {error || 'An error occurred.'}</div>}
        {!loading && !error && filteredBooks.length === 0 && <div>No books found</div>}
        {!loading && !error && filteredBooks.length > 0 && (
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="border-b p-2 text-left">Title</th>
                <th className="border-b p-2 text-left">Author</th>
                <th className="border-b p-2 text-left">Genre</th>
                <th className="border-b p-2 text-left">Stock</th>
              </tr>
            </thead>
            <tbody>
              {filteredBooks.map(book => (
                <tr key={book.isbn}>
                  <td className="border-b p-2">{book.title}</td>
                  <td className="border-b p-2">{book.author}</td>
                  <td className="border-b p-2">{book.genre}</td>
                  <td className="border-b p-2">{book.available_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </main>
    </ErrorBoundary>
  );
}
