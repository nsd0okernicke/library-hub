#!/usr/bin/env pwsh
# ── azure-setup.ps1 ───────────────────────────────────────────────────────────
# One-time infrastructure provisioning script for LibraryHub on Azure.
# Run this once to create all Azure resources. Afterwards, GitHub Actions
# handles all deployments automatically via git tags.
#
# Prerequisites:
#   - Azure CLI installed: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli
#   - Logged in: az login
#   - kubectl + helm installed
#
# Usage:
#   .\azure-setup.ps1 -DbCatalogPassword "YourSecurePass1!" -DbLoanPassword "YourSecurePass2!"
# ──────────────────────────────────────────────────────────────────────────────

param(
    [Parameter(Mandatory = $true)]
    [string]$DbCatalogPassword,

    [Parameter(Mandatory = $true)]
    [string]$DbLoanPassword,

    [string]$Location       = "westeurope",
    [string]$ResourceGroup  = "libraryhub-rg",
    [string]$AcrName        = "libraryhubackr",
    [string]$AksName        = "libraryhub-aks",
    [string]$NodeVmSize     = "Standard_B2s_v2",
    [string]$DnsLabel       = "libraryhub",
    [string]$AdminUser      = "postgres"
)

$ErrorActionPreference = "Continue"

function Write-Step([string]$msg) {
    Write-Host ""
    Write-Host "══ $msg" -ForegroundColor Cyan
}

# ── 0. Verify az login ────────────────────────────────────────────────────────
Write-Step "Verifying Azure login..."
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "Not logged in. Running az login..." -ForegroundColor Yellow
    az login
    $account = az account show | ConvertFrom-Json
}
Write-Host "  Subscription: $($account.name) ($($account.id))" -ForegroundColor Green
$SubscriptionId = $account.id

# ── 0b. Register required resource providers ──────────────────────────────────
Write-Step "Registering required Azure resource providers..."
$providers = @(
    "Microsoft.ContainerRegistry",
    "Microsoft.ContainerService",
    "Microsoft.DBforPostgreSQL",
    "Microsoft.Network",
    "Microsoft.Compute"
)
foreach ($provider in $providers) {
    Write-Host "  Registering $provider ..." -ForegroundColor Yellow
    az provider register --namespace $provider --output none
}
Write-Host "  Waiting for providers to reach 'Registered' state (may take 1-3 min)..." -ForegroundColor Yellow
foreach ($provider in $providers) {
    $state = ""
    $retries = 0
    while ($state -ne "Registered" -and $retries -lt 36) {
        Start-Sleep -Seconds 10
        $state = (az provider show --namespace $provider --query "registrationState" --output tsv 2>$null)
        Write-Host "    $provider : $state"
        $retries++
    }
    if ($state -ne "Registered") {
        Write-Host "  WARNING: $provider not yet 'Registered' after timeout. Continuing..." -ForegroundColor Yellow
    }
}
Write-Host "  Providers ready." -ForegroundColor Green

# ── 1. Resource Group ─────────────────────────────────────────────────────────
Write-Step "Creating Resource Group '$ResourceGroup' in '$Location'..."
az group create --name $ResourceGroup --location $Location --output none
Write-Host "  Done." -ForegroundColor Green

# ── 2. Azure Container Registry ───────────────────────────────────────────────
Write-Step "Creating Azure Container Registry '$AcrName'..."
$acrExists = (az acr show --name $AcrName --query name --output tsv 2>$null)
if ($acrExists) {
    Write-Host "  ACR '$AcrName' already exists, skipping." -ForegroundColor Yellow
} else {
    az acr create `
        --resource-group $ResourceGroup `
        --name $AcrName `
        --sku Basic `
        --admin-enabled true `
        --output none
    Write-Host "  Done." -ForegroundColor Green
}

$AcrLoginServer = (az acr show --name $AcrName --query loginServer --output tsv)
$AcrCredentials = az acr credential show --name $AcrName | ConvertFrom-Json
$AcrUsername    = $AcrCredentials.username
$AcrPassword    = $AcrCredentials.passwords[0].value

# ── 3. AKS Cluster ────────────────────────────────────────────────────────────
# NOTE: No --enable-addons ingress-appgw here.
# nginx Ingress is installed separately via Helm in step 4.
Write-Step "Creating AKS Cluster '$AksName' (1x $NodeVmSize)..."
$aksExists = (az aks show --resource-group $ResourceGroup --name $AksName --query name --output tsv 2>$null)
if ($aksExists) {
    Write-Host "  AKS cluster '$AksName' already exists, skipping." -ForegroundColor Yellow
} else {
    az aks create `
        --resource-group $ResourceGroup `
        --name $AksName `
        --node-count 1 `
        --node-vm-size $NodeVmSize `
        --generate-ssh-keys `
        --attach-acr $AcrName `
        --output none

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: AKS cluster creation failed. Aborting." -ForegroundColor Red
        exit 1
    }
    Write-Host "  AKS cluster created." -ForegroundColor Green
}

