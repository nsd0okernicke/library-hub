# LibraryHub Frontend – Concept

## Project Vision

The LibraryHub frontend is a **Single Page Application (SPA)** living as an independent application
inside the monorepo under `frontend/`. It consumes the REST APIs of the Catalog Service and the
Loan Service and provides library users and administrators with a clean, reactive user interface.

The frontend is intentionally kept simple – the focus is on **clean architecture**, **type safety**
and **modern frontend best practices**, mirroring the principles of the backend.

> **Related documents:**
> - Backend architecture: [`concept.md`](concept.md)
> - Backend requirements: [`requirements.md`](requirements.md)
> - Frontend requirements: [`frontend-requirements.md`](frontend-requirements.md)
> - API specs (live): http://localhost:8000/docs (Catalog) · http://localhost:8001/docs (Loan)

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Framework | **React 18** (Hooks only, no class components) | Largest ecosystem, first-class IntelliJ support |
| Language | **TypeScript 5** (`strict` mode) | Full type safety – equivalent to Python type hints |
| Build tool | **Vite 5** | Near-instant HMR, native ESM, minimal config |
| Routing | **React Router v6** | De-facto standard for React SPAs |
| Server state | **TanStack Query v5** (React Query) | Caching, loading/error states, background refetch |
| API clients | Generated via **`@hey-api/openapi-ts`** | Type-safe clients auto-generated from `/openapi.json` |
| Styling | **Tailwind CSS v3** | Utility-first, no separate CSS files needed |
| UI components | **shadcn/ui** | Accessible, unstyled Radix-based components |
| Forms | **React Hook Form + Zod** | Type-safe validation, minimal re-renders |
| Testing | **Vitest + React Testing Library** | Vite-native, Jest-compatible API |
| API mocking | **MSW (Mock Service Worker)** | Intercepts real HTTP requests in tests |
| Linting | **ESLint + typescript-eslint** | Static analysis |
| Formatting | **Prettier** | Consistent code style |
| Package manager | **npm** | Standard, IntelliJ-native support |

---

## Local Development Setup

The frontend follows the same principle as the backend services: **run natively, no Docker**.

```
# Step 1 – start infrastructure only
docker compose up -d

# Step 2 – start backend services natively
cd catalog-service && uv run uvicorn catalog.main:app --reload --port 8000   # Terminal 1
cd loan-service    && uv run uvicorn loan.main:app    --reload --port 8001   # Terminal 2

# Step 3 – start frontend natively
cd frontend && npm run dev    # Terminal 3  →  http://localhost:3000
```

The Vite dev server proxies all API calls to the backend services, eliminating CORS issues
completely during development:

```
/api/catalog/* → http://localhost:8000
/api/loan/*    → http://localhost:8001
```

Configured in `vite.config.ts`:

```ts
export default defineConfig({
  server: {
    proxy: {
      '/api/catalog': { target: 'http://localhost:8000', rewrite: path => path.replace(/^\/api\/catalog/, '') },
      '/api/loan':    { target: 'http://localhost:8001', rewrite: path => path.replace(/^\/api\/loan/, '') },
    },
  },
});
```

---

## Monorepo Structure

