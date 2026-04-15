import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import BookDetailPage from '@/pages/BookDetailPage';
import { http } from 'msw';
import { setupServer } from 'msw/node';

const mockBook = {
  isbn: '9780132350884',
  title: 'Clean Code',
  author: 'Robert C. Martin',
  genre: 'Programming',
  description: 'A Handbook of Agile Software Craftsmanship',
  available_count: 2,
};

const server = setupServer(
  http.get(new RegExp('/api/catalog/books/.*'), (req, res, ctx) => {
    const isbn = req.url.pathname.split('/').pop();
    if (isbn === mockBook.isbn) {
      return res(ctx.json(mockBook));
    }
    return res(ctx.status(404), ctx.json({ error: 'Book not found' }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('BookDetailPage', () => {
  it('zeigt alle Buchdetails und Verfügbarkeit an', async () => {
    render(
      <MemoryRouter initialEntries={[`/books/${mockBook.isbn}`]}>
        <Routes>
          <Route path="/books/:isbn" element={<BookDetailPage />} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByText('Clean Code')).toBeInTheDocument();
    expect(screen.getByText('Robert C. Martin')).toBeInTheDocument();
    expect(screen.getByText('Programming')).toBeInTheDocument();
    expect(screen.getByText('A Handbook of Agile Software Craftsmanship')).toBeInTheDocument();
    expect(screen.getByText('Available')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /request loan/i })).toBeEnabled();
  });

  it('deaktiviert den Loan-Button, wenn kein Bestand vorhanden ist', async () => {
    server.use(
      http.get(new RegExp('/api/catalog/books/.*'), (req, res, ctx) =>
        res(ctx.json({ ...mockBook, available_count: 0 }))
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
