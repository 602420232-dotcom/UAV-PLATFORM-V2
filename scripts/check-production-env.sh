#!/usr/bin/env bash
# =============================================================================
# Production Environment Configuration Check
# =============================================================================
# This script validates production deployment configuration before release.
# Run as part of CI/CD pipeline for all production deployments.
#
# Usage:
#   chmod +x check-production-env.sh
#   export ENVIRONMENT=production
#   export CORS_ORIGINS=https://api.uav-platform.com
#   export FENGWU_API_KEY=...  (required for fengwu-service)
#   ./check-production-env.sh
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
FAILED=0

print_result() {
    if [ "$2" -eq 0 ]; then
        echo -e "${GREEN}[PASS]${NC} $1"
    else
        echo -e "${RED}[FAIL]${NC} $1"
        FAILED=1
    fi
}

echo "=========================================="
echo " Production Environment Check"
echo "=========================================="
echo ""

# ─── Environment Mode Check ────────────────────────────────────────────────
echo "--- Environment Mode ---"
if [ "${ENVIRONMENT:-}" = "production" ] || [ "${FENGWU_ENV:-}" = "production" ]; then
    print_result "ENVIRONMENT is set to production" 0
else
    print_result "ENVIRONMENT is NOT set to production (current: ${ENVIRONMENT:-unset})" 1
fi

# ─── CORS Configuration ────────────────────────────────────────────────────
echo ""
echo "--- CORS Configuration ---"
if [ -n "${CORS_ORIGINS:-}" ]; then
    print_result "CORS_ORIGINS is set: ${CORS_ORIGINS}" 0
    # Check for wildcard origins
    if [[ "${CORS_ORIGINS}" == "*" ]]; then
        echo -e "${RED}  └─ WARNING: CORS_ORIGINS contains wildcard '*' - this is INSECURE for production${NC}"
        FAILED=1
    fi
    # Check for localhost in production
    if [[ "${CORS_ORIGINS}" == *"localhost"* ]]; then
        echo -e "${YELLOW}  └─ WARNING: CORS_ORIGINS contains 'localhost' - verify this is intended${NC}"
    fi
else
    print_result "CORS_ORIGINS is NOT set (required for production)" 1
fi

# ─── API Key Check ─────────────────────────────────────────────────────────
echo ""
echo "--- API Key Configuration ---"
if [ -n "${FENGWU_API_KEY:-}" ]; then
    print_result "FENGWU_API_KEY is set" 0
    if [ ${#FENGWU_API_KEY} -lt 16 ]; then
        echo -e "${YELLOW}  └─ WARNING: FENGWU_API_KEY is too short (< 16 chars)${NC}"
    fi
else
    echo -e "${YELLOW}  └─ INFO: FENGWU_API_KEY not checked (only required if fengwu-service is deployed)${NC}"
fi

# ─── JPA Configuration ─────────────────────────────────────────────────────
echo ""
echo "--- JPA Configuration ---"
if [ "${JPA_DDL_AUTO:-}" = "validate" ] || [ "${JPA_DDL_AUTO:-}" = "none" ]; then
    print_result "JPA_DDL_AUTO is set to '${JPA_DDL_AUTO}' (safe for production)" 0
elif [ "${JPA_DDL_AUTO:-}" = "update" ]; then
    echo -e "${RED}[FAIL]${NC} JPA_DDL_AUTO is 'update' - SET TO 'validate' OR 'none' FOR PRODUCTION"
    FAILED=1
elif [ -z "${JPA_DDL_AUTO:-}" ]; then
    echo -e "${YELLOW}  └─ INFO: JPA_DDL_AUTO not set (defaults to 'update' - set explicitly for production)${NC}"
fi

# ─── Management Port ───────────────────────────────────────────────────────
echo ""
echo "--- Management (Actuator) Port ---"
if [ -n "${MANAGEMENT_SERVER_PORT:-}" ]; then
    print_result "MANAGEMENT_SERVER_PORT is set to ${MANAGEMENT_SERVER_PORT}" 0
    if [ "${MANAGEMENT_SERVER_PORT}" = "0" ]; then
        echo -e "${YELLOW}  └─ WARNING: Port 0 means random port - firewall rules may not work${NC}"
    fi
else
    echo -e "${YELLOW}  └─ INFO: MANAGEMENT_SERVER_PORT not set (actuator shares main port)${NC}"
fi

# ─── SSL Configuration ─────────────────────────────────────────────────────
echo ""
echo "--- SSL Configuration ---"
if [ "${SSL_ENABLED:-}" = "true" ]; then
    print_result "SSL_ENABLED is true" 0
    if [ -z "${SSL_KEY_STORE:-}" ]; then
        echo -e "${RED}  └─ WARNING: SSL enabled but SSL_KEY_STORE not set${NC}"
    fi
else
    echo -e "${YELLOW}  └─ INFO: SSL is not enabled (ensure TLS termination at reverse proxy)${NC}"
fi

# ─── Result ────────────────────────────────────────────────────────────────
echo ""
echo "=========================================="
if [ "$FAILED" -eq 0 ]; then
    echo -e " ${GREEN}All production checks passed!${NC}"
    exit 0
else
    echo -e " ${RED}One or more production checks FAILED.${NC}"
    echo " Review the issues above before deploying to production."
    exit 1
fi
