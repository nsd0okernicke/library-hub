import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import BooksPage from './BooksPage';
import { http } from 'msw';
import { setupServer } from 'msw/node';
import React from 'react';

describe('BooksPage', () => {
  const books = [
    {
      isbn: '9780132350884',
      title: 'Clean Code',
      author: 'Robert C. Martin',
      genre: 'Programming',
      available_count: 3,
    },
    {
      isbn: '9781491950296',
      title: 'Site Reliability Engineering',
      author: 'Betsy Beyer',
      genre: 'DevOps',
      available_count: 0,
    },
  ];

  const server = setupServer(
    http.get(new RegExp('/api/catalog/books.*'), (req, res, ctx) => {
      const q = req.url.searchParams.get('q')?.toLowerCase() ?? '';
      const filtered = q
        ? books.filter(
            (book) =>
              book.title.toLowerCase().includes(q) ||
              book.author.toLowerCase().includes(q) ||
              book.genre.toLowerCase().includes(q)
          )
        : books;
      return res(ctx.json({ items: filtered, total: filtered.length, page: 1, page_size: 20 }));
    })
  );

  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  it('shows a loading skeleton while fetching', async () => {
    render(<BooksPage />);
    expect(screen.getByTestId('books-loading')).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByTestId('books-loading')).not.toBeInTheDocument());
  });

  it('renders a list of books with title, author, genre and stock', async () => {
    render(<BooksPage />);
    expect(await screen.findByText('Clean Code')).toBeInTheDocument();
    expect(screen.getByText('Robert C. Martin')).toBeInTheDocument();
    expect(screen.getByText('Programming')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('Site Reliability Engineering')).toBeInTheDocument();
    expect(screen.getByText('DevOps')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('filters books by search input', async () => {
    render(<BooksPage />);
    const search = screen.getByPlaceholderText(/search/i);
    fireEvent.change(search, { target: { value: 'Clean' } });
    expect(await screen.findByText('Clean Code')).toBeInTheDocument();
    expect(screen.queryByText('Site Reliability Engineering')).not.toBeInTheDocument();
  });

  it('shows an error message if the API request fails', async () => {
    server.use(
      http.get(new RegExp('/api/catalog/books.*'), (req, res, ctx) => res(
        ctx.status(500),
        ctx.json({ error: 'Internal Server Error' })
      ))
    );
    render(<BooksPage />);
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/error/i);
  });

  it('shows a friendly message if no books are found', async () => {
    server.use(
      http.get(new RegExp('/api/catalog/books.*'), (req, res, ctx) => res(ctx.json({ items: [], total: 0, page: 1, page_size: 20 })))
    );
    render(<BooksPage />);
    expect(await screen.findByText(/no books found/i)).toBeInTheDocument();
  });

  // Pagination test can be added here if pagination is implemented
});