Write-Step "Getting AKS credentials for kubectl..."
az aks get-credentials --resource-group $ResourceGroup --name $AksName --overwrite-existing
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Could not retrieve AKS credentials. Aborting." -ForegroundColor Red
    exit 1
}
Write-Host "  kubectl context set to '$AksName'." -ForegroundColor Green

# ── 4. Install nginx Ingress Controller via Helm ──────────────────────────────
Write-Step "Installing nginx Ingress Controller via Helm..."
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx 2>$null
helm repo update
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx `
    --namespace ingress-nginx `
    --create-namespace `
    --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-load-balancer-health-probe-request-path"=/healthz `
    --wait --timeout 5m

Write-Host "  Waiting for LoadBalancer IP (up to 3 min)..." -ForegroundColor Yellow
$PublicIp = ""
for ($i = 0; $i -lt 18; $i++) {
    Start-Sleep -Seconds 10
    $PublicIp = kubectl get svc -n ingress-nginx ingress-nginx-controller `
        -o jsonpath="{.status.loadBalancer.ingress[0].ip}" 2>$null
    if ($PublicIp) { break }
    Write-Host "    Still waiting... ($( ($i+1)*10 )s)"
}
Write-Host "  Ingress IP: $PublicIp" -ForegroundColor Green

# ── 5. Deploy in-cluster infrastructure (PostgreSQL + RabbitMQ) ───────────────
# We use in-cluster Postgres pods instead of Azure Flexible Server to avoid
# location restrictions on free-tier subscriptions and to reduce costs.
Write-Step "Deploying in-cluster PostgreSQL + RabbitMQ..."
kubectl apply -f "$PSScriptRoot/k8s/azure/infra.yaml"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Infra deployment failed. Aborting." -ForegroundColor Red
    exit 1
}
Write-Host "  Waiting for catalog-db..." -ForegroundColor Yellow
kubectl rollout status deployment/catalog-db --timeout=120s
Write-Host "  Waiting for loan-db..." -ForegroundColor Yellow
kubectl rollout status deployment/loan-db --timeout=120s
Write-Host "  Waiting for rabbitmq..." -ForegroundColor Yellow
kubectl rollout status deployment/rabbitmq --timeout=120s
Write-Host "  In-cluster infrastructure ready." -ForegroundColor Green

# ── 6. GitHub Actions Service Principal ───────────────────────────────────────
Write-Step "Creating Service Principal for GitHub Actions..."
$SpJson = az ad sp create-for-rbac `
    --name "libraryhub-github-actions" `
    --role contributor `
    --scopes "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup" `
    --sdk-auth
Write-Host "  Service Principal created." -ForegroundColor Green

# ── 7. Apply Kubernetes Secrets & ConfigMap ───────────────────────────────────
Write-Step "Applying Kubernetes Secrets and ConfigMap to AKS..."

$CatalogDbUserB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($AdminUser))
$CatalogDbPassB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($DbCatalogPassword))
$CatalogDbNameB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("catalog_db"))
$LoanDbUserB64    = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($AdminUser))
$LoanDbPassB64    = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($DbLoanPassword))
$LoanDbNameB64    = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("loan_db"))
$RabbitUserB64    = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("guest"))
$RabbitPassB64    = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("guest"))

# Full DATABASE_URL for each service (used directly by the app)
$CatalogDbUrl     = "postgresql+asyncpg://${AdminUser}:${DbCatalogPassword}@catalog-db/catalog_db"
$LoanDbUrl        = "postgresql+asyncpg://${AdminUser}:${DbLoanPassword}@loan-db/loan_db"
$CatalogDbUrlB64  = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($CatalogDbUrl))
$LoanDbUrlB64     = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($LoanDbUrl))

$SecretsYaml = @"
apiVersion: v1
kind: Secret
metadata:
  name: libraryhub-secrets
  namespace: default
type: Opaque
data:
  catalog-db-user:        $CatalogDbUserB64
  catalog-db-password:    $CatalogDbPassB64
  catalog-db-name:        $CatalogDbNameB64
  catalog-database-url:   $CatalogDbUrlB64
  loan-db-user:           $LoanDbUserB64
  loan-db-password:       $LoanDbPassB64
  loan-db-name:           $LoanDbNameB64
  loan-database-url:      $LoanDbUrlB64
  rabbitmq-user:          $RabbitUserB64
  rabbitmq-password:      $RabbitPassB64
"@

$SecretsYaml | kubectl apply -f -
kubectl apply -f "$PSScriptRoot/k8s/azure/configmap.yaml"
Write-Host "  Secrets and ConfigMap applied." -ForegroundColor Green

# ── 8. ACR imagePullSecret ────────────────────────────────────────────────────
Write-Step "Creating ACR image pull secret in Kubernetes..."
kubectl create secret docker-registry acr-secret `
    --docker-server=$AcrLoginServer `
    --docker-username=$AcrUsername `
    --docker-password=$AcrPassword `
    --dry-run=client -o yaml | kubectl apply -f -
Write-Host "  ACR pull secret created." -ForegroundColor Green

# ── 9. Budget Alert ───────────────────────────────────────────────────────────
Write-Step "Creating Azure Budget Alert (50 USD/month)..."
az consumption budget create `
    --budget-name "libraryhub-budget" `
    --amount 50 `
    --time-grain Monthly `
    --start-date (Get-Date -Format "yyyy-MM-01") `
    --end-date "2027-12-01" `
    --resource-group $ResourceGroup 2>$null
Write-Host "  Budget alert set at 50 USD/month." -ForegroundColor Green

# ── 10. Output: GitHub Secrets ────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
Write-Host "║         ADD THESE SECRETS TO GITHUB ACTIONS                 ║" -ForegroundColor Yellow
Write-Host "║  Repo → Settings → Secrets and variables → Actions → New    ║" -ForegroundColor Yellow
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
Write-Host ""
Write-Host "AZURE_CREDENTIALS:" -ForegroundColor Cyan
Write-Host $SpJson
Write-Host ""
Write-Host "ACR_LOGIN_SERVER:    $AcrLoginServer" -ForegroundColor Cyan
Write-Host "ACR_USERNAME:        $AcrUsername" -ForegroundColor Cyan
Write-Host "ACR_PASSWORD:        $AcrPassword" -ForegroundColor Cyan
Write-Host "DB_CATALOG_PASSWORD: $DbCatalogPassword" -ForegroundColor Cyan
Write-Host "DB_LOAN_PASSWORD:    $DbLoanPassword" -ForegroundColor Cyan
Write-Host ""
Write-Host "AKS_RESOURCE_GROUP:  $ResourceGroup" -ForegroundColor Cyan
Write-Host "AKS_CLUSTER_NAME:    $AksName" -ForegroundColor Cyan
Write-Host ""
Write-Host "══ Setup complete! Ingress IP: $PublicIp" -ForegroundColor Green
if ($PublicIp) {
    Write-Host "   Run this to set DNS label:" -ForegroundColor Yellow
    Write-Host "   az network public-ip list -g MC_${ResourceGroup}_${AksName}_${Location} --query ""[0].name"" -o tsv"
    Write-Host "   # Then: az network public-ip update -g MC_... -n <name> --dns-name $DnsLabel"
    Write-Host "   App will be available at: http://$DnsLabel.$Location.cloudapp.azure.com"
}









