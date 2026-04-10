# LibraryHub – Anforderungen

## 1. Projektübersicht

**Name:** LibraryHub  
**Typ:** Lernprojekt – Microservices mit Python  
**Ziel:** Python-Basics vertiefen und moderne Architektur- & DevOps-Praktiken lernen (Hexagonale Architektur, Event-Driven Design, Kubernetes, hohe Testabdeckung).

Das System besteht aus **zwei Microservices**:
	- **Catalog Service** – Verwaltung von Büchern und deren Verfügbarkeit
	- **Loan Service** – Verwaltung von Ausleihvorgängen und Nutzern
	
Die Services kommunizieren ausschließlich asynchron über **Messaging** (RabbitMQ).

## 2. Funktionale Anforderungen (MVP)

### Catalog Service

**Endpoints (REST API mit FastAPI):**

| Methode | Endpoint                        | Beschreibung                              | Asynchron |
|---------|---------------------------------|-------------------------------------------|-----------|
| GET     | `/books`                        | Bücher suchen + filtern + paginieren      | **Ja**    |
| GET     | `/books/{isbn}`                 | Einzelnes Buch abrufen                    | Nein      |
| GET     | `/books/{isbn}/availability`    | Aktueller Bestand abfragen                | Nein      |
| POST    | `/books`                        | Neues Buch anlegen (Admin)                | Nein      |
| POST    | `/books/{isbn}/return`          | Buch wird zurückgegeben (Bestand +1)      | Nein      |

**Domain Events (outgoing):**
	- `BookReserved`
	- `BookOutOfStock`

**Domain Events (incoming):**
	- `BookReturned`

### Loan Service

**Endpoints (REST API mit FastAPI):**

| Methode | Endpoint                        | Beschreibung                              | Asynchron |
|---------|---------------------------------|-------------------------------------------|-----------|
| POST    | `/users`                        | Neuen Nutzer anlegen                      | Nein      |
| POST    | `/loans`                        | Buch ausleihen (sofort 202 Accepted)      | **Ja**    |
| GET     | `/loans?user_id={user_id}`      | Ausleihen eines Nutzers anzeigen          | Nein      |
| GET     | `/loans/{loan_id}`              | Einzelne Ausleihe abrufen                 | Nein      |
| POST    | `/loans/{loan_id}/return`       | Buch zurückgeben                          | Nein      |
| GET     | `/loans/overdue`                | Überfällige Ausleihen (Admin)             | Nein      |

**Domain Events:**
	- **Outgoing:** `BookLoanRequested`, `BookReturned`
	- **Incoming:** `BookReserved`, `BookOutOfStock`
	
## 3. Nicht-funktionale Anforderungen
### Architektur
	- Beide Services müssen **hexagonale Architektur** (Ports & Adapters / Clean Architecture) verwenden.
	- Klare Trennung in drei Hauptpakete: `domain/` → `application/` → `infrastructure/`
	- Ports (Output-Port-Interfaces) liegen unter `domain/ports/` – definiert von der Domain, implementiert in `infrastructure/`
	- Mapping zwischen Domain-Objekten, ORM-Models und API-Schemas erfolgt ausschließlich in `infrastructure/`
	- Keine direkte Datenbank- oder Service-zu-Service-Kommunikation außer über Messaging.
	
### Technische Vorgaben
	- **Sprache:** Python 3.11 oder höher
	- **Paketmanager:** `uv` (Rust-basierter Ersatz für `pip` + `venv`, 10–100× schneller). Muss einmalig global installiert werden: `pip install uv`
	- **Virtuelle Umgebungen:** Pro Service eine eigene `.venv` (kein gemeinsames Root-Environment), angelegt mit `uv venv`
	- **Web-Framework:** FastAPI (mit Pydantic v2)
	- **Datenbank:** PostgreSQL (jeweils eigene Datenbank pro Service)
	- **ORM:** SQLAlchemy 2.0 mit async Support + Alembic für Migrationen
	- **Messaging:** RabbitMQ mit `aio-pika` (async)
	- **Containerisierung:** Jeder Service läuft in einem eigenen Docker-Container
	- **Orchestrierung:** Minikube (Kubernetes). Später skalierbar in die Cloud.
	- **API-Dokumentation:** Automatisch über FastAPI Swagger UI (`/docs`)

