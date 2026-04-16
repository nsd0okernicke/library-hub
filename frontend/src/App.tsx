import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { UserProvider } from '@/hooks/useUser';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { NavBar } from '@/components/shared/NavBar';

// Route-level code splitting per frontend-concept.md performance requirements
const BooksPage = lazy(() => import('@/pages/BooksPage'));
const BookDetailPage = lazy(() => import('@/pages/BookDetailPage'));
const LoansPage = lazy(() => import('@/pages/LoansPage'));
const NewLoanPage = lazy(() => import('@/pages/NewLoanPage'));
const LoginPage = lazy(() => import('@/pages/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/RegisterPage'));
const AdminPage = lazy(() => import('@/pages/AdminPage'));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));

/** Layout wrapper that renders the NavBar above all normal pages. */
function MainLayout(): JSX.Element {
  return (
    <>
      <NavBar />
      <Outlet />
    </>
  );
}

export default function App(): JSX.Element {
  return (
    <UserProvider>
      <BrowserRouter>
        <Suspense fallback={<LoadingSpinner />}>
          <Routes>
            {/* Normal pages – all share the NavBar via MainLayout */}
            <Route element={<MainLayout />}>
              <Route path="/" element={<BooksPage />} />
              <Route path="/books/:isbn" element={<BookDetailPage />} />
              <Route path="/loans" element={<LoansPage />} />
              <Route path="/loans/new" element={<NewLoanPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/admin" element={<AdminPage />} />
            </Route>

            {/* NotFoundPage has no NavBar – only a back link */}
            <Route path="/404" element={<NotFoundPage />} />
            <Route path="*" element={<Navigate to="/404" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </UserProvider>
  );
}



