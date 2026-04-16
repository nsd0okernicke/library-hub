import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import NewLoanPage from '@/pages/NewLoanPage';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { UserProvider } from '@/hooks/useUser';

const mockUser = { userId: 'u123', name: 'Test User', email: 'test@example.com' };
const mockIsbn = '9780132350884';

function renderPage(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <UserProvider>
        <Routes>
          <Route path="/loans/new" element={<NewLoanPage />} />
        </Routes>
      </UserProvider>
    </MemoryRouter>
  );
}

describe('NewLoanPage', () => {
  afterEach(() => {
    localStorage.clear();
  });

  it('shows an error message when no user is logged in', async () => {
    renderPage(`/loans/new?isbn=${mockIsbn}`);
    expect(await screen.findByText(/please register/i)).toBeInTheDocument();
  });

  it('validates that isbn is present', async () => {
    localStorage.setItem('user', JSON.stringify(mockUser));
    renderPage('/loans/new');
    fireEvent.click(screen.getByRole('button', { name: /request loan/i }));
    expect(await screen.findByText(/isbn is required/i)).toBeInTheDocument();
  });

  it('submits a loan request and shows success confirmation', async () => {
    localStorage.setItem('user', JSON.stringify(mockUser));
    server.use(
      http.post('/api/loan/loans', async ({ request }) => {
        const body = await request.json() as { isbn: string; user_id: string };
        return HttpResponse.json(
          { status: 'PENDING', isbn: body.isbn, user_id: body.user_id },
          { status: 201 }
        );
      })
    );
    renderPage(`/loans/new?isbn=${mockIsbn}`);
    fireEvent.click(screen.getByRole('button', { name: /request loan/i }));
    expect(await screen.findByText(/loan requested successfully/i)).toBeInTheDocument();
  });

  it('shows an error when the API returns 422', async () => {
    localStorage.setItem('user', JSON.stringify(mockUser));
    server.use(
      http.post('/api/loan/loans', () =>
        HttpResponse.json({ error: 'Already loaned' }, { status: 422 })
      )
    );
    renderPage(`/loans/new?isbn=${mockIsbn}`);
    fireEvent.click(screen.getByRole('button', { name: /request loan/i }));
    expect(await screen.findByText(/already loaned/i)).toBeInTheDocument();
  });
});
