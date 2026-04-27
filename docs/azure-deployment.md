# Azure Deployment – LibraryHub

This document describes the complete Azure infrastructure for LibraryHub, how all
components interact, and how to operate the system.

---

## Architecture Overview

```
Internet
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Azure Load Balancer  (Public IP: 4.175.63.160)             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  AKS Cluster: libraryhub-aks  (westeurope, 1x B2s_v2)       │
│                                                             │
│  ┌─────────────────── nginx Ingress ───────────────────┐    │
│  │  /api/catalog/**  →  catalog-service:8000           │    │
│  │  /api/loan/**     →  loan-service:8001              │    │
│  │  /**              →  frontend:80                    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐     │
│  │   frontend   │  │catalog-serv. │  │  loan-service  │     │
│  │  nginx:80    │  │ FastAPI:8000 │  │  FastAPI:8001  │     │
│  └──────────────┘  └──────┬───────┘  └───────┬────────┘     │
│                           │  AMQP            │  AMQP        │
│                           ▼                  ▼              │
│                    ┌─────────────────────────────┐          │
│                    │   RabbitMQ  (AMQP :5672)    │          │
│                    └─────────────────────────────┘          │
│                                                             │
│  ┌────────────────┐         ┌─────────────────┐             │
│  │   catalog-db   │         │    loan-db      │             │
│  │  PostgreSQL 16 │         │  PostgreSQL 16  │             │
│  │  PVC: 2 GiB    │         │  PVC: 2 GiB     │             │
│  └────────────────┘         └─────────────────┘             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│  Azure Container Registry (ACR)            │
│  libraryhubackr.azurecr.io                 │
│  ├── catalog-service:latest / v*.*.*       │
│  ├── loan-service:latest / v*.*.*          │
│  └── frontend:latest / v*.*.*              │
└────────────────────────────────────────────┘
```

---

## Azure Resources

| Resource | Name | Type | Purpose |
|---|---|---|---|
| Resource Group | `libraryhub-rg` | Resource Group | Container for all resources |
| Container Registry | `libraryhubackr` | ACR (Basic) | Stores Docker images |
| Kubernetes Cluster | `libraryhub-aks` | AKS | Runs all workloads |
| Node Pool | 1× `Standard_B2s_v2` | VM | Single worker node |
| Public IP | `4.175.63.160` | Load Balancer IP | External entry point |

---

## Kubernetes Workloads

### Application Pods

| Deployment | Image | Port | Description |
|---|---|---|---|
| `frontend` | `libraryhubackr.azurecr.io/frontend` | 80 | React SPA served via nginx |
| `catalog-service` | `libraryhubackr.azurecr.io/catalog-service` | 8000 | Book catalogue REST API (FastAPI) |
| `loan-service` | `libraryhubackr.azurecr.io/loan-service` | 8001 | Loan management REST API (FastAPI) |

### Infrastructure Pods

| Deployment | Image | Port | Description |
|---|---|---|---|
| `catalog-db` | `postgres:16-alpine` | 5432 | PostgreSQL for Catalog Service |
| `loan-db` | `postgres:16-alpine` | 5432 | PostgreSQL for Loan Service |
| `rabbitmq` | `rabbitmq:3.13-management-alpine` | 5672 / 15672 | Message broker (AMQP) |

### Persistent Storage

| PVC | Size | Mount | Purpose |
|---|---|---|---|
| `catalog-db-pvc` | 2 GiB | `/var/lib/postgresql/data` | Catalog database data |
| `loan-db-pvc` | 2 GiB | `/var/lib/postgresql/data` | Loan database data |
| `rabbitmq-pvc` | 1 GiB | `/var/lib/rabbitmq` | RabbitMQ message persistence |

---

## Ingress Routing

The nginx Ingress Controller is installed via Helm into the `ingress-nginx` namespace
and receives external traffic via the Azure Load Balancer.

Two separate Ingress resources are used to avoid path rewrite conflicts:

### `libraryhub-api-ingress`
Handles API traffic with path prefix stripping (`rewrite-target: /$2`):

