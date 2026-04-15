import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { UserProvider } from '@/hooks/useUser';
import RegisterPage from '@/pages/RegisterPage';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';

function renderRegisterPage(): ReturnType<typeof render> {
  return render(
    <UserProvider>
      <MemoryRouter initialEntries={['/register']}>
        <Routes>
          <Route path="/" element={<div data-testid="books-page">Books Page</div>} />
          <Route path="/register" element={<RegisterPage />} />
        </Routes>
      </MemoryRouter>
    </UserProvider>
  );
}

describe('RegisterPage', () => {
  afterEach(() => {
    localStorage.clear();
  });

  it('validates that name is required', async () => {
    renderRegisterPage();
    await userEvent.click(screen.getByRole('button', { name: /register/i }));
    expect(await screen.findByText(/name is required/i)).toBeInTheDocument();
  });

  it('validates that email is required', async () => {
    renderRegisterPage();
    await userEvent.click(screen.getByRole('button', { name: /register/i }));
    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
  });

  it('validates the email format', async () => {
    renderRegisterPage();
    await userEvent.type(screen.getByLabelText(/name/i), 'Alice');
    await userEvent.type(screen.getByLabelText(/email/i), 'not-an-email');
    await userEvent.click(screen.getByRole('button', { name: /register/i }));
    expect(await screen.findByText(/valid email/i)).toBeInTheDocument();
  });

  it('calls POST /api/loan/users and stores the user in localStorage on success', async () => {
    server.use(
      http.post('/api/loan/users', () =>
        HttpResponse.json(
          { user_id: 'new-uuid-123', name: 'Alice', email: 'alice@example.com' },
          { status: 201 }
        )
      )
    );
    renderRegisterPage();
    await userEvent.type(screen.getByLabelText(/name/i), 'Alice');
    await userEvent.type(screen.getByLabelText(/email/i), 'alice@example.com');
    await userEvent.click(screen.getByRole('button', { name: /register/i }));
    await waitFor(() => {
      const stored = localStorage.getItem('user');
      expect(stored).not.toBeNull();
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const user = JSON.parse(stored!) as { userId: string };
      expect(user.userId).toBe('new-uuid-123');
    });
  });

  it('redirects to the book catalogue after successful registration', async () => {
    server.use(
      http.post('/api/loan/users', () =>
        HttpResponse.json(
          { user_id: 'new-uuid-123', name: 'Alice', email: 'alice@example.com' },
          { status: 201 }
        )
      )
    );
    renderRegisterPage();
    await userEvent.type(screen.getByLabelText(/name/i), 'Alice');
    await userEvent.type(screen.getByLabelText(/email/i), 'alice@example.com');
    await userEvent.click(screen.getByRole('button', { name: /register/i }));
    expect(await screen.findByTestId('books-page')).toBeInTheDocument();
  });

  it('shows "This e-mail is already registered" for a 409 response', async () => {
    server.use(
      http.post('/api/loan/users', () =>
        HttpResponse.json({ error: 'Email already in use' }, { status: 409 })
      )
    );
    renderRegisterPage();
    await userEvent.type(screen.getByLabelText(/name/i), 'Alice');
    await userEvent.type(screen.getByLabelText(/email/i), 'alice@example.com');
    await userEvent.click(screen.getByRole('button', { name: /register/i }));
    expect(await screen.findByText(/this e-mail is already registered/i)).toBeInTheDocument();
  });
});