### Entwicklungsstrategie
	- **Beide Services parallel:** Jede Architekturschicht wird für `catalog-service` und `loan-service` gleichzeitig implementiert
	- **Test-First (TDD):** Für jede Schicht werden zuerst Tests geschrieben, bevor die Implementierung folgt
	- **Schicht-für-Schicht:** Domain → Ports (unter `domain/ports/`) → Application → Infrastructure (DB + Messaging + API)
	- **TDD-Zyklus (verbindlich):**
		1. 🔴 **RED** – Tests schreiben und ausführen → müssen FEHLSCHLAGEN (kein Produktionscode existiert noch)
		2. 🟢 **GREEN** – Minimale Implementierung, die alle Tests bestehen lässt
		3. 🔵 **REFACTOR** – Aufräumen ohne neues Verhalten; Tests bleiben grün
	- Zwischen RED und GREEN darf **kein Produktionscode** geschrieben werden. Der fehlgeschlagene Test-Output wird vor der Implementierung dokumentiert.
	
### Testen
	- **Teststrategie:** Test-First (TDD) – Tests werden pro Schicht geschrieben, bevor die Implementierung beginnt
	- **Testabdeckung:** **> 90 %** (gemessen mit `coverage`)
	- Mindestens:
		- Unit-Tests für Domain und Application Layer (mit gemockten Ports, kein DB/MQ-Zugriff)
		- Integrationstests für Adapters (DB + Messaging) – **automatisch via Testcontainers** (kein manuelles `docker-compose up` nötig)
		- API-Tests mit `httpx` (async) gegen die FastAPI-App
		- Event Contract Tests (Test-Publisher/-Consumer prüfen Event-Format beidseitig, JSON mit `event_type`-Feld und `version: "1.0"`)
	- Verwendung von `pytest`, `pytest-asyncio`, `pytest-cov`, `testcontainers`
	- **Testcontainers:** PostgreSQL- und RabbitMQ-Container werden automatisch innerhalb von `pytest` gestartet (ein Container pro Test-Session für Performance)
	
### Code Quality
	- **Formatter:** black
	- **Linter:** ruff
	- **Type Checking:** mypy
	- **Pre-commit Hooks** empfohlen
	- Saubere, lesbare und gut dokumentierte Codebase
	
### Deployment & Infrastruktur
	- **Lokale Entwicklung:** docker-compose.yml (für schnelles Starten von Services + RabbitMQ + DBs)
	- **Kubernetes:** Minikube mit separaten Deployments, Services, ConfigMaps/Secrets und PersistentVolumeClaims für die Datenbanken
	- **Später:** Bereit für Cloud-Deployment (z. B. Kubernetes auf DigitalOcean, AWS EKS oder GCP)

### Sicherheit & Sonstiges (MVP)
	- Keine Authentifizierung im MVP (später optional JWT)
	- Einfache Fehlerbehandlung mit HTTP-Statuscodes und aussagekräftigen Fehlermeldungen
	- Logging (structuriert empfohlen)
	- Environment-Variablen für Konfiguration (z. B. via `pydantic-settings`)

## 4. Technologie-Stack (festgelegt)

| Layer              | Technologie                                      |
|--------------------|--------------------------------------------------|
| API                | FastAPI + Uvicorn                                |
| Datenbank          | PostgreSQL                                       |
| ORM                | SQLAlchemy 2.0 (async) + Alembic                 |
| Messaging          | RabbitMQ + aio-pika                              |
| Paketmanagement    | uv (Rust-basiert)                                |
| Testing            | pytest + httpx + pytest-asyncio + testcontainers |
| Container          | Docker                                           |
| Orchestrierung     | Minikube + Kubernetes manifests                  |
| Code Quality       | black, ruff, mypy                                |

