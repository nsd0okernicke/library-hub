import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { UserProvider } from '@/hooks/useUser';
import { NavBar } from '@/components/shared/NavBar';

function renderNavBar(initialPath = '/') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <UserProvider>
        <NavBar />
      </UserProvider>
    </MemoryRouter>
  );
}

describe('NavBar', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('shows the LibraryHub brand link', () => {
    renderNavBar();
    expect(screen.getByText('LibraryHub')).toBeInTheDocument();
  });

  it('shows all navigation links', () => {
    renderNavBar();
    expect(screen.getByRole('link', { name: 'Books' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'My Loans' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'New Loan' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Admin' })).toBeInTheDocument();
  });

  it('shows Login and Register links when not logged in', () => {
    renderNavBar();
    expect(screen.getByRole('link', { name: 'Login' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Register' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Logout' })).not.toBeInTheDocument();
  });

  it('shows user name and Logout button when logged in', () => {
    localStorage.setItem(
      'user',
      JSON.stringify({ userId: 'u1', name: 'Alice', email: 'alice@example.com' })
    );
    renderNavBar();
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Logout' })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Login' })).not.toBeInTheDocument();
  });

  it('clears session on Logout button click', async () => {
    localStorage.setItem(
      'user',
      JSON.stringify({ userId: 'u1', name: 'Alice', email: 'alice@example.com' })
    );
    renderNavBar();
    await userEvent.click(screen.getByRole('button', { name: 'Logout' }));
    expect(localStorage.getItem('user')).toBeNull();
  });
});

