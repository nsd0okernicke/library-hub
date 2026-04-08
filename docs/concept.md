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

## Bounded Contexts

### 1. Catalog Service (Buchkatalog & Verfügbarkeit)
**Verantwortlich für:**
	- Verwaltung aller Bücher (Metadaten)
	- Aktueller Buchbestand / Verfügbarkeit
	- Suche und Filter

**Datenbank:** PostgreSQL (`books`, `book_stock`)

**Wichtige Domain Events (outgoing):**
	- `BookReserved`
	- `BookOutOfStock`
	- `BookReturned` (wird verarbeitet, wenn ein Buch zurückgegeben wird)

### 2. Loan Service (Ausleihen & Nutzerverwaltung)
**Verantwortlich für:**
	- Nutzer (einfach gehalten)
	- Ausleihvorgänge (loans)
	- Fristen und Überfälligkeiten
	- Starten einer Ausleihe
	
**Datenbank:** PostgreSQL (`users`, `loans`)

**Wichtige Domain Events (outgoing):**
	- `BookLoanRequested`
	- `BookReturned`
	
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