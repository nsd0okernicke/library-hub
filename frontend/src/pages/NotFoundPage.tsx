import { Link } from 'react-router-dom';

/** Fallback page shown for unknown routes. */
export default function NotFoundPage(): JSX.Element {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 text-center">
      <h1 className="text-6xl font-bold text-gray-200">404</h1>
      <p className="mt-4 text-xl font-semibold text-gray-700">Page not found</p>
      <p className="mt-2 text-gray-500">The page you are looking for does not exist.</p>
      <Link
        to="/"
        className="mt-6 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      >
        Back to catalogue
      </Link>
    </main>
  );
}

