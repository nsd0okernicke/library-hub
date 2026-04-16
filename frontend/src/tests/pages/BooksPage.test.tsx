import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import BooksPage from '@/pages/BooksPage';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';

/** Helper: render BooksPage inside a MemoryRouter (required for <Link>). */
const renderPage = () =>
  render(
    <MemoryRouter>
      <BooksPage />
    </MemoryRouter>
  );

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
    renderPage();
    expect(screen.getByTestId('books-loading')).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByTestId('books-loading')).not.toBeInTheDocument());
  });

  it('renders a list of books with title, author, genre and stock', async () => {
    renderPage();
    expect(await screen.findByText('Clean Code')).toBeInTheDocument();
    expect(screen.getByText('Robert C. Martin')).toBeInTheDocument();
    expect(screen.getByText('Programming')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('Site Reliability Engineering')).toBeInTheDocument();
    expect(screen.getByText('DevOps')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('renders book titles as links to the detail page', async () => {
    renderPage();
    const link = await screen.findByRole('link', { name: 'Clean Code' });
    expect(link).toHaveAttribute('href', '/books/9780132350884');
  });

  it('filters books by search input', async () => {
    renderPage();
    await screen.findByText('Clean Code'); // wait for initial load
    const search = screen.getByPlaceholderText(/search/i);
    fireEvent.change(search, { target: { value: 'Clean' } });
    // Wait for debounce (300 ms) + fetch to settle
    await waitFor(() =>
      expect(screen.queryByText('Site Reliability Engineering')).not.toBeInTheDocument()
    );
    expect(screen.getByText('Clean Code')).toBeInTheDocument();
  });

  it('shows an error message if the API request fails', async () => {
    server.use(
      http.get('/api/catalog/books', () =>
        HttpResponse.json({ error: 'Internal Server Error' }, { status: 500 })
      )
    );
    renderPage();
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/error/i);
  });

  it('shows a friendly message if no books are found', async () => {
    server.use(
      http.get('/api/catalog/books', () =>
        HttpResponse.json({ items: [], total: 0, page: 1, page_size: 20 })
      )
    );
    renderPage();
    expect(await screen.findByText(/no books found/i)).toBeInTheDocument();
  });

  // Pagination test can be added here if pagination is implemented
});

