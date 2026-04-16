# LibraryHub 📚

A realistic, event-driven library management system built with Python and React – designed as a learning project for **hexagonal architecture**, **microservices**, **TDD** and **modern full-stack best practices**.

---

## What is LibraryHub?

LibraryHub lets library users search for books, request loans and return them. A **React SPA** provides the user interface, while two independent Python microservices coordinate via asynchronous messaging (RabbitMQ) – no direct service-to-service calls.

```
┌──────────────────────────┐
│   React Frontend :3000   │  (Vite dev server with proxy)
│   TypeScript + Tailwind  │
└────────┬────────┬─────────┘
         │        │
    /api/catalog  /api/loan
         │        │
┌────────▼──────┐  ┌────────▼──────────┐        RabbitMQ
│ Catalog Svc   │  │   Loan Service    │ ◄──────────────────►
│ :8000         │  │   :8001           │
│ Books + Stock │  │ Loans + Users     │
└───────────────┘  └───────────────────┘
       │                    │
  PostgreSQL           PostgreSQL
 (catalog_db)          (loan_db)
```

---

## Tech Stack

### Backend

| Layer         | Technology                              |
|---------------|-----------------------------------------|
| Language      | Python 3.11+                            |
| API           | FastAPI + Uvicorn                       |
| Database      | PostgreSQL (one DB per service)         |
| ORM           | SQLAlchemy 2.0 async                    |
| Messaging     | RabbitMQ + aio-pika                     |
| Package mgr   | [uv](https://github.com/astral-sh/uv)  |
| Testing       | pytest + pytest-asyncio + Testcontainers|
| Coverage      | pytest-cov (target: > 90 %)            |
| Mutation test | mutmut                                  |

### Frontend

| Layer         | Technology                              |
|---------------|-----------------------------------------|
| Framework     | React 18 (Hooks only)                   |
| Language      | TypeScript 5 (`strict` mode)            |
| Build tool    | Vite 5                                  |
| Routing       | React Router v6                         |
| Styling       | Tailwind CSS v3                         |
| Forms         | React Hook Form + Zod                   |
| Testing       | Vitest + React Testing Library + MSW v2 |
| Package mgr   | npm                                     |

---

## Project Structure

```
library-hub/
├── catalog-service/          # Book catalogue & stock management
│   ├── src/catalog/
│   │   ├── domain/           # Entities, value objects, ports
│   │   ├── application/      # Use cases
│   │   └── infrastructure/   # FastAPI routers, SQLAlchemy, RabbitMQ
│   └── tests/
├── loan-service/             # Loan lifecycle & user management
│   ├── src/loan/
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   └── tests/
├── frontend/                 # React SPA
│   ├── src/
│   │   ├── components/       # Reusable UI components (NavBar, Toast, …)
│   │   ├── hooks/            # Custom hooks (useBooks, useLoans, useUser, …)
│   │   ├── pages/            # One component per route
│   │   ├── types/            # Shared TypeScript types
│   │   └── App.tsx           # Router + layout setup
│   └── tests/                # Vitest + RTL + MSW tests
├── docs/
│   ├── concept.md            # Backend architecture & big picture
│   ├── requirements.md       # Backend functional & non-functional requirements
│   ├── frontend-concept.md   # Frontend architecture & patterns
│   └── frontend-requirements.md  # Frontend user stories & requirements
└── docker-compose.yml        # Local infrastructure (PostgreSQL + RabbitMQ)
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20 LTS+
- [uv](https://github.com/astral-sh/uv) — install once globally:
  ```bash
  pip install uv
  ```
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for the local infrastructure)

---

### 1 — Start the infrastructure

```bash
docker compose up -d
```

This starts:
| Container | Port | Description |
|-----------|------|-------------|
| `libraryhub-catalog-db` | 5432 | PostgreSQL for Catalog Service |
| `libraryhub-loan-db` | 5433 | PostgreSQL for Loan Service |
| `libraryhub-rabbitmq` | 5672 / 15672 | RabbitMQ + Management UI |

RabbitMQ Management UI → http://localhost:15672 (user: `guest` / pw: `guest`)

---

### 2 — Set up the virtual environments

Each service has its own isolated environment managed by `uv`:

```bash
# Catalog Service
cd catalog-service
uv sync

# Loan Service
cd ../loan-service
uv sync
```

---

### 3 — Start the backend services

Open two terminals:

```bash
# Terminal 1 – Catalog Service (port 8000)
cd catalog-service
uv run uvicorn catalog.main:app --reload --port 8000
```

```bash
# Terminal 2 – Loan Service (port 8001)
cd loan-service
uv run uvicorn loan.main:app --reload --port 8001
```

DB tables are created automatically on first startup (no Alembic migration needed for local dev).

---

### 4 — Start the frontend

```bash
# Terminal 3 – React SPA (port 3000)
cd frontend
npm install   # first time only
npm run dev
```

Open → http://localhost:3000

The Vite dev server proxies all API calls automatically – no CORS configuration needed:

| Prefix | Forwarded to |
|--------|-------------|
| `/api/catalog/*` | http://localhost:8000 |
| `/api/loan/*`    | http://localhost:8001 |

---

### 5 — Explore the APIs

| Service | Swagger UI | ReDoc |
|---------|-----------|-------|
| Catalog | http://localhost:8000/docs | http://localhost:8000/redoc |
| Loan    | http://localhost:8001/docs | http://localhost:8001/redoc |

---

### 6 — Load sample data (optional)

```bash
docker exec -i libraryhub-catalog-db \
  psql -U catalog -d catalog_db \
  < catalog-service/seed_books.sql
```

This inserts 10 real books with valid ISBNs and stock counts.

---

## Frontend Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Book Catalogue | Browse all books, search by title / author / genre |
| `/books/:isbn` | Book Detail | Full metadata, availability, request loan button |
| `/loans/new` | New Loan | Request a loan (pre-filled ISBN from detail page) |
| `/loans` | My Loans | All loans for the logged-in user, return action |
| `/login` | Login | Sign in with your e-mail address |
| `/register` | Register | Create a new account |
| `/admin` | Admin | View all overdue loans |

---

## Event-Driven Flow

The complete loan lifecycle is fully event-driven:

```
POST /loans  (Loan Service)
  → publishes  BookLoanRequested
      → Catalog Service consumes it
      → ReserveBookUseCase: stock - 1
      → publishes  BookReserved  (or BookOutOfStock)
          → Loan Service consumes it
          → ActivateLoanUseCase: loan status PENDING → ACTIVE
              (or RejectLoanUseCase: PENDING → REJECTED)

POST /loans/{id}/return  (Loan Service)
  → publishes  BookReturned
      → Catalog Service consumes it
      → ReturnBookUseCase: stock + 1
```

> Both services start gracefully even without RabbitMQ running (e.g. in unit tests).
> A warning is logged and HTTP endpoints remain fully functional.

---

## Running the Tests

### Backend

```bash
# Catalog Service – unit + API tests
cd catalog-service
uv run pytest tests/ --ignore=tests/integration

# Loan Service – unit + API tests
cd loan-service
uv run pytest tests/ --ignore=tests/integration
```

| Service | Tests | Coverage |
|---------|-------|----------|
| Catalog | 105 ✅ | 100 % |
| Loan    | 129 ✅ | 99 % |

### Frontend

```bash
cd frontend
npm test -- --run        # run once
npm test                 # watch mode
```

| | Tests | 
|-|-------|
| Frontend | 53 ✅ |

### Mutation Testing (Backend)

```bash
# From the repository root (requires WSL)
bash mutmut.sh catalog
bash mutmut.sh loan
```

| Service | Mutation Score |
|---------|---------------|
| Catalog | 100 % (120/120 killed) |
| Loan    | 100 % (139/139 killed) |

---

## Architecture

### Backend – Hexagonal Architecture (Ports & Adapters)

```
┌──────────────────────────────────────────────────┐
│                  infrastructure/                  │
│   FastAPI routers │ SQLAlchemy │ RabbitMQ adapter │
│                         │                         │
│              application/ (use cases)             │
│                         │                         │
│         domain/ (entities, value objects)         │
│              domain/ports/ (interfaces)           │
└──────────────────────────────────────────────────┘
```

- **Domain** – pure Python, no framework dependencies
- **Ports** – abstract interfaces defined by the domain, implemented in infrastructure
- **Application** – use cases that orchestrate domain objects via ports
- **Infrastructure** – adapters: FastAPI, SQLAlchemy repositories, RabbitMQ publisher/consumer

### Frontend – Layered Architecture

```
┌──────────────────────────────────────┐
│         NavBar + pages/              │  ← routing & page layout
├──────────────────────────────────────┤
│            components/               │  ← pure UI, no data fetching
├──────────────────────────────────────┤
│              hooks/                  │  ← all data fetching & mutations
├──────────────────────────────────────┤
│           fetch() / MSW              │  ← raw HTTP via Vite proxy
└──────────────────────────────────────┘
```

---

## Development Workflow (TDD)

Every feature – backend and frontend – follows the strict Red → Green → Refactor cycle:

| Phase | Description |
|-------|-------------|
| 🔴 **RED** | Write tests first – they must **fail** before any implementation exists |
| 🟢 **GREEN** | Write the minimal implementation to make tests pass |
| 🔵 **REFACTOR** | Clean up code – tests stay green, no new behaviour added |
| 🧬 **MUTATE** | Run `mutmut` – mutation score must stay ≥ 80 % for backend `domain/` and `application/` |

---

## Configuration

Each service reads its configuration from a `.env` file in its directory.
Copy the example and adjust as needed:

```bash
cp catalog-service/.env.example catalog-service/.env
cp loan-service/.env.example    loan-service/.env
```

Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async PostgreSQL connection string |
| `RABBITMQ_URL` | `amqp://guest:guest@localhost:5672/` | RabbitMQ connection |
| `RABBITMQ_EXCHANGE` | `library.events` | Topic exchange name |
| `LOAN_DURATION_DAYS` | `28` | Default loan period in days (Loan Service only) |

---

## Documentation

Full architecture and requirements are documented in [`/docs`](docs/):

- [`docs/concept.md`](docs/concept.md) – Backend architecture decisions, development strategy
- [`docs/requirements.md`](docs/requirements.md) – Backend functional & non-functional requirements
- [`docs/frontend-concept.md`](docs/frontend-concept.md) – Frontend architecture, patterns, tech decisions
- [`docs/frontend-requirements.md`](docs/frontend-requirements.md) – Frontend user stories & acceptance criteria
