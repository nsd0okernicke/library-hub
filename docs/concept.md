# LibraryHub – Bibliotheksverleih-System

## Projektvision
**LibraryHub** ist ein einfaches, aber realistisches digitales Bibliothekssystem, mit dem Nutzer Bücher suchen, ausleihen und zurückgeben können. Das System besteht aus zwei unabhängigen Microservices, die über asynchrone Messaging (Event-Driven) kommunizieren. 
Ziel des Projekts ist es, Python-Basics zu vertiefen und gleichzeitig moderne Software-Architektur-Praktiken zu lernen:
	- Hexagonale Architektur (Ports & Adapters / Clean Architecture)
	- Microservices mit klar getrennten Bounded Contexts
	- Event-Driven Communication mit RabbitMQ
	- Asynchrone REST-Endpunkte mit FastAPI
	- Hohe Testabdeckung (> 90 %)
	- Containerisierung mit Docker und lokale Orchestrierung mit Minikube (später Cloud-Deployment)

Das Projekt ist bewusst überschaubar gehalten, damit der Fokus auf sauberer Architektur, Testen und DevOps liegt – nicht auf komplizierter Business-Logik.

## Entwicklungsstrategie

### Vorgehensweise
- **Beide Services werden parallel entwickelt** – jede Architekturschicht wird für `catalog-service` und `loan-service` gleichzeitig implementiert (erst alle Domain-Modelle, dann alle Ports, usw.)
- **Test-First-Ansatz (TDD):** Für jede Schicht werden zuerst die Tests geschrieben, bevor die eigentliche Implementierung folgt
- **Schicht-für-Schicht:** Die Entwicklung folgt der hexagonalen Schichtstruktur von innen nach außen: Domain → Ports → Application → Adapters → API

### Schritte (Übersicht)
| Schritt | Inhalt |
|---------|--------|
| 0 | `uv` global installieren |
| 1 | Python-Umgebungen mit `uv` initialisieren (pro Service) |
| 2 | Repository-Struktur aufsetzen (beide Services parallel) |
| 3 | Domain-Schicht: Tests → Implementierung (beide Services parallel) |
| 4 | Ports-Schicht: Contract-Tests → Interfaces (beide Services parallel) |
| 5 | Application-Schicht: Unit-Tests mit gemockten Ports → Use Cases (beide Services parallel) |
| 6 | Adapter-Schicht: Integrationstests via Testcontainers → Implementierung (beide Services parallel) |
| 7 | API-Schicht: API-Tests → FastAPI-Router (beide Services parallel) |
| 8 | Event Contract Tests (serviceübergreifend) |
| 9 | Infrastruktur (Docker Compose, Kubernetes) |