```
library-hub/
├── catalog-service/
├── loan-service/
├── frontend/                          ← New application
│   ├── src/
│   │   ├── api/                       ← Generated API clients – DO NOT edit manually
│   │   │   ├── catalog/               ← Generated from catalog-service /openapi.json
│   │   │   └── loan/                  ← Generated from loan-service /openapi.json
│   │   ├── components/                ← Reusable UI components
│   │   │   ├── ui/                    ← shadcn/ui base components (Button, Card, Badge, …)
│   │   │   ├── books/                 ← Book-specific components (BookCard, BookList, …)
│   │   │   ├── loans/                 ← Loan-specific components (LoanStatusBadge, LoanCard, …)
│   │   │   └── shared/                ← Cross-domain components (ErrorBoundary, LoadingSpinner, …)
│   │   ├── hooks/                     ← Custom React hooks (data fetching + local state)
│   │   │   ├── useBooks.ts
│   │   │   ├── useBookAvailability.ts
│   │   │   ├── useLoans.ts
│   │   │   └── useUsers.ts
│   │   ├── pages/                     ← Page components – one per route
│   │   │   ├── BooksPage.tsx
│   │   │   ├── BookDetailPage.tsx
│   │   │   ├── LoansPage.tsx
│   │   │   ├── NewLoanPage.tsx
│   │   │   └── AdminPage.tsx
│   │   ├── lib/                       ← Utility functions, helpers
│   │   │   ├── utils.ts
│   │   │   └── formatters.ts
│   │   ├── types/                     ← Shared TypeScript types (if not generated)
│   │   ├── App.tsx                    ← Root component + router setup
│   │   └── main.tsx                   ← Entry point
│   ├── public/                        ← Static assets
│   ├── tests/                         ← Tests – mirrors src/ structure
│   │   ├── components/
│   │   ├── hooks/
│   │   └── pages/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── .env.example
│   └── package.json
├── docs/
├── docker-compose.yml
└── README.md
```

---

## Architecture & Layering

The frontend follows a **feature-adjacent layered structure** that mirrors the hexagonal architecture
of the backend. The key principle is the same: **dependencies only point inward**.

```
┌─────────────────────────────────────────────────────────┐
│                        pages/                            │
│   BooksPage │ BookDetailPage │ LoansPage │ AdminPage    │
│              (routing, page layout, composition)         │
├─────────────────────────────────────────────────────────┤
│                      components/                         │
│   BookCard │ LoanStatusBadge │ SearchBar │ ErrorBoundary │
│                (pure UI, no data fetching)               │
├─────────────────────────────────────────────────────────┤
│                        hooks/                            │
│         useBooks │ useLoans │ useUsers │ …              │
│          (all data fetching + mutation logic)            │
├─────────────────────────────────────────────────────────┤
│                    TanStack Query                        │
│            (caching, loading/error states)               │
├─────────────────────────────────────────────────────────┤
│                  api/ (generated)                        │
│           catalog client │ loan client                   │
│                (raw HTTP calls, fully typed)             │
└─────────────────────────────────────────────────────────┘
```

### Layer Rules

| From | To | Allowed? | Reason |
|------|----|----------|--------|
| `pages/` | `components/` | ✅ | Pages compose components |
| `pages/` | `hooks/` | ✅ | Pages fetch data via hooks |
| `components/` | `hooks/` | ✅ | Components may use hooks for local state |
| `hooks/` | `api/` | ✅ | Hooks are the only consumers of generated clients |
| `components/` | `api/` | ❌ | Components must not call API directly |
| `pages/` | `api/` | ❌ | Pages must not call API directly |
| `api/` | `components/` | ❌ | Generated code has no UI dependency |
| `hooks/` | `components/` | ❌ | No circular dependency |

---

## API Client Generation

Type-safe API clients are generated directly from the OpenAPI specifications of both backend
services. The generated files live in `src/api/` and must **never be edited manually**.

```bash
# Regenerate clients (run after any backend API change)
npm run generate:api
```

Configured in `package.json`:

```json
{
  "scripts": {
    "generate:api": "openapi-ts --input http://localhost:8000/openapi.json --output src/api/catalog && openapi-ts --input http://localhost:8001/openapi.json --output src/api/loan"
  }
}
```

**Benefits:**
- No hand-written DTOs or API types
- TypeScript errors surface immediately when the backend API changes
- Request and response types are always in sync with the backend
- Reduces boilerplate significantly

---

## Pages & Navigation

| Route | Page | Description |
|-------|------|-------------|
| `/` | `BooksPage` | Book catalogue with search and filtering |
| `/books/:isbn` | `BookDetailPage` | Book details + availability + request loan |
| `/loans` | `LoansPage` | All loans of the current user |
| `/loans/new` | `NewLoanPage` | New loan request form |
| `/admin` | `AdminPage` | Overdue loans (admin view) |

---

## State Management Strategy

The frontend uses **no global state management library** (no Redux, no Zustand) for server state.
Instead:

