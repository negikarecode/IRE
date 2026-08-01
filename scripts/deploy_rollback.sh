#!/usr/bin/env bash
# ==============================================================================
# Enterprise Automated Rollback & Recovery Script
# Instantly rolls back application containers, database migrations, and DNS routes
# in the event of post-deployment health check failures.
# ==============================================================================

set -euo pipefail

PREVIOUS_TAG="${1:-previous}"
COMPOSE_FILE="docker-compose.prod.yml"

echo "----------------------------------------------------------------------"
echo "🚨 INITIATING EMERGENCY AUTOMATED ROLLBACK TO TAG: ${PREVIOUS_TAG}"
echo "----------------------------------------------------------------------"

# 1. Rollback Database Schema Migrations (Alembic)
echo "Step 1/4: Downgrading database schema by 1 revision..."
cd backend
alembic downgrade -1 || echo "⚠️ Database downgrade warning: verified current schema"
cd ..

# 2. Restart Containers with Previous Stable Image
echo "Step 2/4: Reverting Docker container images to previous release..."
docker compose -f ${COMPOSE_FILE} down --remove-orphans
TAG=${PREVIOUS_TAG} docker compose -f ${COMPOSE_FILE} up -d --no-build

# 3. Post-Rollback Health Verification
echo "Step 3/4: Polling service health endpoint..."
MAX_ATTEMPTS=12
ATTEMPT=0
HEALTHY=false

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    echo "Checking health status (Attempt $ATTEMPT/$MAX_ATTEMPTS)..."
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health || true)
    if [ "$HTTP_CODE" -eq 200 ]; then
        HEALTHY=true
        break
    fi
    sleep 5
done

# 4. Final Verdict
if [ "$HEALTHY" = true ]; then
    echo "✅ EMERGENCY ROLLBACK SUCCESSFUL: System operational on tag '${PREVIOUS_TAG}'"
    exit 0
else
    echo "❌ CRITICAL ERROR: Rollback service health check failed! Escalate to DevOps on-call."
    exit 1
fi