| External Path | Rewrites to | Service |
|---|---|---|
| `/api/catalog/books` | `/books` | `catalog-service:8000` |
| `/api/catalog/books/{isbn}` | `/books/{isbn}` | `catalog-service:8000` |
| `/api/loan/loans` | `/loans` | `loan-service:8001` |
| `/api/loan/users` | `/users` | `loan-service:8001` |
| `/api/loan/loans/{id}/return` | `/loans/{id}/return` | `loan-service:8001` |

### `libraryhub-frontend-ingress`
Handles all other traffic without path rewriting:

| External Path | Service |
|---|---|
| `/` (and all sub-paths) | `frontend:80` |

> **Why two Ingress resources?**  
> The `nginx.ingress.kubernetes.io/rewrite-target` annotation applies to the entire
> Ingress resource. A single Ingress would rewrite frontend asset paths like
> `/assets/main.js` incorrectly. Splitting them keeps routing clean.

---

## Configuration & Secrets

### ConfigMap: `libraryhub-config`

Non-sensitive runtime configuration, applied from `k8s/azure/configmap.yaml`:

| Key | Value | Used by |
|---|---|---|
| `CATALOG_PG_HOST` | `catalog-db` | catalog-service |
| `CATALOG_PG_DB` | `catalog_db` | catalog-service |
| `CATALOG_RABBITMQ_URL` | `amqp://guest:guest@rabbitmq:5672/` | catalog-service |
| `LOAN_PG_HOST` | `loan-db` | loan-service |
| `LOAN_PG_DB` | `loan_db` | loan-service |
| `LOAN_RABBITMQ_URL` | `amqp://guest:guest@rabbitmq:5672/` | loan-service |
| `LOAN_DURATION_DAYS` | `28` | loan-service |

### Secret: `libraryhub-secrets`

Sensitive values, created by `azure-setup.ps1` and refreshed by GitHub Actions:

| Key | Description |
|---|---|
| `catalog-db-user` | PostgreSQL user for catalog DB |
| `catalog-db-password` | PostgreSQL password for catalog DB |
| `catalog-db-name` | Database name (`catalog_db`) |
| `catalog-database-url` | Full SQLAlchemy connection URL |
| `loan-db-user` | PostgreSQL user for loan DB |
| `loan-db-password` | PostgreSQL password for loan DB |
| `loan-database-url` | Full SQLAlchemy connection URL |
| `rabbitmq-user` | RabbitMQ user |
| `rabbitmq-password` | RabbitMQ password |

### Secret: `acr-secret`

Docker registry credentials so AKS can pull images from ACR.
Created by `azure-setup.ps1`, referenced in all application Deployments via
`imagePullSecrets`.

---

## CI/CD Pipeline (GitHub Actions)

File: `.github/workflows/deploy.yml`

The pipeline triggers automatically on **version tags** (e.g. `v1.2.0`) or manually
via `workflow_dispatch`.

```
git tag v1.2.0
git push origin v1.2.0
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│  Job 1: test  (parallel for catalog-service + loan-service)  │
│  ─────────────────────────────────────────────────────────── │
│  • Spins up PostgreSQL + RabbitMQ as service containers       │
│  • Installs Python deps via uv                               │
│  • Runs unit tests + integration tests                        │
│  • Both services must pass before proceeding                  │
└───────────────────────────┬──────────────────────────────────┘
                            │ needs: test
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  Job 2: build-push                                           │
│  ─────────────────────────────────────────────────────────── │
│  • Logs in to Azure + ACR                                    │
│  • Builds Docker images for all 3 services                   │
│  • Pushes to ACR with tag v1.2.0 AND :latest                 │
└───────────────────────────┬──────────────────────────────────┘
                            │ needs: build-push
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  Job 3: deploy  (environment: production)                    │
│  ─────────────────────────────────────────────────────────── │
│  • Gets AKS credentials (kubectl context)                    │
│  • Patches image tags in k8s/azure/*.yaml                    │
│  • Applies ConfigMap + Secrets                               │
│  • Applies infra manifests (Postgres, RabbitMQ)              │
│  • Deploys application services                              │
│  • Applies Ingress                                           │
│  • Waits for rollout (kubectl rollout status)                │
│  • Runs catalog seed job (idempotent)                        │
└──────────────────────────────────────────────────────────────┘
```

