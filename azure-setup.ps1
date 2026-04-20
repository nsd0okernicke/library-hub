#!/usr/bin/env pwsh
# ── azure-setup.ps1 ───────────────────────────────────────────────────────────
# One-time infrastructure provisioning script for LibraryHub on Azure.
# Run this once to create all Azure resources. Afterwards, GitHub Actions
# handles all deployments automatically via git tags.
#
# Prerequisites:
#   - Azure CLI installed: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli
#   - Logged in: az login
#   - kubectl installed
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
    [string]$PgServerName   = "libraryhub-pg",
    [string]$DnsLabel       = "libraryhub",
    [string]$AdminUser      = "pgadmin"
)

$ErrorActionPreference = "Stop"

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

# ── 1. Resource Group ─────────────────────────────────────────────────────────
Write-Step "Creating Resource Group '$ResourceGroup' in '$Location'..."
az group create --name $ResourceGroup --location $Location --output none
Write-Host "  Done." -ForegroundColor Green

# ── 2. Azure Container Registry ───────────────────────────────────────────────
Write-Step "Creating Azure Container Registry '$AcrName'..."
az acr create `
    --resource-group $ResourceGroup `
    --name $AcrName `
    --sku Basic `
    --admin-enabled true `
    --output none
Write-Host "  Done." -ForegroundColor Green

$AcrLoginServer = (az acr show --name $AcrName --query loginServer --output tsv)
$AcrCredentials = az acr credential show --name $AcrName | ConvertFrom-Json
$AcrUsername    = $AcrCredentials.username
$AcrPassword    = $AcrCredentials.passwords[0].value

# ── 3. AKS Cluster ────────────────────────────────────────────────────────────
Write-Step "Creating AKS Cluster '$AksName' (1x Standard_B2s)..."
az aks create `
    --resource-group $ResourceGroup `
    --name $AksName `
    --node-count 1 `
    --node-vm-size Standard_B2s `
    --enable-addons ingress-appgw `
    --generate-ssh-keys `
    --attach-acr $AcrName `
    --output none

# Use nginx ingress instead via helm (simpler, matches minikube setup)
Write-Host "  AKS cluster created." -ForegroundColor Green

Write-Step "Getting AKS credentials for kubectl..."
az aks get-credentials --resource-group $ResourceGroup --name $AksName --overwrite-existing
Write-Host "  kubectl context set to '$AksName'." -ForegroundColor Green

# ── 4. Install nginx Ingress Controller ───────────────────────────────────────
Write-Step "Installing nginx Ingress Controller via Helm..."
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx 2>$null
helm repo update
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx `
    --namespace ingress-nginx `
    --create-namespace `
    --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-load-balancer-health-probe-request-path"=/healthz
Write-Host "  Waiting for LoadBalancer IP..." -ForegroundColor Yellow
Start-Sleep -Seconds 30
$PublicIp = kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath="{.status.loadBalancer.ingress[0].ip}"
Write-Host "  Ingress IP: $PublicIp" -ForegroundColor Green

# ── 5. Azure Database for PostgreSQL Flexible Server ─────────────────────────
Write-Step "Creating PostgreSQL Flexible Server '$PgServerName'..."
az postgres flexible-server create `
    --resource-group $ResourceGroup `
    --name $PgServerName `
    --location $Location `
    --admin-user $AdminUser `
    --admin-password $DbCatalogPassword `
    --sku-name Standard_B1ms `
    --tier Burstable `
    --storage-size 32 `
    --version 16 `
    --yes `
    --output none
Write-Host "  PostgreSQL server created." -ForegroundColor Green

Write-Step "Creating databases..."
az postgres flexible-server db create `
    --resource-group $ResourceGroup `
    --server-name $PgServerName `
    --database-name catalog_db `
    --output none

az postgres flexible-server db create `
    --resource-group $ResourceGroup `
    --server-name $PgServerName `
    --database-name loan_db `
    --output none
Write-Host "  Databases 'catalog_db' and 'loan_db' created." -ForegroundColor Green

Write-Step "Configuring PostgreSQL firewall (allow AKS)..."
az postgres flexible-server firewall-rule create `
    --resource-group $ResourceGroup `
    --name $PgServerName `
    --rule-name AllowAllAzureIPs `
    --start-ip-address 0.0.0.0 `
    --end-ip-address 0.0.0.0 `
    --output none
Write-Host "  Firewall rule created." -ForegroundColor Green

$PgHost = "$PgServerName.postgres.database.azure.com"
$CatalogDbUrl = "postgresql+asyncpg://${AdminUser}:${DbCatalogPassword}@${PgHost}/catalog_db?ssl=require"
$LoanDbUrl    = "postgresql+asyncpg://${AdminUser}:${DbLoanPassword}@${PgHost}/loan_db?ssl=require"

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

$CatalogDbUserB64    = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($AdminUser))
$CatalogDbPassB64    = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($DbCatalogPassword))
$CatalogDbNameB64    = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("catalog_db"))
$LoanDbUserB64       = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($AdminUser))
$LoanDbPassB64       = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($DbLoanPassword))
$LoanDbNameB64       = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("loan_db"))
$RabbitUserB64       = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("guest"))
$RabbitPassB64       = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("guest"))

$SecretsYaml = @"
apiVersion: v1
kind: Secret
metadata:
  name: libraryhub-secrets
  namespace: default
type: Opaque
data:
  catalog-db-user:     $CatalogDbUserB64
  catalog-db-password: $CatalogDbPassB64
  catalog-db-name:     $CatalogDbNameB64
  loan-db-user:        $LoanDbUserB64
  loan-db-password:    $LoanDbPassB64
  loan-db-name:        $LoanDbNameB64
  rabbitmq-user:       $RabbitUserB64
  rabbitmq-password:   $RabbitPassB64
"@

$SecretsYaml | kubectl apply -f -
kubectl apply -f "$PSScriptRoot/k8s/azure/configmap.yaml"
Write-Host "  Secrets and ConfigMap applied." -ForegroundColor Green

# ── 8. Apply ACR imagePullSecret ──────────────────────────────────────────────
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
Write-Host "ACR_LOGIN_SERVER:   $AcrLoginServer" -ForegroundColor Cyan
Write-Host "ACR_USERNAME:       $AcrUsername" -ForegroundColor Cyan
Write-Host "ACR_PASSWORD:       $AcrPassword" -ForegroundColor Cyan
Write-Host "DB_CATALOG_PASSWORD: $DbCatalogPassword" -ForegroundColor Cyan
Write-Host "DB_LOAN_PASSWORD:    $DbLoanPassword" -ForegroundColor Cyan
Write-Host ""
Write-Host "AKS_RESOURCE_GROUP: $ResourceGroup" -ForegroundColor Cyan
Write-Host "AKS_CLUSTER_NAME:   $AksName" -ForegroundColor Cyan
Write-Host ""
Write-Host "══ Setup complete! Ingress IP: $PublicIp" -ForegroundColor Green
Write-Host "   Add DNS label via Azure Portal or:"
Write-Host "   az network public-ip update --dns-name $DnsLabel ..."
Write-Host "   App will be available at: http://$DnsLabel.$Location.cloudapp.azure.com"

