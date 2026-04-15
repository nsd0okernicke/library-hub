# LibraryHub Frontend – Requirements
## 1. Project Overview
**Name:** LibraryHub Frontend
**Type:** Learning project – React SPA
**Goal:** Build a clean, type-safe, well-tested frontend that consumes the LibraryHub backend APIs and demonstrates modern React best practices.
**Depends on:**
- Catalog Service REST API (`http://localhost:8000`)
- Loan Service REST API (`http://localhost:8001`)
> **Related documents:**
> - Frontend architecture: [`frontend-concept.md`](frontend-concept.md)
> - Backend architecture: [`concept.md`](concept.md)
> - Backend requirements: [`requirements.md`](requirements.md)
---
## 2. Functional Requirements
### FE-1 – Browse the Book Catalogue
> As a user I want to browse all available books so that I can discover what the library offers.
**Acceptance criteria:**
- Displays a list of books with title, author, genre and available stock
- Supports text search by title, author and genre (filters via API query params)
- Shows a loading skeleton while data is being fetched
- Shows an error message if the API request fails
- Empty result shows a friendly "no books found" message (not a blank screen)
- Pagination for large catalogues
---
### FE-2 – View Book Details
> As a user I want to see all details of a book including its current availability so that I can decide whether to borrow it.
**Acceptance criteria:**
- Displays full book metadata (ISBN, title, author, genre, description)
- Displays current `available_count` with a clear in-stock / out-of-stock indicator
- Provides a "Request Loan" button that is disabled when `available_count === 0`
- Shows a 404 page if the ISBN does not exist
- Availability is automatically refreshed after a successful loan request
---
### FE-3 – Request a Loan
> As a user I want to request a book loan so that I can borrow a book from the library.
**Acceptance criteria:**
- User must have a valid `user_id` (stored in `localStorage` after registration)
- Submitting the form calls `POST /loans` and shows a pending confirmation immediately
- The UI reflects the `PENDING` status instantly (via API response)
- Form validates: `isbn` must be present, `user_id` must be present
- Submission errors (network, 422) are shown inline
---
### FE-4 – View My Loans
> As a user I want to see all my loans so that I can track what I have borrowed.
**Acceptance criteria:**
- Displays all loans for the current user (`GET /loans?user_id=...`)
- Each loan shows: ISBN, status badge, due date, returned date
- Loan status is colour-coded: `PENDING` (grey), `ACTIVE` (green), `RETURNED` (blue), `REJECTED` (red)
- Shows a "Return" button for `ACTIVE` loans
- Shows an empty state message when the user has no loans
- List auto-refreshes after a return action
---
### FE-5 – Return a Book
> As a user I want to return a book I have borrowed so that the library stock is updated.
**Acceptance criteria:**
- "Return" button is visible only for `ACTIVE` loans
- Clicking triggers `POST /loans/{loan_id}/return`
- Loan status updates to `RETURNED` immediately after success
- A success toast notification is shown
- Errors (409, 404) are shown with clear messages
---
### FE-6 – Register a User
> As a new user I want to register with my name and e-mail so that I can start borrowing books.
**Acceptance criteria:**
- Form with `name` (required) and `email` (required, valid e-mail format)
- Calls `POST /users` on submit
- On success: stores the returned `user_id` in `localStorage` for the session
- Duplicate e-mail (409) shows a clear inline error: "This e-mail is already registered"
- After registration, the user is redirected to the book catalogue
---
### FE-7 – View Overdue Loans (Admin)
> As an admin I want to see all overdue loans so that I can follow up with borrowers.
**Acceptance criteria:**
- Displays all loans where `due_date < today` and `status === ACTIVE`
- Shows: user ID, ISBN, due date, days overdue
- Days overdue is highlighted in red
- Empty state: "No overdue loans" message
- Accessible at route `/admin`
- Admin link is visible in the global navigation for all users (no role system in MVP)
---
### FE-8 – Log in as existing user
> As a returning user I want to log in with my e-mail address so that I can access my loans without re-registering.
**Acceptance criteria:**
- Simple e-mail input form at route `/login`
- On submit calls `GET /users?email=<email>` on the Loan Service
- On success (200): stores the returned user in context + `localStorage`, redirects to `/`
- On 404: shows a friendly message "No account found for this e-mail. Register here." with a link to `/register`
- Network errors are shown inline
- If a user is already logged in, visiting `/login` redirects to `/`
---
### FE-UI-1 – Global Navigation Bar
> As a user I want a persistent navigation bar so that I can reach all pages from anywhere in the app.
**Acceptance criteria:**
- Visible on every page except `NotFoundPage` (which shows only a back link)
- Shows the application name "LibraryHub" as a link to `/`
- Navigation links: *Books* (`/`), *My Loans* (`/loans`), *New Loan* (`/loans/new`), *Admin* (`/admin`)
- When logged in: shows the user's name and a **Logout** button; clicking logout clears the session and redirects to `/`
- When not logged in: shows **Login** (`/login`) and **Register** (`/register`) links
- Active link is visually highlighted
---
## 3. Non-Functional Requirements
### 3.1 Architecture
- The frontend is a **standalone application** inside `frontend/` – no mixing with backend code
- Follows the layered architecture defined in `frontend-concept.md`: `pages/ -> components/ -> hooks/ -> api/`
- **Layer rules are strictly enforced:**
  - `components/` and `pages/` must not call the generated API clients directly
  - All API calls must go through a custom hook in `hooks/`