## 5. User Stories

### Catalog Service

**CAT-1 – Bücher suchen**
> Als Nutzer möchte ich Bücher nach Titel, Autor oder Genre suchen und paginieren, damit ich schnell das passende Buch finde.

**CAT-2 – Buchverfügbarkeit prüfen**
> Als Nutzer möchte ich die Verfügbarkeit eines Buchs per ISBN prüfen, damit ich weiß ob ich es ausleihen kann.

**CAT-3 – Buch anlegen**
> Als Admin möchte ich ein neues Buch mit Metadaten und Anfangsbestand anlegen, damit der Katalog gepflegt werden kann.

**CAT-4 – Bestand bei Rückgabe erhöhen** *(System Story)*
> Als System möchte ich den Bestand eines Buchs automatisch erhöhen, wenn ein `BookReturned`-Event eintrifft, damit die Verfügbarkeit stets aktuell ist.

**CAT-5 – Einzelnes Buch abrufen**
> Als Nutzer möchte ich ein einzelnes Buch per ISBN abrufen, damit ich alle Metadaten auf einen Blick sehe.

**CAT-6 – Buch manuell zurückbuchen**
> Als System möchte ich über `POST /books/{isbn}/return` den Buchbestand um 1 erhöhen, damit der Endpoint als interner Trigger durch den Loan Service (via Event-Consumer) genutzt werden kann.

---

### Loan Service

**LOAN-0 – Nutzer anlegen**
> Als Nutzer möchte ich mich registrieren, damit ich Bücher ausleihen kann.

**LOAN-1 – Buch ausleihen**
> Als Nutzer möchte ich ein Buch ausleihen und sofort eine Antwort erhalten, damit ich nicht auf die Bestätigung warten muss.

**LOAN-2 – Ausleihstatus einsehen**
> Als Nutzer möchte ich den Status einer einzelnen Ausleihe einsehen, damit ich weiß ob sie bestätigt, abgelehnt oder aktiv ist.

**LOAN-3 – Alle Ausleihen anzeigen**
> Als Nutzer möchte ich alle meine aktiven Ausleihen auf einen Blick sehen, damit ich den Überblick behalte.

**LOAN-4 – Buch zurückgeben**
> Als Nutzer möchte ich ein Buch zurückgeben, damit der Bestand im Katalog wieder freigegeben wird.

**LOAN-5 – Überfällige Ausleihen einsehen**
> Als Admin möchte ich alle überfälligen Ausleihen einsehen, damit ich Nutzer daran erinnern kann.

---

## 6. Akzeptanzkriterien

### CAT-1 – Bücher suchen
- `GET /books` gibt `HTTP 200 OK` zurück
- Response enthält paginierte Liste (`items`, `total`, `page`, `page_size`)
- Filterparameter `?title=`, `?author=`, `?genre=` werden einzeln und kombiniert unterstützt
- Leere Ergebnisliste liefert `HTTP 200 OK` mit `items: []` (kein 404)
- Testabdeckung > 90 %

### CAT-2 – Buchverfügbarkeit prüfen
- `GET /books/{isbn}/availability` gibt `HTTP 200 OK` mit `{ "isbn": "...", "available_count": n }` zurück
- Unbekannte ISBN liefert `HTTP 404 Not Found` mit aussagekräftiger Fehlermeldung
- Testabdeckung > 90 %

### CAT-3 – Buch anlegen
- `POST /books` gibt `HTTP 201 Created` + vollständiges Book-Objekt zurück
- Request-Body enthält Pflichtfelder: `isbn`, `title`, `author`, `genre` sowie `initial_stock` (Integer ≥ 0)
- `initial_stock` wird beim Anlegen automatisch als Eintrag in `book_stock` gespeichert
- Doppelte ISBN liefert `HTTP 409 Conflict`
- Fehlende Pflichtfelder liefern `HTTP 422 Unprocessable Entity`
- Testabdeckung > 90 %

