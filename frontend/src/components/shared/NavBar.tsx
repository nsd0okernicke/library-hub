import { NavLink, useNavigate } from 'react-router-dom';
import { useUser } from '@/hooks/useUser';

const NAV_LINKS = [
  { to: '/', label: 'Books', end: true },
  { to: '/loans', label: 'My Loans', end: false },
  { to: '/loans/new', label: 'New Loan', end: false },
  { to: '/admin', label: 'Admin', end: false },
] as const;

/** Global navigation bar rendered on every page except NotFoundPage. */
export function NavBar(): JSX.Element {
  const { user, clearUser } = useUser();
  const navigate = useNavigate();

  const handleLogout = (): void => {
    clearUser();
    navigate('/');
  };

  const activeCls = 'underline underline-offset-4';
  const linkCls = 'hover:underline hover:underline-offset-4 transition-all';

  return (
    <header className="bg-blue-700 text-white">
      <nav
        className="mx-auto flex h-14 max-w-5xl items-center gap-6 px-4"
        aria-label="Main navigation"
      >
        {/* Brand */}
        <NavLink to="/" className="text-lg font-bold tracking-tight mr-4">
          LibraryHub
        </NavLink>

        {/* Page links */}
        {NAV_LINKS.map(({ to, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `text-sm ${linkCls} ${isActive ? activeCls : ''}`
            }
          >
            {label}
          </NavLink>
        ))}

        {/* Spacer */}
        <span className="flex-1" />

        {/* User area */}
        {user ? (
          <div className="flex items-center gap-3 text-sm">
            <span className="opacity-90">{user.name}</span>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded border border-white/40 px-3 py-1 text-sm hover:bg-white/20 transition-colors"
            >
              Logout
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-3 text-sm">
            <NavLink
              to="/login"
              className={({ isActive }) =>
                `${linkCls} ${isActive ? activeCls : ''}`
              }
            >
              Login
            </NavLink>
            <NavLink
              to="/register"
              className={({ isActive }) =>
                `rounded border border-white/40 px-3 py-1 hover:bg-white/20 transition-colors ${isActive ? 'bg-white/20' : ''}`
              }
            >
              Register
            </NavLink>
          </div>
        )}
      </nav>
    </header>
  );
}

