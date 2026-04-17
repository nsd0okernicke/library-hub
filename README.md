# LibraryHub 📚

A realistic, event-driven library management system built with Python and React – designed as a learning project for **hexagonal architecture**, **microservices**, **TDD** and **modern full-stack best practices**.

---

## What is LibraryHub?

LibraryHub lets library users search for books, request loans and return them. A **React SPA** provides the user interface, while two independent Python microservices coordinate via asynchronous messaging (RabbitMQ) – no direct service-to-service calls.

```
                    ┌──────────────────────────────────────┐
                    │        React Frontend :3000          │
                    │     TypeScript  +  Tailwind CSS      │
                    │     (Vite dev server + proxy)        │
                    └──────────────┬───────────┬───────────┘
                                   │           │
                            /api/catalog    /api/loan
                                   │           │
               ┌───────────────────▼──┐   ┌────▼──────────────────┐
               │    Catalog Service   │   │     Loan Service      │
               │        :8000         │   │         :8001         │
               │    Books + Stock     │   │    Loans + Users      │
               └─┬────────┬───────────┘   └───────────┬─────────┬─┘
                 │        │                           │         │
                 │        │       ┌───────────┐       │         │
                 │        └──────►│ RabbitMQ  │◄──────┘         │
                 │                │  (topic   │                 │
                 │                │ exchange: │                 │
                 │                │ library.  │                 │
                 │                │  events)  │                 │
                 │                └───────────┘                 │ 
                 │                                              │                
             PostgreSQL                                     PostgreSQL
            (catalog_db)                                    (loan_db)
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
├── k8s/
│   ├── infra/                # Kubernetes manifests – infrastructure
│   │   ├── secrets.yaml      # DB passwords & RabbitMQ credentials
│   │   ├── catalog-db.yaml   # PostgreSQL for Catalog Service
│   │   ├── loan-db.yaml      # PostgreSQL for Loan Service
│   │   └── rabbitmq.yaml     # RabbitMQ broker
│   ├── apps/                 # Kubernetes manifests – application layer
│   │   ├── configmap.yaml    # Service URLs (K8s-internal hostnames)
│   │   ├── catalog-service.yaml
│   │   ├── loan-service.yaml
│   │   ├── frontend.yaml     # nginx serving the React SPA + API proxy
│   │   └── seed-job.yaml     # One-off Job to populate the book catalogue
│   └── ingress.yaml          # Ingress → libraryhub.local
├── deploy.ps1                # One-shot deploy script for Minikube (Windows)
└── docker-compose.yml        # Local infrastructure (PostgreSQL + RabbitMQ)
```

### Infrastructure

