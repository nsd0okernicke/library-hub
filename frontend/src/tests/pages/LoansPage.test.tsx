import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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

// ─── FE-5: Return a Book ──────────────────────────────────────────────────────

describe('LoansPage – Return a Book (FE-5)', () => {
  const activeLoans: Loan[] = [
    {
      loan_id: 'l-001',
      isbn: '9780132350884',
      user_id: 'u-abc-123',
      status: 'ACTIVE',
      due_date: '2026-05-15',
      returned_at: null,
    },
  ];

  afterEach(() => {
    localStorage.clear();
  });

  it('calls POST /api/loan/loans/:id/return when Return is clicked', async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(mockUser));
    let returnCalled = false;
    server.use(
      http.get('/api/loan/loans', () =>
        HttpResponse.json({ items: activeLoans, total: 1, page: 1, page_size: 20 })
      ),
      http.post('/api/loan/loans/:loanId/return', () => {
        returnCalled = true;
        return HttpResponse.json({}, { status: 200 });
      })
    );
    renderLoansPage();
    await screen.findByText('9780132350884');
    await userEvent.click(screen.getByRole('button', { name: /return/i }));
    await waitFor(() => expect(returnCalled).toBe(true));
  });

  it('shows a success toast after returning a book', async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(mockUser));
    server.use(
      http.get('/api/loan/loans', () =>
        HttpResponse.json({ items: activeLoans, total: 1, page: 1, page_size: 20 })
      ),
      http.post('/api/loan/loans/:loanId/return', () =>
        HttpResponse.json({}, { status: 200 })
      )
    );
    renderLoansPage();
    await screen.findByText('9780132350884');
    await userEvent.click(screen.getByRole('button', { name: /return/i }));
    expect(await screen.findByText(/returned successfully/i)).toBeInTheDocument();
  });

  it('updates the loan list after a successful return', async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(mockUser));
    let callCount = 0;
    const returnedLoans: Loan[] = [{ ...activeLoans[0]!, status: 'RETURNED', returned_at: '2026-04-15' }];
    server.use(
      http.get('/api/loan/loans', () => {
        callCount += 1;
        const items = callCount === 1 ? activeLoans : returnedLoans;
        return HttpResponse.json({ items, total: items.length, page: 1, page_size: 20 });
      }),
      http.post('/api/loan/loans/:loanId/return', () =>
        HttpResponse.json({}, { status: 200 })
      )
    );
    renderLoansPage();
    await screen.findByText('9780132350884');
    await userEvent.click(screen.getByRole('button', { name: /return/i }));
    // After refresh the Return button should be gone (loan is now RETURNED)
    await waitFor(() =>
      expect(screen.queryByRole('button', { name: /return/i })).not.toBeInTheDocument()
    );
  });

  it('shows an error toast when the return fails with 409 Conflict', async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(mockUser));
    server.use(
      http.get('/api/loan/loans', () =>
        HttpResponse.json({ items: activeLoans, total: 1, page: 1, page_size: 20 })
      ),
      http.post('/api/loan/loans/:loanId/return', () =>
        HttpResponse.json({ error: 'Loan already returned' }, { status: 409 })
      )
    );
    renderLoansPage();
    await screen.findByText('9780132350884');
    await userEvent.click(screen.getByRole('button', { name: /return/i }));
    expect(await screen.findByText(/already returned/i)).toBeInTheDocument();
  });
});