- Generated API clients in `src/api/` must **never be edited manually**
- No business logic in components – all data fetching and mutation lives in `hooks/`
---
### 3.2 Technical Requirements
- **Node.js:** 20 LTS or higher
- **TypeScript:** `strict` mode is **mandatory**:
  ```json
  {
    "compilerOptions": {
      "strict": true,
      "noImplicitAny": true,
      "strictNullChecks": true,
      "noUncheckedIndexedAccess": true,
      "exactOptionalPropertyTypes": true
    }
  }
  ```
- **`any` is forbidden** – ESLint rule `@typescript-eslint/no-explicit-any: "error"`
- **`as` type assertions** are strongly discouraged – use type guards instead
- All public functions and hooks must have **explicit return type annotations**
- React components must use **function components only** – no class components
---
### 3.3 Naming Conventions
| Item | Convention | Example |
|------|------------|---------|
| Component files | `PascalCase.tsx` | `BookCard.tsx` |
| Hook files | `camelCase.ts`, prefixed `use` | `useBooks.ts` |
| Utility files | `camelCase.ts` | `formatters.ts` |
| Types / Interfaces | `PascalCase` | `BookResponse`, `LoanStatus` |
| Constants | `SCREAMING_SNAKE_CASE` | `DEFAULT_PAGE_SIZE` |
| Variables & functions | `camelCase` | `availableCount`, `handleSubmit` |
| Event handlers | `handle<Event>` | `handleSubmit`, `handleLoanRequest` |
| Test files | `<name>.test.tsx` / `.test.ts` | `BookCard.test.tsx` |
| CSS | Tailwind utility classes only | `className="flex items-center gap-2"` |
---
### 3.4 Code Quality Rules
#### General
- **One component per file** – never export multiple components from one file
- Component files must not exceed **150 lines** (excluding imports and type definitions)
- Hook files must not exceed **100 lines** – extract sub-hooks if needed
- No **magic numbers** – extract named constants with descriptive names
- No **commented-out code** – use version control (`git`) to track history
- No **`console.log`** in committed code – remove before committing
- All code, comments, variable names, function names and error messages must be in **English**
#### React-Specific Rules
- **Named exports** preferred over default exports for components and hooks
  (exception: page components may use default exports for React.lazy compatibility)