### CAT-4 – Bestand bei Rückgabe erhöhen *(System Story)*
- Eingehendes `BookReturned`-Event (`event_type: "BookReturned"`, `version: "1.0"`, `isbn`) erhöht `available_count` um 1
- Unbekannte ISBN im Event wird als Dead-Letter geloggt, kein Absturz
- `GET /books/{isbn}/availability` spiegelt den erhöhten Bestand unmittelbar wider
- Testabdeckung > 90 %

### CAT-5 – Einzelnes Buch abrufen
- `GET /books/{isbn}` gibt `HTTP 200 OK` + vollständiges Book-Objekt zurück
- Unbekannte ISBN liefert `HTTP 404 Not Found`
- Testabdeckung > 90 %

### CAT-6 – Buch manuell zurückbuchen
- `POST /books/{isbn}/return` gibt `HTTP 200 OK` + aktualisiertes `book_stock`-Objekt zurück
- `available_count` wird um 1 erhöht
- Unbekannte ISBN liefert `HTTP 404 Not Found`
- Testabdeckung > 90 %

### LOAN-0 – Nutzer anlegen
- `POST /users` gibt `HTTP 201 Created` + User-Objekt (`id`, `name`, `email`, `created_at`) zurück
- Pflichtfelder: `name`, `email`
- Doppelte E-Mail liefert `HTTP 409 Conflict`
- Fehlende Pflichtfelder liefern `HTTP 422 Unprocessable Entity`
- Testabdeckung > 90 %

### LOAN-1 – Buch ausleihen
- `POST /loans` gibt sofort `HTTP 202 Accepted` + `{ "loan_id": "...", "status": "PENDING" }` zurück
- Loan Service publiziert `BookLoanRequested`-Event (`event_type`, `version: "1.0"`, `loan_id`, `isbn`, `user_id`)
- Loan Service setzt `due_date` beim Anlegen auf `heute + LOAN_DURATION_DAYS` (Standard: 28 Tage, konfigurierbar via Umgebungsvariable `LOAN_DURATION_DAYS`)
- Catalog Service antwortet mit `BookReserved` → Loan-Status wechselt `PENDING → ACTIVE`
- Catalog Service antwortet mit `BookOutOfStock` → Loan-Status wechselt `PENDING → REJECTED`
- Fehlende Pflichtfelder (`isbn`, `user_id`) liefern `HTTP 422 Unprocessable Entity`
- Testabdeckung > 90 %

### LOAN-2 – Ausleihstatus einsehen
- `GET /loans/{loan_id}` gibt `HTTP 200 OK` mit Loan-Objekt inkl. aktuellem `status` zurück
- Unbekannte `loan_id` liefert `HTTP 404 Not Found`
- Testabdeckung > 90 %

### LOAN-3 – Alle Ausleihen anzeigen
- `GET /loans?user_id={user_id}` gibt `HTTP 200 OK` mit paginierter Liste aller Ausleihen des Nutzers zurück
- `user_id` wird als Query-Parameter übergeben (kein Auth-Header im MVP)
- Fehlender `user_id`-Parameter liefert `HTTP 422 Unprocessable Entity`
- Leere Liste liefert `HTTP 200 OK` mit `items: []`
- Testabdeckung > 90 %

### LOAN-4 – Buch zurückgeben
- `POST /loans/{loan_id}/return` gibt `HTTP 200 OK` zurück, Loan-Status wechselt `ACTIVE → RETURNED`
- Loan Service publiziert `BookReturned`-Event (`event_type`, `version: "1.0"`, `loan_id`, `isbn`)
- Bereits zurückgegebene Ausleihe liefert `HTTP 409 Conflict`
- Unbekannte `loan_id` liefert `HTTP 404 Not Found`
- Testabdeckung > 90 %

