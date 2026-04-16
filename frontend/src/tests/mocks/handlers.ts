import { http, HttpResponse } from 'msw';

// Default MSW handlers – override per test with server.use(...)
export const handlers = [
  // Catalog Service
  http.get('/api/catalog/books', () =>
    HttpResponse.json({ items: [], total: 0, page: 1, page_size: 20 })
  ),
  http.get('/api/catalog/books/:isbn', () =>
    HttpResponse.json(null, { status: 404 })
  ),
  http.get('/api/catalog/books/:isbn/availability', () =>
    HttpResponse.json({ isbn: '0000000000000', available_count: 0 })
  ),
  http.post('/api/catalog/books', () =>
    HttpResponse.json({}, { status: 201 })
  ),

  // Loan Service
  http.get('/api/loan/loans', () =>
    HttpResponse.json({ items: [], total: 0, page: 1, page_size: 20 })
  ),
  http.post('/api/loan/loans', () =>
    HttpResponse.json({}, { status: 201 })
  ),
  http.post('/api/loan/loans/:loanId/return', () =>
    HttpResponse.json({}, { status: 200 })
  ),
  http.post('/api/loan/users', () =>
    HttpResponse.json({}, { status: 201 })
  ),
  http.get('/api/loan/users', () =>
    HttpResponse.json(null, { status: 404 })
  ),
  http.get('/api/loan/loans/overdue', () =>
    HttpResponse.json({ items: [] })
  ),
];