- **Never** use `useEffect` to synchronise derived state – compute values directly
- Avoid **prop drilling** beyond 2 levels – use composition, context or hooks
- **Keys in lists** must be stable unique IDs – never use array index as key
- Use `React.memo`, `useCallback` and `useMemo` only when a measured performance issue exists – never pre-emptively
- **Conditional rendering** must be readable:
```tsx
// Good
{isLoading && <Spinner />}
{error && <ErrorMessage message={error.message} />}
{data && <BookList books={data.items} />}
// Bad
{isLoading ? <Spinner /> : error ? <ErrorMessage ... /> : <BookList ... />}
```
#### TypeScript-Specific Rules
- Prefer **`interface`** for object shapes that describe data structures
- Prefer **`type`** for unions, intersections, mapped types and aliases
- Use **discriminated unions** for state modelling:
  ```ts
  type LoanStatus = 'PENDING' | 'ACTIVE' | 'RETURNED' | 'REJECTED';
  ```
- Use **Zod** as the single source of truth for form validation types:
  ```ts
  const loanRequestSchema = z.object({
    isbn: z.string().min(1, 'ISBN is required'),
    userId: z.string().uuid('Must be a valid user ID'),
  });
  type LoanRequestFormData = z.infer<typeof loanRequestSchema>;
  ```
- All API response types come from the generated clients – never redeclare them manually
#### Props Design
- Define all props via explicit TypeScript `interface` – never `any` or inline object types
- Props that are callbacks must be named `on<Event>`:
  ```tsx
  interface BookCardProps {
    isbn: string;
    title: string;
    author: string;
    availableCount: number;
    onLoanRequest: (isbn: string) => void;
  }
  ```
- Prefer **required props** over optional props with defaults – makes behaviour explicit
---
### 3.5 Testing Requirements
- **Coverage target: > 80 %** (measured with `@vitest/coverage-v8`)
- **Test-first:** write the test before the implementation
- All tests must pass before a feature branch is merged
#### Mandatory test types
| Type | Tool | Coverage target |
|------|------|----------------|
| Component tests | Vitest + React Testing Library | Every component |
| Hook tests | Vitest + `renderHook` | Every custom hook |
| Page tests | Vitest + RTL + MSW | Every page |
| Accessibility tests | `jest-axe` | Every page |
#### Testing Principles (strictly enforced)
- **Test behaviour, not implementation** – use `getByRole`, `getByLabelText`, `getByText`; avoid `getByTestId`
- **Never test React internals** – no state, refs, lifecycle or component methods
- **MSW for all API mocking** – handlers in `tests/mocks/handlers.ts`
- **One `describe` block per component**, one `it` per distinct user behaviour
- Tests must be fully **isolated** – no shared mutable state between tests; use `beforeEach` to reset
- Use **`userEvent`** (not `fireEvent`) for all user interaction simulation
- All async tests must properly `await` assertions – never leave floating promises
- Test descriptions must be readable sentences:
  ```ts
  it('disables the loan button when the book is out of stock')
  it('shows an error message when the API request fails')
  ```
#### MSW Setup
```ts
// tests/mocks/handlers.ts
import { http, HttpResponse } from 'msw';
export const handlers = [
  http.get('/api/catalog/books', () =>
    HttpResponse.json({ items: [], total: 0, page: 1, page_size: 20 })
  ),
];
```
---
### 3.6 Accessibility (a11y)
- Target: **WCAG 2.1 AA** compliance
- Use **semantic HTML** – `<nav>`, `<main>`, `<article>`, `<button>`, `<form>`; never `<div onClick>`
- All interactive elements must be **fully keyboard navigable** (Tab, Enter, Space, Escape for modals)
- All non-decorative images must have descriptive `alt` attributes
- All form inputs must have associated `<label>` elements (via `htmlFor` or `aria-labelledby`)
- Colour must **never** be the only means of conveying information (loan status uses colour + text)
- Focus indicators must be visible – never use `outline: none` without a replacement
- Use `aria-live="polite"` for dynamic status updates (e.g. toast notifications)
- Automated accessibility check on every page:
  ```ts
  it('has no accessibility violations', async () => {
    const { container } = render(<BooksPage />);
    expect(await axe(container)).toHaveNoViolations();
  });
  ```
