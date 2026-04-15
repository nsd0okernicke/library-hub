import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import BookDetailPage from '@/pages/BookDetailPage';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';

const mockBook = {
  isbn: '9780132350884',
  title: 'Clean Code',
  author: 'Robert C. Martin',
  genre: 'Programming',
  description: 'A Handbook of Agile Software Craftsmanship',
  available_count: 2,
};

describe('BookDetailPage', () => {
  it('zeigt alle Buchdetails und Verfügbarkeit an', async () => {
    server.use(
      http.get('/api/catalog/books/:isbn', ({ params }) => {
        if (params.isbn === mockBook.isbn) {
          return HttpResponse.json(mockBook);
        }
        return HttpResponse.json({ error: 'Book not found' }, { status: 404 });
      })
    );
    render(
      <MemoryRouter initialEntries={[`/books/${mockBook.isbn}`]}>
        <Routes>
          <Route path="/books/:isbn" element={<BookDetailPage />} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByText('Clean Code')).toBeInTheDocument();
    // The page renders "Author: Robert C. Martin" in a single div, so use exact: false
    expect(screen.getByText('Robert C. Martin', { exact: false })).toBeInTheDocument();
    expect(screen.getByText('Programming', { exact: false })).toBeInTheDocument();
    expect(screen.getByText('A Handbook of Agile Software Craftsmanship')).toBeInTheDocument();
    expect(screen.getByText('Available')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /request loan/i })).toBeEnabled();
  });

  it('deaktiviert den Loan-Button, wenn kein Bestand vorhanden ist', async () => {
    server.use(
      http.get('/api/catalog/books/:isbn', () =>
        HttpResponse.json({ ...mockBook, available_count: 0 })
      )
    );
    render(
      <MemoryRouter initialEntries={[`/books/${mockBook.isbn}`]}>
        <Routes>
          <Route path="/books/:isbn" element={<BookDetailPage />} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByText('Clean Code')).toBeInTheDocument();
    expect(screen.getByText('Out of stock')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /request loan/i })).toBeDisabled();
  });

  it('zeigt eine 404-Seite, wenn das Buch nicht existiert', async () => {
    // The default global handler returns 404 for /api/catalog/books/:isbn,
    // so no override is needed here.
    render(
      <MemoryRouter initialEntries={[`/books/0000000000000`]}>
        <Routes>
          <Route path="/books/:isbn" element={<BookDetailPage />} />
          <Route path="*" element={<div>404 Not Found</div>} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByText(/404/i)).toBeInTheDocument();
  });
});
