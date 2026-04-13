#!/usr/bin/env bash
# mutmut.sh – Mutation Testing für LibraryHub (via WSL)
#
# Verwendung:
#   bash mutmut.sh                    # beide Services
#   bash mutmut.sh catalog            # nur catalog-service
#   bash mutmut.sh loan               # nur loan-service
#   bash mutmut.sh catalog --results  # nur Ergebnisse anzeigen (kein neuer Run)
#
# Voraussetzungen (einmalig, automatisch erledigt falls nötig):
#   - WSL Ubuntu mit Python 3.11 (deadsnakes PPA)
#   - ~/muttest/{catalog,loan}/ werden bei jedem Aufruf frisch synchronisiert
#
# Hintergrund: mutmut 2.x läuft auf Windows nicht nativ (Issue #397).
# Dieses Skript kopiert die Sources in den WSL-Heimordner (keine Windows-Mounts)
# und führt mutmut dort aus, um lib64-Symlink- und Python-Pfad-Probleme zu vermeiden.

set -euo pipefail

# ── Konfiguration ─────────────────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WSL_DISTRO="Ubuntu"
PYTHON="python3.11"
MUTMUT_VERSION="mutmut<3"

# Services die ausgeführt werden sollen
SERVICES=()
RESULTS_ONLY=false

for arg in "$@"; do
  case "$arg" in
    catalog) SERVICES+=("catalog") ;;
    loan)    SERVICES+=("loan") ;;
    --results) RESULTS_ONLY=true ;;
    *) echo "Unknown argument: $arg" >&2; exit 1 ;;
  esac
done

# Default: beide Services
if [ ${#SERVICES[@]} -eq 0 ]; then
  SERVICES=("catalog" "loan")
fi

# ── Hilfsfunktionen ───────────────────────────────────────────────────────────
wsl_run() {
  wsl.exe -d "$WSL_DISTRO" -e bash -c "$1"
}

setup_service() {
  local svc="$1"         # "catalog" oder "loan"
  local src_dir          # Windows-Quellpfad (als WSL-Mount)
  local wsl_dir="/root/muttest/$svc"
  local svc_full

  case "$svc" in
    catalog) svc_full="catalog-service" ;;
    loan)    svc_full="loan-service" ;;
  esac

  src_dir="/mnt/c/projekte/python/other/library-hub/$svc_full"

  echo "=== [$svc] Syncing sources ==="
  wsl_run "
    mkdir -p $wsl_dir
    rsync -a \
      --exclude='.venv' --exclude='__pycache__' \
      --exclude='*.egg-info' --exclude='.mutmut-cache' \
      $src_dir/ $wsl_dir/
  "

  echo "=== [$svc] Setting up venv ==="
  wsl_run "
    cd $wsl_dir
    if [ ! -f .venv/bin/mutmut ]; then
      $PYTHON -m venv .venv
      .venv/bin/pip install -q --upgrade pip
      .venv/bin/pip install -q -e '.'
      .venv/bin/pip install -q pytest pytest-asyncio pytest-cov anyio httpx '$MUTMUT_VERSION'
    fi
  "

  echo "=== [$svc] Patching runner in pyproject.toml ==="
  wsl_run "
    cd $wsl_dir
    sed -i \"s|runner = \\\"python.*-m pytest|runner = \\\"$wsl_dir/.venv/bin/python3 -m pytest|g\" pyproject.toml
  "
}

run_mutmut() {
  local svc="$1"
  local wsl_dir="/root/muttest/$svc"

  if [ "$RESULTS_ONLY" = true ]; then
    echo "=== [$svc] Results ==="
    wsl_run "cd $wsl_dir && .venv/bin/mutmut results"
  else
    echo "=== [$svc] Running mutmut ==="
    wsl_run "cd $wsl_dir && rm -f .mutmut-cache && .venv/bin/mutmut run 2>&1 | grep -E 'Checking|🎉|🙁|Done'"
    echo "=== [$svc] Results ==="
    wsl_run "cd $wsl_dir && .venv/bin/mutmut results"
  fi
}

print_score() {
  local svc="$1"
  local wsl_dir="/root/muttest/$svc"
  echo ""
  echo "=== [$svc] Mutation Score ==="
  wsl_run "
    cd $wsl_dir
    survived=\$(.venv/bin/mutmut results 2>&1 | grep -oP '(?<=Survived 🙁 \()\d+' || echo 0)
    suspicious=\$(.venv/bin/mutmut results 2>&1 | grep -oP '(?<=Suspicious 🤔 \()\d+' || echo 0)
    # Total aus Cache schätzen (letzte Zahl aus 'Checking mutants')
    echo \"Survived: \$survived | Suspicious: \$suspicious\"
    echo \"Ziel: ≥ 80% | Port-@abstractmethod-Mutanten (ca. 10-16 pro Service) sind strukturell nicht killbar\"
  "
}

# ── Einmalige System-Deps prüfen ──────────────────────────────────────────────
echo "=== Checking WSL prerequisites ==="
wsl_run "
  $PYTHON --version 2>/dev/null || (
    echo 'Python 3.11 not found, installing...'
    add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null
    apt-get update -qq
    apt-get install -y python3.11 python3.11-venv rsync
  )
  echo 'Python OK: '\$($PYTHON --version)
"

# ── Hauptschleife ─────────────────────────────────────────────────────────────
for svc in "${SERVICES[@]}"; do
  if [ "$RESULTS_ONLY" = false ]; then
    setup_service "$svc"
  fi
  run_mutmut "$svc"
  print_score "$svc"
done

echo ""
echo "✅ Done. Surviving mutants that are structurally unkillable:"
echo "   - Port @abstractmethod mutations (book_repository, loan_repository, etc.)"
echo "   - Type annotation mutations (str | None / date | None field defaults)"
echo "   - isbn.py: 'total += value * (i+1)' → 'total -= ...' (ISBN-10 checksum)"
echo "     Reason: (-x) % 11 == 0 iff x % 11 == 0 — negating the sum is mathematically"
echo "     equivalent; no test input can distinguish += from -= for valid/invalid ISBNs."
echo "   These do NOT count against the ≥ 80% target."