---
### 3.7 Performance
- **Route-level code splitting** via `React.lazy` + `Suspense` is mandatory
- TanStack Query `staleTime` per query type:
| Query | `staleTime` | Rationale |
|-------|------------|-----------|
| Book list | 30 s | Changes infrequently |
| Book availability | 0 | Must always be fresh before loan request |
| Loan list | 10 s | Changes after user actions |
| Overdue loans | 60 s | Admin view, not time-critical |
- Lighthouse performance score target: **> 90** on a production build
- No unused imports – ESLint `no-unused-vars` and Vite tree-shaking enforced
- Prefer `date-fns` for date formatting over heavier alternatives
---
### 3.8 Development Strategy
1. 🔴 **RED** – Write a failing test describing the desired behaviour
2. 🟢 **GREEN** – Write the minimal implementation to make it pass
3. 🔵 **REFACTOR** – Clean up, extract components, improve naming
- No component is committed without at least one passing test
- API clients are **regenerated** after every backend API change before new frontend work begins
- Feature branches per user story: `feature/FE-1-browse-books`, `feature/FE-3-request-loan`, etc.
---
### 3.9 Code Language
- All source code, comments, variable names, function names, component names, type names, constants, test descriptions and error messages must be written in **English**
- German text is not permitted anywhere in the codebase
- Exception: test data (e.g. user names like `"Alice Müller"`) may contain German characters
---
### 3.10 Environment Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_CATALOG_API_URL` | `http://localhost:8000` | Catalog Service base URL |
| `VITE_LOAN_API_URL` | `http://localhost:8001` | Loan Service base URL |
```bash
cp frontend/.env.example frontend/.env.local
```
Only variables prefixed with `VITE_` are exposed to the browser bundle by Vite.
---
## 4. User Stories
### FE-1 – Browse the Book Catalogue
| # | Acceptance Criterion |
|---|----------------------|
| 1 | `GET /books` is called on page load |
| 2 | Books are displayed as cards with title, author, genre, available count |
| 3 | A search input filters results by title, author or genre |
| 4 | A loading skeleton is shown while data is loading |
| 5 | An error message is shown if the API request fails |
| 6 | "No books found" is shown for an empty result |
### FE-2 – View Book Details
| # | Acceptance Criterion |
|---|----------------------|
| 1 | `GET /books/:isbn` and `GET /books/:isbn/availability` are called on page load |
| 2 | All metadata fields are displayed |
| 3 | Available count is shown with in-stock / out-of-stock indicator |
| 4 | "Request Loan" button is disabled when `available_count === 0` |
| 5 | A 404 page is shown if the ISBN does not exist |
### FE-3 – Request a Loan
| # | Acceptance Criterion |
|---|----------------------|
| 1 | `POST /loans` is called with `isbn` and the stored `user_id` |
| 2 | Response status `PENDING` is displayed immediately after submission |
| 3 | Form shows validation errors for missing or invalid fields |
| 4 | Network / API errors are shown as inline messages |
| 5 | Availability count updates after a successful loan request |
### FE-4 – View My Loans
| # | Acceptance Criterion |
|---|----------------------|
| 1 | `GET /loans?user_id=...` is called with the stored user ID |
| 2 | Each loan shows ISBN, status badge, due date |
| 3 | Status badges are colour-coded and include the status text |
| 4 | "Return" button is visible only for `ACTIVE` loans |
| 5 | Empty state message is shown when there are no loans |
### FE-5 – Return a Book
| # | Acceptance Criterion |
|---|----------------------|
| 1 | `POST /loans/:loan_id/return` is called on button click |
| 2 | Loan status updates to `RETURNED` in the UI without page reload |
| 3 | A success toast notification is shown |
| 4 | 404 / 409 responses show descriptive error messages |
### FE-6 – Register a User
| # | Acceptance Criterion |
|---|----------------------|
| 1 | Form validates `name` (required) and `email` (required, valid format via Zod) |
| 2 | `POST /users` is called on submit |
| 3 | Returned `user_id` is stored in context and `localStorage` via `useUser()` |
| 4 | Duplicate e-mail (409) shows "This e-mail is already registered" |
| 5 | After success, user is redirected to the book catalogue (`/`) |
### FE-7 – View Overdue Loans (Admin)
| # | Acceptance Criterion |
|---|----------------------|
| 1 | `GET /loans/overdue` is called on page load |
| 2 | Each row shows user ID, ISBN, due date, days overdue |
| 3 | Days overdue is highlighted in red when > 0 |
| 4 | "No overdue loans" is shown for an empty result |
### FE-8 – Log in as existing user
| # | Acceptance Criterion |
|---|----------------------|
| 1 | `GET /users?email=<email>` is called with the entered e-mail |
| 2 | On 200: user is stored via `useUser()` context, user is redirected to `/` |
| 3 | On 404: message "No account found for this e-mail. Register here." with link to `/register` |
| 4 | Form shows inline validation error when e-mail format is invalid |
| 5 | Visiting `/login` while already logged in redirects immediately to `/` |
### FE-UI-1 – Global Navigation Bar
| # | Acceptance Criterion |
|---|----------------------|
| 1 | NavBar is rendered on every page except `NotFoundPage` |
| 2 | Application name "LibraryHub" links to `/` |
| 3 | Navigation links for Books, My Loans, New Loan, Admin are always visible |
| 4 | When logged in: user name and Logout button are shown in the header |
| 5 | When logged out: Login and Register links are shown instead |
| 6 | The currently active route link is visually distinguished |
| 7 | Logout clears the session (context + localStorage) and redirects to `/` |
---
## 5. Dependencies (`package.json`)
### Runtime dependencies
| Package | Min version | Purpose |
|---------|-------------|---------|
| `react` | `^18.3` | UI framework |
| `react-dom` | `^18.3` | DOM renderer |
| `react-router-dom` | `^6.22` | Client-side routing |
| `@tanstack/react-query` | `^5.28` | Server state management |
| `react-hook-form` | `^7.51` | Form state management |
| `zod` | `^3.22` | Schema validation |
| `@hey-api/client-fetch` | `^0.2` | Generated API client runtime |
### Development dependencies
| Package | Min version | Purpose |
|---------|-------------|---------|
| `vite` | `^5.2` | Build tool + dev server |
| `typescript` | `^5.4` | Language |
| `@types/react` | `^18.3` | React type definitions |
| `@types/react-dom` | `^18.3` | React DOM type definitions |
| `tailwindcss` | `^3.4` | Utility-first CSS |
| `@hey-api/openapi-ts` | `^0.46` | API client generator |
| `vitest` | `^1.4` | Test runner (Vite-native) |
| `@vitest/coverage-v8` | `^1.4` | Coverage reporter |
| `@testing-library/react` | `^15.0` | Component testing utilities |
| `@testing-library/user-event` | `^14.5` | User interaction simulation |
| `@testing-library/jest-dom` | `^6.4` | Custom DOM matchers |
| `msw` | `^2.2` | API mocking at network level |
| `jest-axe` | `^8.0` | Automated accessibility testing |
| `eslint` | `^9.0` | Linter |
| `typescript-eslint` | `^7.3` | TypeScript ESLint rules |
| `prettier` | `^3.2` | Code formatter |
---
## 6. Out of Scope (MVP)
- JWT / session tokens / protected routes (authentication is e-mail lookup only)
- Password-based login
- Dark mode / theme switching
- Internationalisation (i18n / l10n)
- Push notifications for loan status changes
- Admin UI for adding or editing books
- E2E tests (Playwright / Cypress) – considered for a later phase
- PWA / offline support
- Mobile-native app
- Role-based access control (admin link is visible to all users)
