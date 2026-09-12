#!/usr/bin/env bash
# ==============================================================================
# Financial Access Intelligence Layer (FAIL) — Directory Scaffolding Script
# ==============================================================================

set -euo pipefail

echo "🚀 Generating Financial Access Intelligence Layer repository structure..."

# 1. Application entrypoints
mkdir -p apps/api/static
mkdir -p apps/worker

# 2. Domain Layer (DDD - Pure Business Rules, Zero External Dependencies)
mkdir -p src/domain/access_index
mkdir -p src/domain/barriers
mkdir -p src/domain/interventions
mkdir -p src/domain/users
mkdir -p src/domain/shared

# 3. Application Layer (Use Cases & Orchestration)
mkdir -p src/application/access_index
mkdir -p src/application/barriers
mkdir -p src/application/interventions
mkdir -p src/application/payments
mkdir -p src/application/common

# 4. Infrastructure Layer (Database, Cache, ML, Observability, Security)
mkdir -p src/infrastructure/database
mkdir -p src/infrastructure/cache
mkdir -p src/infrastructure/events
mkdir -p src/infrastructure/ml/scoring
mkdir -p src/infrastructure/ml/models
mkdir -p src/infrastructure/ml/features
mkdir -p src/infrastructure/observability
mkdir -p src/infrastructure/security

# 5. Integrations Layer (Open Payments Anti-Corruption Layer)
mkdir -p src/integrations/open_payments

# 6. Test Suite (Pytest Pyramid)
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/api
mkdir -p tests/open_payments
mkdir -p tests/fixtures

# 7. Documentation (MkDocs Architecture & Specifications)
mkdir -p docs/architecture
mkdir -p docs/domain
mkdir -p docs/financial_access_index
mkdir -p docs/interventions
mkdir -p docs/open_payments
mkdir -p docs/api

# 8. Data, Notebooks & Scripts
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/synthetic
mkdir -p notebooks
mkdir -p scripts
mkdir -p infrastructure/docker
mkdir -p infrastructure/compose

# 9. Touch __init__.py package markers
touch src/__init__.py
touch src/domain/__init__.py
touch src/domain/access_index/__init__.py
touch src/domain/barriers/__init__.py
touch src/domain/interventions/__init__.py
touch src/domain/users/__init__.py
touch src/domain/shared/__init__.py
touch src/application/__init__.py
touch src/application/access_index/__init__.py
touch src/application/barriers/__init__.py
touch src/application/interventions/__init__.py
touch src/application/payments/__init__.py
touch src/application/common/__init__.py
touch src/infrastructure/__init__.py
touch src/infrastructure/database/__init__.py
touch src/infrastructure/cache/__init__.py
touch src/infrastructure/events/__init__.py
touch src/infrastructure/ml/__init__.py
touch src/infrastructure/observability/__init__.py
touch src/infrastructure/security/__init__.py
touch src/integrations/__init__.py
touch src/integrations/open_payments/__init__.py

echo "✅ Directory structure successfully scaffolded!"
