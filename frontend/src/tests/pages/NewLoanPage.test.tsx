import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import NewLoanPage from '@/pages/NewLoanPage';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';

const mockUser = { userId: 'u123', name: 'Test User', email: 'test@example.com' };
const mockIsbn = '9780132350884';

describe('NewLoanPage', () => {
  afterEach(() => {
    localStorage.clear();
  });

  it('zeigt eine Fehlermeldung, wenn kein User eingeloggt ist', async () => {
    render(
      <MemoryRouter initialEntries={[`/loans/new?isbn=${mockIsbn}`]}>
        <Routes>
          <Route path="/loans/new" element={<NewLoanPage />} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByText(/please register/i)).toBeInTheDocument();
  });

  it('validiert, dass isbn und user_id vorhanden sind', async () => {
    localStorage.setItem('user', JSON.stringify(mockUser));
    render(
      <MemoryRouter initialEntries={[`/loans/new`]}>
        <Routes>
          <Route path="/loans/new" element={<NewLoanPage />} />
        </Routes>
      </MemoryRouter>
    );
    fireEvent.click(screen.getByRole('button', { name: /request loan/i }));
    expect(await screen.findByText(/isbn is required/i)).toBeInTheDocument();
  });

  it('sendet eine Loan-Anfrage und zeigt Pending-Bestätigung', async () => {
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
    render(
      <MemoryRouter initialEntries={[`/loans/new?isbn=${mockIsbn}`]}>
        <Routes>
          <Route path="/loans/new" element={<NewLoanPage />} />
        </Routes>
      </MemoryRouter>
    );
    fireEvent.click(screen.getByRole('button', { name: /request loan/i }));
    expect(await screen.findByText(/pending/i)).toBeInTheDocument();
  });

  it('zeigt einen Fehler, wenn die API 422 zurückgibt', async () => {
    localStorage.setItem('user', JSON.stringify(mockUser));
    server.use(
      http.post('/api/loan/loans', () =>
        HttpResponse.json({ error: 'Already loaned' }, { status: 422 })
      )
    );
    render(
      <MemoryRouter initialEntries={[`/loans/new?isbn=${mockIsbn}`]}>
        <Routes>
          <Route path="/loans/new" element={<NewLoanPage />} />
        </Routes>
      </MemoryRouter>
    );
    fireEvent.click(screen.getByRole('button', { name: /request loan/i }));
    expect(await screen.findByText(/already loaned/i)).toBeInTheDocument();
  });
});