| Layer         | Technology                              |
|---------------|-----------------------------------------|
| Containers    | Docker Desktop                          |
| Orchestration | Kubernetes (Minikube)                   |
| API Proxy     | nginx (inside frontend container)       |
| CI deploy     | `deploy.ps1` (PowerShell, Windows)      |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20 LTS+
- [uv](https://github.com/astral-sh/uv) — install once globally:
  ```bash
  pip install uv
  ```
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for local infrastructure and Minikube)
- [Minikube](https://minikube.sigs.k8s.io/docs/start/) (for Kubernetes deployment)
- [kubectl](https://kubernetes.io/docs/tasks/tools/) (bundled with Docker Desktop or installed separately)

There are two ways to run LibraryHub locally:

| Mode | When to use |
|------|-------------|
| **Local dev** (docker-compose + uv) | Day-to-day development, fast reload, debugger |
| **Kubernetes** (Minikube) | Testing the full containerised stack |

---

### Option A — Local Development (docker-compose + uv)

#### A1 — Start the infrastructure

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

#### A2 — Set up the virtual environments

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

#### A3 — Start the backend services

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

#### A4 — Start the frontend

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

#### A5 — Explore the APIs

| Service | Swagger UI | ReDoc |
|---------|-----------|-------|
| Catalog | http://localhost:8000/docs | http://localhost:8000/redoc |
| Loan    | http://localhost:8001/docs | http://localhost:8001/redoc |

---

#### A6 — Load sample data (optional)

```bash
docker exec -i libraryhub-catalog-db \
  psql -U catalog -d catalog_db \
  < catalog-service/seed_books.sql
```

This inserts 10 real books with valid ISBNs and stock counts.

---

### Option B — Kubernetes (Minikube)

Runs the full production-like stack in a local Kubernetes cluster – all services containerised, nginx as reverse proxy, PostgreSQL and RabbitMQ as Pods with persistent volumes.

#### Prerequisites

- [Minikube](https://minikube.sigs.k8s.io/docs/start/) installed
- Docker Desktop running

> **Windows note – MINIKUBE_HOME:**  
> If Minikube is installed in `C:\Program Files\...`, set `MINIKUBE_HOME` to a user-writable path to avoid permission errors:
> ```powershell
> # Run as Administrator (one-time):
> [System.Environment]::SetEnvironmentVariable("MINIKUBE_HOME", $null, "Machine")
> # Then in normal PowerShell:
> [System.Environment]::SetEnvironmentVariable("MINIKUBE_HOME", "$env:USERPROFILE\.minikube", "User")
> ```

#### B1 — Deploy everything

```powershell
# Stop local compose infrastructure first
docker compose down

# Deploy to Minikube (builds images, starts cluster, applies all manifests)
.\deploy.ps1
```

The script will:
1. Build all 3 Docker images locally (with internet access)
2. Start a fresh Minikube cluster (docker driver, 4 CPUs, 4 GB RAM)
3. Enable the nginx Ingress addon
4. Load images into Minikube via SSH (`docker save` → `minikube cp` → `docker load`)
5. Apply all `k8s/infra/` manifests and wait for DBs + RabbitMQ to be ready
6. Apply all `k8s/apps/` manifests and wait for services to be ready
7. Run the catalog seed Job (10 sample books)
8. Print the URL and required `hosts` entry

#### B2 — Access the application

> The Minikube Docker driver on Windows does **not** expose the cluster IP directly to the Windows host. Use one of these options:

**Option 1 – Port-forward (simplest, no setup):**
```powershell
kubectl port-forward svc/frontend 8080:80
```
Open → **http://localhost:8080**

**Option 2 – `minikube tunnel` (persistent, nice URL):**
```powershell
# 1. Add hosts entry (run as Administrator, one-time):
Add-Content "C:\Windows\System32\drivers\etc\hosts" "127.0.0.1  libraryhub.local"

# 2. Keep tunnel running in a separate terminal:
minikube tunnel
```
Open → **http://libraryhub.local**

#### B3 — Useful Kubernetes commands

```powershell
# Check all pods
kubectl get pods

# Follow logs of a service
kubectl logs deployment/catalog-service -f
kubectl logs deployment/loan-service -f

# RabbitMQ Management UI (guest/guest)
kubectl port-forward svc/rabbitmq 15672:15672
# → http://localhost:15672

# Re-run seed job
kubectl delete job catalog-seed
kubectl apply -f k8s/apps/seed-job.yaml

# Tear down the cluster completely
minikube delete
```

#### B4 — Kubernetes Architecture

```
                ┌─────────────────────────────────────────┐
                │          Ingress (nginx)                 │
                │      libraryhub.local → frontend:80      │
                └───────────────────┬─────────────────────┘
                                    │
                          ┌─────────▼──────────┐
                          │   frontend Pod      │
                          │   nginx:1.27        │
                          │   /api/catalog/ ────┼──► catalog-service:8000
                          │   /api/loan/    ────┼──► loan-service:8001
                          └─────────────────────┘

  catalog-service:8000          loan-service:8001
         │                              │
         └──────────► rabbitmq:5672 ◄───┘
         │                              │
    catalog-db:5432              loan-db:5432
    (PersistentVolume)           (PersistentVolume)
```

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
| Catalog | 106 ✅ | 98 % |
| Loan    | 133 ✅ | 99 % |

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
| Loan    | 100 % (142/142 killed) |

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