### Required GitHub Actions Secrets

Set these under: **Repo → Settings → Secrets and variables → Actions**

| Secret | Description |
|---|---|
| `AZURE_CREDENTIALS` | Service Principal JSON (from `azure-setup.ps1` output) |
| `ACR_LOGIN_SERVER` | e.g. `libraryhubackr.azurecr.io` |
| `ACR_USERNAME` | ACR admin username |
| `ACR_PASSWORD` | ACR admin password |
| `DB_CATALOG_PASSWORD` | PostgreSQL password for catalog DB |
| `DB_LOAN_PASSWORD` | PostgreSQL password for loan DB |
| `AKS_RESOURCE_GROUP` | `libraryhub-rg` |
| `AKS_CLUSTER_NAME` | `libraryhub-aks` |

---

## Initial Setup

Run once after creating an Azure account:

```powershell
# 1. Install prerequisites
# - Azure CLI: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows
# - kubectl:   winget install Kubernetes.kubectl
# - helm:      winget install Helm.Helm

# 2. Login to Azure
az login

# 3. Run setup script (creates all Azure resources)
.\azure-setup.ps1 -DbCatalogPassword "YourSecurePass1!" -DbLoanPassword "YourSecurePass2!"

# 4. Add the printed values as GitHub Actions Secrets (see output)

# 5. Trigger first deployment
git tag v1.0.0
git push origin v1.0.0
```

---

## Day-to-Day Operations

### Trigger a new deployment

```powershell
git tag v1.2.3
git push origin v1.2.3
```

Or use **Actions → Deploy to Azure AKS → Run workflow** in the GitHub UI.

### Check cluster status

```powershell
# Switch to AKS context
kubectl config use-context libraryhub-aks

# All pods
kubectl get pods

# All ingress routes
kubectl get ingress

# View logs of a service
kubectl logs deployment/catalog-service --tail=50
kubectl logs deployment/loan-service --tail=50
```

### Connect pgAdmin to in-cluster PostgreSQL

The databases are not publicly exposed. Use `kubectl port-forward` to access them locally:

```powershell
# Forward catalog-db to local port 5433 (keep terminal open)
kubectl port-forward svc/catalog-db 5433:5432
```

Then connect pgAdmin to:

| Field | Value |
|---|---|
| Host | `127.0.0.1` |
| Port | `5433` |
| Database | `catalog_db` |
| Username | `postgres` |
| Password | value of `DB_CATALOG_PASSWORD` |
| SSL Mode | `disable` |

### Access RabbitMQ Management UI

```powershell
kubectl port-forward svc/rabbitmq 15672:15672
# Open: http://localhost:15672  (user: guest / password: guest)
```

### Re-run the book seed

```powershell
kubectl delete job catalog-seed --ignore-not-found=true
kubectl apply -f k8s/azure/seed-job.yaml
kubectl wait --for=condition=complete job/catalog-seed --timeout=120s
```

---

## Public URLs

| Endpoint | URL |
|---|---|
| **Frontend** | http://4.175.63.160 |
| **Catalog API Docs** | http://4.175.63.160/api/catalog/docs |
| **Loan API Docs** | http://4.175.63.160/api/loan/docs |

> **Note:** The IP may change if the AKS cluster is deleted and recreated.
> Check the current IP with: `kubectl get svc -n ingress-nginx ingress-nginx-controller`

---

## File Structure Reference

```
library-hub/
├── azure-setup.ps1              # One-time Azure infrastructure provisioning
├── .github/
│   └── workflows/
│       └── deploy.yml           # GitHub Actions CI/CD pipeline
└── k8s/
    └── azure/
        ├── infra.yaml           # PostgreSQL + RabbitMQ in-cluster deployments + PVCs
        ├── configmap.yaml       # Non-sensitive runtime config (host names, queue names)
        ├── catalog-service.yaml # Catalog Service Deployment + Service
        ├── loan-service.yaml    # Loan Service Deployment + Service
        ├── frontend.yaml        # Frontend Deployment + Service
        ├── ingress.yaml         # nginx Ingress (split: API with rewrite + frontend)
        └── seed-job.yaml        # One-time catalog seed Job + ConfigMap with SQL
```

