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
	- `BookReturned` (verarbeitet eingehendes Event)

### Loan Service

**Endpoints (REST API mit FastAPI):**

| Methode | Endpoint                        | Beschreibung                              | Asynchron |
|---------|---------------------------------|-------------------------------------------|-----------|
| POST    | `/loans`                        | Buch ausleihen (sofort 202 Accepted)      | **Ja**    |
| GET     | `/loans`                        | Meine Ausleihen anzeigen                  | Nein      |
| GET     | `/loans/{loan_id}`              | Einzelne Ausleihe abrufen                 | Nein      |
| POST    | `/loans/{loan_id}/return`       | Buch zurückgeben                          | Nein      |
| GET     | `/loans/overdue`                | Überfällige Ausleihen (Admin)             | Nein      |

**Domain Events:**
	- **Outgoing:** `BookLoanRequested`, `BookReturned`
	- **Incoming:** `BookReserved`, `BookOutOfStock`
	
## 3. Nicht-funktionale Anforderungen
### Architektur
	- Beide Services müssen **hexagonale Architektur** (Ports & Adapters / Clean Architecture) verwenden.
	- Klare Trennung: Domain → Application → Ports → Adapters
	- Keine direkte Datenbank- oder Service-zu-Service-Kommunikation außer über Messaging.
	
### Technische Vorgaben
	- **Sprache:** Python 3.11 oder höher
	- **Web-Framework:** FastAPI (mit Pydantic v2)
	- **Datenbank:** PostgreSQL (jeweils eigene Datenbank pro Service)
	- **ORM:** SQLAlchemy 2.0 mit async Support + Alembic für Migrationen
	- **Messaging:** RabbitMQ mit `aio-pika` (async)
	- **Containerisierung:** Jeder Service läuft in einem eigenen Docker-Container
	- **Orchestrierung:** Minikube (Kubernetes). Später skalierbar in die Cloud.
	- **API-Dokumentation:** Automatisch über FastAPI Swagger UI (`/docs`)
	
### Testen
	- **Testabdeckung:** **> 90 %** (gemessen mit `coverage`)
	- Mindestens:  - Unit-Tests für Domain und Application Layer  
	- Integration-Tests für Adapters (DB + Messaging)  
	- API-Tests mit `httpx` (async)  
	- Event Contract Tests (z. B. mit `pytest` und Test-Controllern)
	- Verwendung von `pytest`, `pytest-asyncio`, `pytest-cov`
	
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

| Layer              | Technologie                          |
|--------------------|--------------------------------------|
| API                | FastAPI + Uvicorn                    |
| Datenbank          | PostgreSQL                           |
| ORM                | SQLAlchemy 2.0 (async) + Alembic     |
| Messaging          | RabbitMQ + aio-pika                  |
| Testing            | pytest + httpx + pytest-asyncio      |
| Container          | Docker                               |
| Orchestrierung     | Minikube + Kubernetes manifests      |
| Code Quality       | black, ruff, mypy                    |

## 5. Akzeptanzkriterien pro User Story

**Beispiel für "Buch ausleihen":**
	- POST /loans gibt sofort HTTP 202 Accepted + Loan-ID zurück
	- Im Hintergrund wird `BookLoanRequested` Event gesendet
	- Catalog Service reserviert das Buch oder sendet `BookOutOfStock`
	- Loan Service aktualisiert den Status der Ausleihe entsprechend
	- Testabdeckung für diesen Flow > 90 %

## 6. Out of Scope (MVP)
	- Komplexes User-Management / Authentifizierung
	- Bezahlsystem- Benachrichtigungen per E-Mail/SMS
	- Frontend (kann später mit React/Vue hinzugefügt werden)
	- Buch-Cover-Upload oder komplexe Metadaten
