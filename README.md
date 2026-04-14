# LibraryHub 📚

A realistic, event-driven library management system built with Python – designed as a learning project for **hexagonal architecture**, **microservices**, and **modern Python best practices**.

---

## What is LibraryHub?

LibraryHub lets library users search for books, request loans and return them. Behind the scenes two independent microservices coordinate via asynchronous messaging (RabbitMQ) – no direct service-to-service calls.

```
┌─────────────────────┐        RabbitMQ        ┌──────────────────────┐
│   Catalog Service   │ ◄───────────────────── │    Loan Service      │
│                     │                         │                      │
│  • Book catalogue   │ ──────────────────────► │  • Loan lifecycle    │
│  • Stock tracking   │   BookReserved /         │  • User management   │
│  • REST API :8000   │   BookOutOfStock         │  • REST API :8001    │
└─────────────────────┘                         └──────────────────────┘
        │                                                  │
   PostgreSQL                                         PostgreSQL
  (catalog_db)                                        (loan_db)
```

---

## Tech Stack

| Layer         | Technology                              |
|---------------|-----------------------------------------|
| Language      | Python 3.11+                            |
| API           | FastAPI + Uvicorn                       |
| Database      | PostgreSQL (one DB per service)         |
| ORM           | SQLAlchemy 2.0 async + Alembic          |
| Messaging     | RabbitMQ + aio-pika                     |
| Package mgr   | [uv](https://github.com/astral-sh/uv)  |
| Testing       | pytest + pytest-asyncio + Testcontainers|
| Coverage      | pytest-cov (target: > 90 %)            |
| Mutation test | mutmut                                  |

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
├── docs/
│   ├── concept.md            # Architecture & big picture
│   └── requirements.md       # Functional & non-functional requirements
└── docker-compose.yml        # Local infrastructure (PostgreSQL + RabbitMQ)
```

---

## Getting Started

### Prerequisites

- Python 3.11+
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

### 3 — Start the services

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

### 4 — Explore the APIs

| Service | Swagger UI | ReDoc |
|---------|-----------|-------|
| Catalog | http://localhost:8000/docs | http://localhost:8000/redoc |
| Loan    | http://localhost:8001/docs | http://localhost:8001/redoc |

---

### 5 — Load sample data (optional)

```bash
docker exec -i libraryhub-catalog-db \
  psql -U catalog -d catalog_db \
  < catalog-service/seed_books.sql
```

This inserts 10 real books with valid ISBNs and stock counts.

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

```bash
# Catalog Service – unit + API tests
cd catalog-service
uv run pytest tests/ --ignore=tests/integration

# Loan Service – unit + API tests
cd loan-service
uv run pytest tests/ --ignore=tests/integration
```

Current status:

| Service | Tests | Coverage |
|---------|-------|----------|
| Catalog | 105 ✅ | 100 % |
| Loan    | 124 ✅ | 99 % |

### Mutation Testing

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

Both services follow **Hexagonal Architecture (Ports & Adapters)**:

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

---

## Development Workflow (TDD)

Every feature follows the strict Red → Green → Refactor → Mutate cycle:

| Phase | Description |
|-------|-------------|
| 🔴 **RED** | Write tests first – they must **fail** before any implementation exists |
| 🟢 **GREEN** | Write the minimal implementation to make tests pass |
| 🔵 **REFACTOR** | Clean up code – tests stay green, no new behaviour added |
| 🧬 **MUTATE** | Run `mutmut` – mutation score must stay ≥ 80 % for `domain/` and `application/` |

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

- [`docs/concept.md`](docs/concept.md) – Architecture decisions, development strategy, step-by-step plan
- [`docs/requirements.md`](docs/requirements.md) – Functional & non-functional requirements, tech stack



