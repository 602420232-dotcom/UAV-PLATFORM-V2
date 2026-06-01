#!/usr/bin/env bash
# =============================================================================
# Key Rotation Script for UAV Platform
# =============================================================================
# Rotates secrets across all environments.
# Designed to be run manually (for dev/test) or by CI/CD pipeline (for prod).
#
# Usage:
#   ./rotate-keys.sh                  # Rotate dev keys (interactive)
#   ./rotate-keys.sh --env=production  # Rotate production keys
#   ./rotate-keys.sh --env=all         # Rotate all environments
#   ./rotate-keys.sh --check           # Check key age only
#
# Key rotation schedule:
#   - JWT Secret:    every 90 days
#   - Encryption Key: every 90 days
#   - DB Password:   every 180 days
#   - API Keys:      every 30 days
#   - SSL Certs:     every 365 days
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ENV="${1:-development}"
ROTATED=0

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  UAV Platform - Key Rotation Tool${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ─── Helpers ────────────────────────────────────────────────────────────────

generate_jwt_secret() {
    openssl rand -base64 32 | tr -d '\n'
}

generate_encryption_key() {
    openssl rand -base64 32 | tr -d '\n'
}

generate_db_password() {
    openssl rand -base64 24 | tr -d '\n' | tr '+/' '-_'
}

generate_api_key() {
    openssl rand -hex 32 | tr -d '\n'
}

# ─── Rotate dev environment ─────────────────────────────────────────────────
rotate_dev() {
    echo -e "${YELLOW}[dev]${NC} Rotating development keys..."
    
    ENV_FILE=".env.dev"
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}[dev]${NC} $ENV_FILE not found, skipping"
        return
    fi
    
    # Backup
    cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%Y%m%d)"
    echo -e "${GREEN}[dev]${NC} Backup created: ${ENV_FILE}.bak.$(date +%Y%m%d)"
    
    # Generate new keys
    NEW_JWT=$(generate_jwt_secret)
    NEW_DB_PASS=$(generate_db_password)
    
    # Update file (macOS vs Linux sed compat)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/^JWT_SECRET=.*/JWT_SECRET=${NEW_JWT}/" "$ENV_FILE"
        sed -i '' "s/^DB_PASSWORD=.*/DB_PASSWORD=${NEW_DB_PASS}/" "$ENV_FILE"
    else
        sed -i "s/^JWT_SECRET=.*/JWT_SECRET=${NEW_JWT}/" "$ENV_FILE"
        sed -i "s/^DB_PASSWORD=.*/DB_PASSWORD=${NEW_DB_PASS}/" "$ENV_FILE"
    fi
    
    echo -e "${GREEN}[dev]${NC} ✅ JWT secret rotated"
    echo -e "${GREEN}[dev]${NC} ✅ DB password rotated"
    ROTATED=$((ROTATED + 2))
}

# ─── Rotate test environment ────────────────────────────────────────────────
rotate_test() {
    echo -e "${YELLOW}[test]${NC} Rotating test environment keys..."
    
    ENV_FILE=".env.test"
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}[test]${NC} $ENV_FILE not found, skipping"
        return
    fi
    
    cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%Y%m%d)"
    
    NEW_JWT=$(generate_jwt_secret)
    NEW_DB_PASS=$(generate_db_password)
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/^JWT_SECRET=.*/JWT_SECRET=${NEW_JWT}/" "$ENV_FILE"
        sed -i '' "s/^DB_PASSWORD=.*/DB_PASSWORD=${NEW_DB_PASS}/" "$ENV_FILE"
    else
        sed -i "s/^JWT_SECRET=.*/JWT_SECRET=${NEW_JWT}/" "$ENV_FILE"
        sed -i "s/^DB_PASSWORD=.*/DB_PASSWORD=${NEW_DB_PASS}/" "$ENV_FILE"
    fi
    
    echo -e "${GREEN}[test]${NC} ✅ JWT secret rotated"
    echo -e "${GREEN}[test]${NC} ✅ DB password rotated"
    ROTATED=$((ROTATED + 2))
}

# ─── Rotate production environment ──────────────────────────────────────────
rotate_prod() {
    echo -e "${YELLOW}[prod]${NC} Rotating production keys..."
    echo -e "${RED}⚠️  Production key rotation should be done via secrets manager!${NC}"
    echo -e "${YELLOW}[prod]${NC} This script generates new values for manual update."
    echo ""
    
    # Only generate, don't write to a tracked file
    echo -e "${BLUE}── New Production Keys ──────────────────────${NC}"
    echo ""
    echo -e "  ${GREEN}JWT_SECRET:${NC}         $(generate_jwt_secret)"
    echo -e "  ${GREEN}ENCRYPTION_KEY:${NC}      $(generate_encryption_key)"
    echo -e "  ${GREEN}DB_PASSWORD:${NC}         $(generate_db_password)"
    echo -e "  ${GREEN}FENGWU_API_KEY:${NC}      $(generate_api_key)"
    echo ""
    echo -e "${YELLOW}  → Update these in your secrets manager (Vault/AWS/Azure)${NC}"
    echo -e "${YELLOW}  → These values are NOT written to any file${NC}"
    echo ""
    
    read -p "  Have you updated the secrets manager? (y/N): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}[prod]${NC} ✅ Production keys rotated (secrets manager updated)"
        ROTATED=$((ROTATED + 4))
    else
        echo -e "${RED}[prod]${NC} ❌ Skipped - update secrets manager before deploying"
    fi
}

# ─── Key age check ──────────────────────────────────────────────────────────
check_age() {
    echo -e "${BLUE}── Key Age Check ────────────────────────────${NC}"
    echo ""
    
    for env_file in .env.dev .env.test; do
        if [ -f "$env_file" ]; then
            created=$(stat -c %Y "$env_file" 2>/dev/null || stat -f %m "$env_file" 2>/dev/null)
            now=$(date +%s)
            age_days=$(( (now - created) / 86400 ))
            
            echo -e "  ${YELLOW}$env_file:${NC} ${age_days} days old"
            if [ "$age_days" -gt 90 ]; then
                echo -e "  ${RED}  ⚠️  Over 90 days - consider rotating${NC}"
            fi
        fi
    done
    echo ""
    exit 0
}

# ─── Main ───────────────────────────────────────────────────────────────────

case "$ENV" in
    --env=development|--env=dev|-d)
        rotate_dev
        ;;
    --env=test|--env=staging|-t)
        rotate_test
        ;;
    --env=production|--env=prod|-p)
        rotate_prod
        ;;
    --env=all|-a)
        rotate_dev
        rotate_test
        echo ""
        rotate_prod
        ;;
    --check|-c)
        check_age
        ;;
    *)
        echo "Usage: $0 [--env=<env> | --check]"
        echo ""
        echo "  --env=dev         Rotate development keys"
        echo "  --env=test        Rotate test/staging keys"
        echo "  --env=production  Generate new production keys (manual update)"
        echo "  --env=all         Rotate all environments"
        echo "  --check           Check key age"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}  Rotation complete: $ROTATED keys rotated${NC}"
echo -e "${BLUE}============================================${NC}"
