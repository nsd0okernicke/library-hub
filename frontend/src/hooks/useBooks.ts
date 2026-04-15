import { useState, useEffect } from 'react';

export interface Book {
  isbn: string;
  title: string;
  author: string;
  genre: string;
  available_count: number;
}

export function useBooks(query: string = ''): {
  books: Book[];
  loading: boolean;
  error: string | null;
} {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`/api/catalog/books?q=${encodeURIComponent(query)}`)
      .then(async (res) => {
        if (!res.ok) {
          let msg = 'Failed to fetch books';
          try {
            const data = await res.json();
            if (data && data.error) msg = data.error;
          } catch {}
          throw new Error(msg);
        }
        return res.json();
      })
      .then((data) => setBooks(data.items || []))
      .catch((e) => {
        setBooks([]); // Leere die Bücherliste im Fehlerfall
        setError(e.message);
      })
      .finally(() => setLoading(false));
  }, [query]);

  return { books, loading, error };
}