### LOAN-5 – Überfällige Ausleihen einsehen
- `GET /loans/overdue` gibt `HTTP 200 OK` mit Liste aller Ausleihen zurück, bei denen `due_date < heute` und `status = ACTIVE`
- Leere Liste liefert `HTTP 200 OK` mit `items: []`
- Testabdeckung > 90 %

---

## 7. Abhängigkeiten (pyproject.toml)

Pro Service werden folgende Mindestversionen verwendet:

### `[project.dependencies]` (Runtime)
| Package              | Mindestversion | Zweck                                 |
|----------------------|----------------|---------------------------------------|
| `fastapi`            | `>=0.111`      | Web-Framework                         |
| `uvicorn[standard]`  | `>=0.29`       | ASGI-Server                           |
| `pydantic`           | `>=2.7`        | Datenvalidierung / Schemas            |
| `pydantic-settings`  | `>=2.2`        | Konfiguration via Umgebungsvariablen  |
| `sqlalchemy`         | `>=2.0`        | ORM (async)                           |
| `asyncpg`            | `>=0.29`       | Async PostgreSQL-Treiber              |
| `alembic`            | `>=1.13`       | Datenbankmigrationen                  |
| `aio-pika`           | `>=9.4`        | Async RabbitMQ-Client                 |

### `[dependency-groups.dev]` (Entwicklung & Tests)
| Package                  | Mindestversion | Zweck                                  |
|--------------------------|----------------|----------------------------------------|
| `pytest`                 | `>=8.0`        | Test-Framework                         |
| `pytest-asyncio`         | `>=0.23`       | Async-Test-Support                     |
| `pytest-cov`             | `>=5.0`        | Coverage-Messung                       |
| `httpx`                  | `>=0.27`       | Async HTTP-Client für API-Tests        |
| `testcontainers`         | `>=4.4`        | Automatische Docker-Container in Tests |
| `black`                  | `>=24.0`       | Code-Formatter                         |
| `ruff`                   | `>=0.4`        | Linter                                 |
| `mypy`                   | `>=1.10`       | Typ-Prüfung                            |

---

## 8. Event-Payloads (verbindlich)

Alle Events werden als JSON über RabbitMQ übertragen. Jedes Event enthält die Pflichtfelder `event_type`, `version` und `occurred_at`.

### `BookLoanRequested` *(Loan Service → Catalog Service)*
```json
{
  "event_type": "BookLoanRequested",
  "version": "1.0",
  "occurred_at": "2026-04-08T10:00:00Z",
  "loan_id": "uuid",
  "isbn": "978-3-16-148410-0",
  "user_id": "uuid"
}
```

### `BookReserved` *(Catalog Service → Loan Service)*
```json
{
  "event_type": "BookReserved",
  "version": "1.0",
  "occurred_at": "2026-04-08T10:00:01Z",
  "loan_id": "uuid",
  "isbn": "978-3-16-148410-0"
}
```

### `BookOutOfStock` *(Catalog Service → Loan Service)*
```json
{
  "event_type": "BookOutOfStock",
  "version": "1.0",
  "occurred_at": "2026-04-08T10:00:01Z",
  "loan_id": "uuid",
  "isbn": "978-3-16-148410-0"
}
```

### `BookReturned` *(Loan Service → Catalog Service)*
```json
{
  "event_type": "BookReturned",
  "version": "1.0",
  "occurred_at": "2026-04-08T11:00:00Z",
  "loan_id": "uuid",
  "isbn": "978-3-16-148410-0"
}
```

---

## 9. Datenbankschema (Catalog Service)