| State type | Solution | Rationale |
|------------|----------|-----------|
| Server data (books, loans, …) | **TanStack Query** | Automatic caching, stale-while-revalidate, deduplication |
| Local UI state (modal open, input value) | **React useState / useReducer** | Minimal, co-located with the component |
| Cross-cutting UI state (current user ID) | **React Context** | Only for truly global, rarely changing values |
| Form state | **React Hook Form** | Optimised for forms, integrates with Zod |

**Rules:**
- Never put server data into `useState` – always use TanStack Query
- Keep `useContext` usage minimal – prefer passing props or using hooks
- Optimistic updates for mutations (e.g. return loan) to improve perceived performance

---

## Component Design Principles

### Single Responsibility
Each component does exactly one thing. A `BookCard` displays book data. A `SearchBar` captures
input. A `LoanStatusBadge` renders a coloured badge. No component does all three.

### Props Design
- Prefer **explicit props** over spreading objects (`...props`)
- Define **prop types via TypeScript interfaces**, never `any`
- Use **default props** sparingly – prefer required props + explicit `undefined`

```tsx
// Good
interface BookCardProps {
  isbn: string;
  title: string;
  author: string;
  availableCount: number;
  onLoanRequest: (isbn: string) => void;
}

// Bad
const BookCard = (props: any) => { ... }
```

### Component Size
- A component file should not exceed **150 lines** (excluding types/imports)
- If a component grows beyond that, extract sub-components

### Co-location
- Tests live next to the component or in a mirrored `tests/` structure
- Keep styles (Tailwind classes), logic (hooks) and markup in the same file where possible

---

## Error Handling Strategy

| Scenario | Handling |
|----------|----------|
| API request fails | TanStack Query `error` state → show `ErrorMessage` component |
| Form validation fails | Zod + React Hook Form → inline field errors |
| Unexpected render error | `ErrorBoundary` component wrapping each page |
| Network offline | TanStack Query retry logic + user-visible toast notification |
| 404 route | Dedicated `NotFoundPage` component |

---

## Development Workflow (TDD-Adapted)

The frontend adopts the same Red → Green → Refactor cycle as the backend:

| Phase | Description |
|-------|-------------|
| 🔴 **RED** | Write a component or hook test – it must **fail** before implementation |
| 🟢 **GREEN** | Write the minimal implementation to make the test pass |
| 🔵 **REFACTOR** | Clean up, extract sub-components, improve naming |

**Mutation Testing** does not apply to the frontend (no `mutmut` for TypeScript). Instead, the
focus is on high **component coverage** and thorough **user interaction tests** with
React Testing Library.

---

## Testing Strategy

| Test type | Tool | What is tested |
|-----------|------|----------------|
| Unit tests (hooks) | Vitest + `@testing-library/react-hooks` | Data fetching logic, state transitions |
| Component tests | Vitest + React Testing Library | Rendering, user interactions, conditional display |
| Page tests | Vitest + RTL + MSW | Full page behaviour with mocked API responses |
| Accessibility tests | `jest-axe` | WCAG 2.1 AA violations caught automatically |

**Testing principles:**
- Test **behaviour**, not implementation (`getByRole`, `getByText` over `getByTestId`)
- Never test React internals (state, refs) – only the DOM output
- MSW mocks at the **network level**, not the module level
- One `describe` block per component, one `it` per user behaviour

---

## IntelliJ Setup

The frontend is configured as a **separate module** inside the existing IntelliJ project:

1. `File → Project Structure → Modules → + → Import Module → frontend/`
2. Select **"Create module from existing sources"**
3. Module type: **JavaScript / Node.js** (requires Node.js plugin)
4. Add run configuration: `npm run dev` in the `frontend/` working directory
5. TypeScript service: IntelliJ auto-detects `frontend/tsconfig.json`
6. ESLint: `Languages & Frameworks → JavaScript → Code Quality Tools → ESLint → Automatic ESLint configuration`
7. Prettier: `Languages & Frameworks → JavaScript → Prettier → Automatic Prettier configuration`
8. Vitest: add a **Vitest** run configuration pointing to `frontend/vitest.config.ts`

