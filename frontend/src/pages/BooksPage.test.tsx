import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import BooksPage from './BooksPage';
import { http, HttpResponse } from 'msw';
import { server } from '../tests/mocks/server';
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

  beforeEach(() => {
    // Override the default empty-list handler with one that returns real book data,
    // filtering by the optional 'q' query parameter.
    server.use(
      http.get('/api/catalog/books', ({ request }) => {
        const url = new URL(request.url);
        const q = url.searchParams.get('q')?.toLowerCase() ?? '';
        const filtered = q
          ? books.filter(
              (book) =>
                book.title.toLowerCase().includes(q) ||
                book.author.toLowerCase().includes(q) ||
                book.genre.toLowerCase().includes(q)
            )
          : books;
        return HttpResponse.json({ items: filtered, total: filtered.length, page: 1, page_size: 20 });
      })
    );
  });

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
      http.get('/api/catalog/books', () =>
        HttpResponse.json({ error: 'Internal Server Error' }, { status: 500 })
      )
    );
    render(<BooksPage />);
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/error/i);
  });

  it('shows a friendly message if no books are found', async () => {
    server.use(
      http.get('/api/catalog/books', () =>
        HttpResponse.json({ items: [], total: 0, page: 1, page_size: 20 })
      )
    );
    render(<BooksPage />);
    expect(await screen.findByText(/no books found/i)).toBeInTheDocument();
  });

  // Pagination test can be added here if pagination is implemented
});