### Tabelle `books`
| Spalte        | Typ           | Constraints              |
|---------------|---------------|--------------------------|
| `isbn`        | `VARCHAR(20)` | PRIMARY KEY              |
| `title`       | `VARCHAR(255)`| NOT NULL                 |
| `author`      | `VARCHAR(255)`| NOT NULL                 |
| `genre`       | `VARCHAR(100)`| NOT NULL                 |
| `description` | `TEXT`        | NULLABLE                 |
| `created_at`  | `TIMESTAMP`   | NOT NULL, DEFAULT now()  |

### Tabelle `book_stock`
| Spalte            | Typ           | Constraints              |
|-------------------|---------------|--------------------------|
| `isbn`            | `VARCHAR(20)` | PRIMARY KEY, FK → books  |
| `available_count` | `INTEGER`     | NOT NULL, DEFAULT 0, ≥ 0 |
| `updated_at`      | `TIMESTAMP`   | NOT NULL, DEFAULT now()  |

## 10. Datenbankschema (Loan Service)

### Tabelle `users`
| Spalte       | Typ           | Constraints             |
|--------------|---------------|-------------------------|
| `id`         | `UUID`        | PRIMARY KEY             |
| `name`       | `VARCHAR(255)`| NOT NULL                |
| `email`      | `VARCHAR(255)`| NOT NULL, UNIQUE        |
| `created_at` | `TIMESTAMP`   | NOT NULL, DEFAULT now() |

### Tabelle `loans`
| Spalte        | Typ           | Constraints                                                   |
|---------------|---------------|---------------------------------------------------------------|
| `id`          | `UUID`        | PRIMARY KEY                                                   |
| `user_id`     | `UUID`        | NOT NULL, FK → users                                          |
| `isbn`        | `VARCHAR(20)` | NOT NULL                                                      |
| `status`      | `VARCHAR(20)` | NOT NULL (`PENDING`,`ACTIVE`,`RETURNED`,`REJECTED`)           |
| `due_date`    | `DATE`        | NOT NULL (gesetzt beim Anlegen: heute + `LOAN_DURATION_DAYS`) |
| `returned_at` | `TIMESTAMP`   | NULLABLE (gesetzt bei `POST /loans/{id}/return`)              |
| `created_at`  | `TIMESTAMP`   | NOT NULL, DEFAULT now()                                       |
| `updated_at`  | `TIMESTAMP`   | NOT NULL, DEFAULT now()                                       |

---

## 11. RabbitMQ-Struktur

- **Exchange:** `library.events` (Typ: **Topic**)
- **Routing Keys:** entsprechen dem `event_type` in snake_case

| Routing Key             | Publiziert von  | Konsumiert von  |
|-------------------------|-----------------|-----------------|
| `book.loan.requested`   | Loan Service    | Catalog Service |
| `book.reserved`         | Catalog Service | Loan Service    |
| `book.out_of_stock`     | Catalog Service | Loan Service    |
| `book.returned`         | Loan Service    | Catalog Service |

**Queues:**

| Queue                      | Binding (Routing Key)   | Konsument       |
|----------------------------|-------------------------|-----------------|
| `catalog.loan-requested`   | `book.loan.requested`   | Catalog Service |
| `loan.book-reserved`       | `book.reserved`         | Loan Service    |
| `loan.book-out-of-stock`   | `book.out_of_stock`     | Loan Service    |
| `catalog.book-returned`    | `book.returned`         | Catalog Service |

- **Durability:** Alle Exchanges und Queues sind `durable: true`
- **Dead-Letter:** Nicht verarbeitbare Messages landen in `library.events.dlq`
- **Konfiguration:** Exchange- und Queue-Namen via Umgebungsvariablen konfigurierbar (`RABBITMQ_EXCHANGE`, etc.)

---

## 12. Out of Scope (MVP)
	- Komplexes User-Management / Authentifizierung
	- Bezahlsystem- Benachrichtigungen per E-Mail/SMS
	- Frontend (kann später mit React/Vue hinzugefügt werden)
	- Buch-Cover-Upload oder komplexe Metadaten
