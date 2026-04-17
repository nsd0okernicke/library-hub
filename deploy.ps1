#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploys LibraryHub to a local Minikube cluster.

.DESCRIPTION
    1. Starts Minikube (if not already running)
    2. Enables the ingress addon
    3. Points the local Docker client to Minikube's Docker daemon
    4. Builds all three Docker images directly inside Minikube
    5. Applies all Kubernetes manifests (infra first, then apps)
    6. Waits for infrastructure Pods to be ready
    7. Applies the seed Job to pre-populate the book catalogue
    8. Prints the URL and the required /etc/hosts entry

.EXAMPLE
    .\deploy.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = $PSScriptRoot

# ── Minikube home: avoid "Access denied" when installed in Program Files ──────
$desiredHome = "$env:USERPROFILE\.minikube"
if ($env:MINIKUBE_HOME -ne $desiredHome) {
    Write-Host "  Fixing MINIKUBE_HOME: '$env:MINIKUBE_HOME' → '$desiredHome'" -ForegroundColor Yellow
    # Set for current process
    $env:MINIKUBE_HOME = $desiredHome
    # Set permanently for the current user (no admin needed)
    [System.Environment]::SetEnvironmentVariable("MINIKUBE_HOME", $desiredHome, "User")
    Write-Host "  MINIKUBE_HOME saved to user environment." -ForegroundColor Green
}

function Write-Step([string]$msg) {
    Write-Host ""
    Write-Host "── $msg" -ForegroundColor Cyan
}

# ── 1. Build Docker images locally (before minikube, so internet works) ───────
Write-Step "Building catalog-service image (local Docker)..."
docker build -t catalog-service:latest "$ROOT/catalog-service"

Write-Step "Building loan-service image (local Docker)..."
docker build -t loan-service:latest "$ROOT/loan-service"

Write-Step "Building frontend image (local Docker)..."
docker build -t frontend:latest "$ROOT/frontend"

# ── 2. Start Minikube ─────────────────────────────────────────────────────────
Write-Step "Starting Minikube..."
$minikubeOut = & minikube status --format "{{.Host}}" 2>&1
$status = ($minikubeOut | Where-Object { $_ -notmatch "^[EW][0-9]" }) -join ""
if ($status.Trim() -ne "Running") {
    # Delete stale profile to avoid API-server-missing errors after MINIKUBE_HOME change
    Write-Host "  Deleting old minikube profile (if any)..." -ForegroundColor DarkGray
    try { $null = minikube delete 2>&1 } catch { <# profile may not exist – that's fine #> }
    minikube start --driver=docker --cpus=4 --memory=4096 --wait=all --wait-timeout=5m
} else {
    Write-Host "  Minikube already running." -ForegroundColor Green
}

# ── 3. Enable Ingress addon ───────────────────────────────────────────────────
Write-Step "Enabling ingress addon..."
minikube addons enable ingress

# ── 4. Load images into Minikube ──────────────────────────────────────────────
# minikube image load has a permission bug with Program Files cache on Windows,
# so we use docker save → minikube cp → docker load as a reliable workaround.
Write-Step "Loading images into Minikube..."
foreach ($img in @("catalog-service", "loan-service", "frontend")) {
    $tar = "$env:TEMP\$img.tar"
    Write-Host "  Loading $img ..." -ForegroundColor DarkGray
    docker save "${img}:latest" -o $tar
    minikube cp $tar "/tmp/$img.tar"
    minikube ssh "docker load -i /tmp/$img.tar" | Out-Null
    Write-Host "  $img loaded." -ForegroundColor Green
}

# ── 5. Apply infra manifests ──────────────────────────────────────────────────
Write-Step "Applying infrastructure manifests (Secrets, DBs, RabbitMQ)..."
kubectl apply -f "$ROOT/k8s/infra/"

# ── 6. Wait for infra Pods ────────────────────────────────────────────────────
Write-Step "Waiting for catalog-db to be ready..."
kubectl rollout status deployment/catalog-db --timeout=120s

Write-Step "Waiting for loan-db to be ready..."
kubectl rollout status deployment/loan-db --timeout=120s

Write-Step "Waiting for rabbitmq to be ready..."
kubectl rollout status deployment/rabbitmq --timeout=120s

# ── 7. Apply app manifests ────────────────────────────────────────────────────
Write-Step "Applying application manifests (ConfigMap, Services, Deployments)..."
kubectl apply -f "$ROOT/k8s/apps/configmap.yaml"
kubectl apply -f "$ROOT/k8s/apps/catalog-service.yaml"
kubectl apply -f "$ROOT/k8s/apps/loan-service.yaml"
kubectl apply -f "$ROOT/k8s/apps/frontend.yaml"

Write-Step "Waiting for catalog-service to be ready..."
kubectl rollout status deployment/catalog-service --timeout=120s

Write-Step "Waiting for loan-service to be ready..."
kubectl rollout status deployment/loan-service --timeout=120s

# ── 8. Apply Ingress ──────────────────────────────────────────────────────────
Write-Step "Applying Ingress..."
kubectl apply -f "$ROOT/k8s/ingress.yaml"

# ── 9. Run seed Job ───────────────────────────────────────────────────────────
Write-Step "Running catalog seed Job..."
kubectl apply -f "$ROOT/k8s/apps/seed-job.yaml"
Write-Host "  Waiting for seed job to complete..." -ForegroundColor Yellow
kubectl wait --for=condition=complete job/catalog-seed --timeout=60s
Write-Host "  Seed job completed." -ForegroundColor Green

# ── 10. Print access info ─────────────────────────────────────────────────────
$MINIKUBE_IP = minikube ip
Write-Host ""
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  LibraryHub deployed successfully!" -ForegroundColor Green
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  Add this line to your hosts file" -ForegroundColor Yellow
Write-Host "  (C:\Windows\System32\drivers\etc\hosts):" -ForegroundColor Yellow
Write-Host ""
Write-Host "    $MINIKUBE_IP  libraryhub.local" -ForegroundColor White
Write-Host ""
Write-Host "  Then open: http://libraryhub.local" -ForegroundColor Cyan
Write-Host "  RabbitMQ:  http://$(${MINIKUBE_IP}):15672  (run: kubectl port-forward svc/rabbitmq 15672:15672)" -ForegroundColor Cyan
Write-Host ""








