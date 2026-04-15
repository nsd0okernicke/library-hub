import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import LoansPage from '@/pages/LoansPage';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import type { Loan } from '@/types';
const STORAGE_KEY = 'user';
const mockUser = { userId: 'u-abc-123', name: 'Alice', email: 'alice@example.com' };
const mockLoans: Loan[] = [
  {
    loan_id: 'l-001',
    isbn: '9780132350884',
    user_id: 'u-abc-123',
    status: 'ACTIVE',
    due_date: '2026-05-15',
    returned_at: null,
  },
  {
    loan_id: 'l-002',
    isbn: '9781491950296',
    user_id: 'u-abc-123',
    status: 'RETURNED',
    due_date: '2026-04-01',
    returned_at: '2026-03-28',
  },
  {
    loan_id: 'l-003',
    isbn: '9780201633610',
    user_id: 'u-abc-123',
    status: 'PENDING',
    due_date: null,
    returned_at: null,
  },
];
function renderLoansPage(): ReturnType<typeof render> {
  return render(
    <MemoryRouter>
      <LoansPage />
    </MemoryRouter>
  );
}
describe('LoansPage', () => {
  afterEach(() => {
    localStorage.clear();
  });
  it('shows a message when no user is logged in', async () => {
    renderLoansPage();
    expect(await screen.findByText(/please register/i)).toBeInTheDocument();
  });
  it('shows an empty state message when the user has no loans', async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(mockUser));
    renderLoansPage();
    expect(await screen.findByText(/no loans/i)).toBeInTheDocument();
  });
  it('renders all loans with ISBN, status badge and due date', async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(mockUser));
    server.use(
      http.get('/api/loan/loans', () =>
        HttpResponse.json({ items: mockLoans, total: mockLoans.length, page: 1, page_size: 20 })
      )
    );
    renderLoansPage();
    expect(await screen.findByText('9780132350884')).toBeInTheDocument();
    expect(screen.getByText('9781491950296')).toBeInTheDocument();
    expect(screen.getByText('9780201633610')).toBeInTheDocument();
    expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    expect(screen.getByText('RETURNED')).toBeInTheDocument();
    expect(screen.getByText('PENDING')).toBeInTheDocument();
    expect(screen.getByText('15 May 2026')).toBeInTheDocument();
  });
  it('shows a Return button only for ACTIVE loans', async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(mockUser));
    server.use(
      http.get('/api/loan/loans', () =>
        HttpResponse.json({ items: mockLoans, total: mockLoans.length, page: 1, page_size: 20 })
      )
    );
    renderLoansPage();
    await screen.findByText('9780132350884');
    const returnButtons = screen.getAllByRole('button', { name: /return/i });
    expect(returnButtons).toHaveLength(1);
  });
  it('shows an error message when the API request fails', async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(mockUser));
    server.use(
      http.get('/api/loan/loans', () =>
        HttpResponse.json({ error: 'Internal Server Error' }, { status: 500 })
      )
    );
    renderLoansPage();
    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});