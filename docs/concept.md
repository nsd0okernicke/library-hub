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
- **Schicht-für-Schicht:** Die Entwicklung folgt der hexagonalen Schichtstruktur von innen nach außen: Domain → Application → Infrastructure
- **Sprache im Code (verbindlich):** Alle Kommentare, Docstrings, Variablen- und Funktionsnamen sowie Fehlermeldungen im Quellcode werden **ausschließlich auf Englisch** verfasst. Deutsche Texte sind im Code nicht erlaubt – auch nicht in Tests. Ausnahme: Testdaten (z. B. Nutzernamen wie „Alice Müller") dürfen Deutsche Sonderzeichen enthalten.

### TDD-Zyklus: Red → Green → Refactor → Mutate

Für jede Einheit (Klasse, Use Case, Adapter, Endpoint) wird der folgende Zyklus **strikt eingehalten**:

```
🔴 RED    – Tests schreiben, die das gewünschte Verhalten beschreiben.
            Tests werden ausgeführt → müssen FEHLSCHLAGEN (ImportError /
            AssertionError / NotImplementedError). Kein Code existiert noch.

🟢 GREEN  – Minimale Implementierung schreiben, die die Tests zum Bestehen
            bringt. Kein Over-Engineering – nur das Nötigste.
            Tests werden erneut ausgeführt → müssen alle BESTEHEN.

🔵 REFACTOR – Code aufräumen, Duplikate entfernen, Lesbarkeit verbessern.
              Tests bleiben grün. Kein neues Verhalten wird hinzugefügt.

🧬 MUTATE – Mutation Testing mit `mutmut` ausführen.
            Ziel: Mutation Score > 80 % pro Modul.
            Überlebende Mutanten → fehlende/schwache Assertions identifizieren
            → neue Tests schreiben (→ zurück zu 🔴 RED für die Lücke).
```

**Was ist Mutation Testing?**  
Ein Tool verändert automatisch den Produktionscode an vielen Stellen – jede Änderung heißt **Mutant**
(z.B. `>` → `>=`, `+` → `-`, `True` → `False`, `"BookReserved"` → `"BookReserved_"`).
Wird ein Mutant von keinem Test erkannt (alle Tests bleiben grün), hat die Testsuite eine inhaltliche
Lücke – auch wenn die Coverage 100 % beträgt.

```
Mutation Score = killed mutants / (killed + survived) × 100
```

**Wann wird 🧬 MUTATE ausgeführt?**
- Nach jedem abgeschlossenen 🔵 REFACTOR-Schritt für `domain/` und `application/`
- Fokus auf reine Businesslogik (kein I/O, kein Framework-Code)
- `infrastructure/` wird durch Integrations- und API-Tests abgedeckt; Mutation Testing dort ist optional

**Verbindliche Schwellwerte:**

| Paket | Mindest-Mutation-Score |
|---|---|
| `domain/` | ≥ 80 % |
| `application/` | ≥ 80 % |
| `infrastructure/` | optional |

Score < 80 % gilt als Qualitätsmangel und muss durch zusätzliche Tests behoben werden,
bevor die nächste Schicht begonnen wird.

**Verbindliche Regel:** Zwischen 🔴 RED und 🟢 GREEN darf **kein Produktionscode** geschrieben werden. Die fehlgeschlagenen Tests werden dokumentiert (Screenshot oder Terminal-Output), bevor die Implementierung beginnt.

### Schritte (Übersicht)
| Schritt | Inhalt |
|---------|--------|
| 0 | `uv` global installieren |
| 1 | Python-Umgebungen mit `uv` initialisieren (pro Service) |
| 2 | Repository-Struktur aufsetzen (beide Services parallel) |
| 3 | Domain-Schicht: Tests → Implementierung (beide Services parallel) |
| 4 | Ports-Schicht: Contract-Tests → Interfaces unter `domain/ports/` (beide Services parallel) |
| 5 | Application-Schicht: Unit-Tests mit gemockten Ports → Use Cases (beide Services parallel) |
| 5.5 | Mutation Testing: `domain/` + `application/` beider Services (`mutmut`, Score ≥ 80 %) |
| 6 | Infrastructure-Schicht: Integrationstests via Testcontainers → SQLAlchemy-Adapter, RabbitMQ-Adapter (beide Services parallel) |
| 6a | Echte Repository-Implementierungen (SQLAlchemy) in infrastructure/db/ anlegen und mit Use Cases verdrahten |
| 7 | Infrastructure-Schicht API: API-Tests → FastAPI-Router + Pydantic-Schemas + Mapping (beide Services parallel) |
| 8 | Event Contract Tests (serviceübergreifend) |
| 9 | Infrastruktur (Docker Compose, Kubernetes) |

### Schritt 6: Infrastruktur-Schicht (Integrationstests, Adapter)

#### Voraussetzungen
- Domain-, Ports- und Application-Schicht für beide Services sind implementiert und getestet.
- Mutation Testing für Domain und Application mit Score ≥ 80 % durchgeführt und dokumentiert.
- Paketstruktur und Schichtenregeln gemäß Konzept umgesetzt.
- User Stories/technische Stories für Infrastruktur-Schicht sind spezifiziert.
- Testumgebung für Integrationstests (Testcontainers, Docker, RabbitMQ, PostgreSQL) ist vorbereitet.
- Alle bisherigen Schritte und Ergebnisse sind dokumentiert.

#### ToDo-Checkliste vor Start Schritt 6
1. Sind alle Schnittstellen (Ports) ausreichend für die Infrastruktur-Adapter spezifiziert?
2. Gibt es offene technische Abhängigkeiten (z.B. Testcontainer-Konfiguration, Netzwerkzugriffe)?
3. Müssen weitere User Stories für Infrastruktur/Adapter ergänzt werden?

---

## Infrastruktur: Repository-Implementierungen (SQLAlchemy)

- Für jeden Output-Port (z.B. BookRepository, BookStockRepository) wird eine konkrete Implementierung in `infrastructure/db/` angelegt:
  - `sqlalchemy_book_repository.py`
  - `sqlalchemy_book_stock_repository.py`
- Diese Klassen nutzen SQLAlchemy (async) für den Zugriff auf PostgreSQL.
- Das Mapping Domain ↔ ORM-Model erfolgt ausschließlich in diesen Klassen.
- Die Dependency Injection im API-Layer wird so gestaltet, dass im Produktivbetrieb die echten Repositories verwendet werden (z.B. via Factory, Settings oder DI-Framework).
- Für Tests/Entwicklung können weiterhin In-Memory-Fakes verwendet werden.

**Beispielstruktur:**

```
└── infrastructure/
    └── db/
        ├── models.py                  # SQLAlchemy-ORM-Modelle
        ├── sqlalchemy_book_repository.py
        ├── sqlalchemy_book_stock_repository.py
        └── fake_repositories.py       # Nur für Tests/Entwicklung
```

**Hinweis:**
- Die Implementierung der echten Repositories ist Voraussetzung für Integrationstests und den produktiven Betrieb.
- Die Repositories werden in Schritt 6a (nach den Fakes, vor den Integrationstests) implementiert.

---

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

## Paketstruktur (3-Pakete-Layout)

Jeder Service ist in **drei Hauptpakete** gegliedert, die der Schichtenregel entsprechen: Abhängigkeiten zeigen immer von außen nach innen, niemals umgekehrt.

```
<service>/src/<service_name>/
│
├── domain/                     ← Innerste Schicht – keine Abhängigkeiten nach außen
│   ├── book.py / loan.py / …   │  Entities, Value Objects (z. B. Isbn), reine Businesslogik
│   ├── events/                 │  Domain Events (Datenklassen)
│   └── ports/                  │  Output-Port-Interfaces (ABCs) – definiert von der Domain,
│       ├── book_repository.py  │  implementiert in infrastructure/
│       └── message_publisher.py│
│
├── application/                ← Mittlere Schicht – kennt domain/, nutzt domain/ports/
│   └── <use_case>.py           │  Use Cases / Application Services (orchestrieren Domain-Objekte
│                               │  und rufen Ports auf)
│
└── infrastructure/             ← Äußerste Schicht – kennt alles, wird von domain/ nicht gekannt
    ├── db/                     │  SQLAlchemy ORM-Models + Repository-Implementierungen
    │   ├── models.py           │    → Mapping: ORM-Model ↔ Domain-Object
    │   └── <x>_repository.py  │
    ├── messaging/              │  RabbitMQ-Adapter (Publisher + Consumer)
    │   ├── publisher.py        │
    │   └── consumer.py         │
    ├── api/                    │  FastAPI-Router + Pydantic-Schemas (DTOs)
    │   └── v1/                 │    → Mapping: DTO ↔ Domain-Object
    │       ├── schemas/        │
    │       └── routers/        │
    └── config/                 │  pydantic-settings (Settings-Klasse)
        └── settings.py         │
```

### Schichtenregeln

| Von | Nach | Erlaubt? |
|---|---|---|
| `infrastructure/` | `application/` | ✅ |
| `infrastructure/` | `domain/` | ✅ |
| `application/` | `domain/` | ✅ |
| `application/` | `infrastructure/` | ❌ (nur über Ports) |
| `domain/` | `application/` | ❌ |
| `domain/` | `infrastructure/` | ❌ |

### Mapping-Strategie (Domain ↔ DB ↔ API)

Die Domain-Klassen (`Book`, `Loan`, …) sind **reine Python-Dataclasses** ohne ORM- oder Pydantic-Abhängigkeit. Das Mapping findet ausschließlich in der `infrastructure/`-Schicht statt:

```
HTTP-Request (Pydantic Schema)
        ↓  to_domain()         [infrastructure/api/]
  Domain Object
        ↓  from_domain()       [infrastructure/db/]
  ORM Model (SQLAlchemy)
        ↓
  PostgreSQL

PostgreSQL
        ↑
  ORM Model (SQLAlchemy)
        ↑  to_domain()         [infrastructure/db/]
  Domain Object
        ↑  from_domain()       [infrastructure/api/]
HTTP-Response (Pydantic Schema)
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