### Paketmanagement
- **Tool:** [`uv`](https://github.com/astral-sh/uv) – moderner, Rust-basierter Ersatz für `pip` + `venv` (10–100× schneller)
- Jeder Service erhält eine **eigene isolierte `.venv`** (kein gemeinsames Root-Environment)
- Dependencies werden pro Service in `pyproject.toml` unter `[project.dependencies]` und `[dependency-groups.dev]` verwaltet
- `uv pip compile` erzeugt ein `requirements.lock` für reproduzierbare Builds

## Bounded Contexts

### 1. Catalog Service (Buchkatalog & Verfügbarkeit)
**Verantwortlich für:**
	- Verwaltung aller Bücher (Metadaten)
	- Aktueller Buchbestand / Verfügbarkeit
	- Suche und Filter

**Datenbank:** PostgreSQL (`books`, `book_stock`)

**Domain Events (outgoing):**
	- `BookReserved`
	- `BookOutOfStock`

**Domain Events (incoming):**
	- `BookReturned` *(publiziert vom Loan Service → Catalog Service erhöht den Bestand)*

### 2. Loan Service (Ausleihen & Nutzerverwaltung)
**Verantwortlich für:**
	- Nutzer (einfach gehalten)
	- Ausleihvorgänge (loans)
	- Fristen und Überfälligkeiten
	- Starten einer Ausleihe

**Ausleihfrist:** `due_date` wird vom Loan Service beim Anlegen gesetzt: `heute + LOAN_DURATION_DAYS` (Standard: **28 Tage**, konfigurierbar via Umgebungsvariable `LOAN_DURATION_DAYS`)
	
**Datenbank:** PostgreSQL (`users`, `loans`)

**Domain Events (outgoing):**
	- `BookLoanRequested`
	- `BookReturned`

**Domain Events (incoming):**
	- `BookReserved` *(publiziert vom Catalog Service → Loan Status: PENDING → ACTIVE)*
	- `BookOutOfStock` *(publiziert vom Catalog Service → Loan Status: PENDING → REJECTED)*
	
## Kommunikation zwischen den Services

- **Messaging:** RabbitMQ (Exchange + Queues)
- **Pattern:** Publish-Subscribe mit Domain Events
- **Beispiel-Flow:**  
	1. Nutzer ruft `POST /loans` im Loan Service auf → sofortige Pending-Antwort  
	2. Loan Service publiziert `BookLoanRequested`  
	3. Catalog Service reserviert das Buch und publiziert `BookReserved` oder `BookOutOfStock`  
	4. Loan Service verarbeitet die Antwort und schließt die Ausleihe ab  
	5. Bei Rückgabe: `POST /loans/{id}/return` → `BookReturned` Event → Catalog Service erhöht Bestand

Dies ermöglicht **Eventual Consistency** und entkoppelt die Services stark.

## LoanStatus – Zustandsübergänge

```mermaid
stateDiagram-v2
    [*] --> PENDING : POST /loans\n(BookLoanRequested publiziert)
    PENDING --> ACTIVE : BookReserved Event empfangen
    PENDING --> REJECTED : BookOutOfStock Event empfangen
    ACTIVE --> RETURNED : POST /loans/{id}/return\n(BookReturned publiziert)
    REJECTED --> [*]
    RETURNED --> [*]
```

**Erlaubte Übergänge:**

| Von | Nach | Auslöser |
|---------|----------|-----------------------------------|
| `PENDING` | `ACTIVE` | `BookReserved`-Event empfangen |
| `PENDING` | `REJECTED` | `BookOutOfStock`-Event empfangen |
| `ACTIVE` | `RETURNED` | `POST /loans/{id}/return` |

**Nicht erlaubte Übergänge** (führen zu `HTTP 409 Conflict`):
- `RETURNED → *` (bereits zurückgegeben)
- `REJECTED → *` (bereits abgelehnt)
- `PENDING → RETURNED` (Ausleihe muss erst aktiv sein)

## High-Level Architektur

```mermaid
flowchart TD    
	subgraph "Catalog Service"
		A[FastAPI REST API] --> B[Application Services]        
		B --> C[Domain Model]        
		C <--> D[Ports: Repository, Message Publisher]        
		D --> E[Adapters: SQLAlchemy, RabbitMQ]        
		E <--> F[(PostgreSQL Catalog)]        
		E <--> G[RabbitMQ]    
	end
	
    subgraph "Loan Service"  
    	H[FastAPI REST API] --> I[Application Services]        
		I --> J[Domain Model]        
		J <--> K[Ports: Repository, Message Publisher/Consumer]        
		K --> L[Adapters: SQLAlchemy, RabbitMQ]        
		L <--> M[(PostgreSQL Loan)]        
		L <--> G[RabbitMQ]    
	end
	
    User[Nutzer / Frontend] <--> A    
	User <--> H
```

## Konfiguration & Umgebungsvariablen

Jeder Service enthält eine `.env.example`-Datei als Dokumentation aller Konfigurationswerte. Die eigentliche `.env`-Datei wird **nicht** ins Repository eingecheckt (`.gitignore`).

### `catalog-service/.env.example`
```env
# Datenbank
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/catalog_db

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
RABBITMQ_EXCHANGE=library.events
RABBITMQ_QUEUE_LOAN_REQUESTED=catalog.loan-requested
RABBITMQ_QUEUE_BOOK_RETURNED=catalog.book-returned
```

### `loan-service/.env.example`
```env
# Datenbank
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/loan_db

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
RABBITMQ_EXCHANGE=library.events
RABBITMQ_QUEUE_BOOK_RESERVED=loan.book-reserved
RABBITMQ_QUEUE_BOOK_OUT_OF_STOCK=loan.book-out-of-stock

# Geschäftslogik
LOAN_DURATION_DAYS=28
```
