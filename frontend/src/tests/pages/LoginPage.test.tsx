import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { UserProvider } from '@/hooks/useUser';
import LoginPage from '@/pages/LoginPage';

function renderLoginPage() {
  return render(
    <MemoryRouter>
      <UserProvider>
        <LoginPage />
      </UserProvider>
    </MemoryRouter>
  );
}

describe('LoginPage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders the login form', () => {
    renderLoginPage();
    expect(screen.getByRole('heading', { name: 'Login' })).toBeInTheDocument();
    expect(screen.getByLabelText('E-mail address')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Login' })).toBeInTheDocument();
  });

  it('shows validation error for invalid e-mail format', async () => {
    renderLoginPage();
    await userEvent.type(screen.getByLabelText('E-mail address'), 'notanemail');
    await userEvent.click(screen.getByRole('button', { name: 'Login' }));
    expect(
      await screen.findByRole('alert')
    ).toHaveTextContent('valid e-mail');
  });

  it('shows "no account found" message on 404 response', async () => {
    server.use(
      http.get('/api/loan/users', () => HttpResponse.json(null, { status: 404 }))
    );
    renderLoginPage();
    await userEvent.type(screen.getByLabelText('E-mail address'), 'unknown@example.com');
    await userEvent.click(screen.getByRole('button', { name: 'Login' }));
    expect(
      await screen.findByRole('alert')
    ).toHaveTextContent('No account found');
  });

  it('stores user and shows "Register here" link on 404', async () => {
    server.use(
      http.get('/api/loan/users', () => HttpResponse.json(null, { status: 404 }))
    );
    renderLoginPage();
    await userEvent.type(screen.getByLabelText('E-mail address'), 'unknown@example.com');
    await userEvent.click(screen.getByRole('button', { name: 'Login' }));
    await waitFor(() => {
      expect(screen.getByRole('link', { name: 'Register here.' })).toBeInTheDocument();
    });
  });

  it('stores user in localStorage on successful login', async () => {
    server.use(
      http.get('/api/loan/users', () =>
        HttpResponse.json({ id: 'u-123', name: 'Alice', email: 'alice@example.com' })
      )
    );
    renderLoginPage();
    await userEvent.type(screen.getByLabelText('E-mail address'), 'alice@example.com');
    await userEvent.click(screen.getByRole('button', { name: 'Login' }));
    await waitFor(() => {
      const stored = localStorage.getItem('user');
      expect(stored).not.toBeNull();
      const parsed = JSON.parse(stored!) as { userId: string; name: string };
      expect(parsed.userId).toBe('u-123');
      expect(parsed.name).toBe('Alice');
    });
  });

  it('shows a link to the register page', () => {
    renderLoginPage();
    expect(screen.getByRole('link', { name: 'Register here' })).toBeInTheDocument();
  });
});

