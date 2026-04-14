-- Sample data: 10 books with valid ISBNs for the Catalog Service
-- Run against the catalog_db database:
--   psql -h localhost -p 5432 -U catalog -d catalog_db -f seed_books.sql
--
-- All ISBNs verified against their check-digit algorithm (ISBN-13 mod-10, ISBN-10 mod-11).

-- ── Books ─────────────────────────────────────────────────────────────────────

INSERT INTO books (isbn, title, author, genre, description) VALUES
  ('9780132350884', 'Clean Code',                        'Robert C. Martin',     'Software Engineering', 'A handbook of agile software craftsmanship.'),
  ('9780134494166', 'Clean Architecture',                'Robert C. Martin',     'Software Engineering', 'A craftsman''s guide to software structure and design.'),
  ('9780201633610', 'Design Patterns',                   'Gang of Four',         'Software Engineering', 'Elements of reusable object-oriented software.'),
  ('9780596517748', 'JavaScript: The Good Parts',        'Douglas Crockford',    'Programming',          'Unearthing the excellence in JavaScript.'),
  ('9781491950357', 'Python Fluente',                    'Luciano Ramalho',      'Programming',          'Clear, concise and effective Python programming.'),
  ('9780134685991', 'Effective Java',                    'Joshua Bloch',         'Programming',          'Best practices for the Java platform.'),
  ('9780321125217', 'Domain-Driven Design',              'Eric Evans',           'Software Engineering', 'Tackling complexity in the heart of software.'),
  ('9780062301239', 'The Hard Thing About Hard Things',  'Ben Horowitz',         'Business',             'Building a business when there are no easy answers.'),
  ('9780743273565', 'The Great Gatsby',                  'F. Scott Fitzgerald',  'Fiction',              'A story of the fabulously wealthy Jay Gatsby.'),
  ('9780451524935', 'Nineteen Eighty-Four',              'George Orwell',        'Fiction',              'A dystopian novel set in a totalitarian society.')
ON CONFLICT (isbn) DO NOTHING;

-- ── Stock entries ─────────────────────────────────────────────────────────────

INSERT INTO book_stock (isbn, available_count) VALUES
  ('9780132350884', 12),
  ('9780134494166',  8),
  ('9780201633610',  6),
  ('9780596517748',  5),
  ('9781491950357', 10),
  ('9780134685991',  7),
  ('9780321125217',  4),
  ('9780062301239',  9),
  ('9780743273565', 15),
  ('9780451524935', 14)
ON CONFLICT (isbn) DO UPDATE SET available_count = EXCLUDED.available_count;

