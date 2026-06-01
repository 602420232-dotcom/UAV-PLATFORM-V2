#!/usr/bin/env bash
# =============================================================================
# Secrets Manager Integration - Quick Setup
# =============================================================================
# This script provides examples for integrating with common secrets managers.
# Run the relevant section based on your infrastructure.
#
# Usage:
#   ./integrate-secrets-manager.sh vault        # HashiCorp Vault
#   ./integrate-secrets-manager.sh aws          # AWS Secrets Manager
#   ./integrate-secrets-manager.sh azure        # Azure Key Vault
#   ./integrate-secrets-manager.sh check        # Check if secrets are accessible
# =============================================================================

set -euo pipefail

CMD="${1:-help}"

case "$CMD" in

# ─── HashiCorp Vault ────────────────────────────────────────────────────────
vault)
    echo "=== HashiCorp Vault Integration ==="
    echo ""
    
    # Prerequisites
    if ! command -v vault &>/dev/null; then
        echo "Installing Vault CLI..."
        # Linux
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo apt-get update && sudo apt-get install -y vault
        # macOS
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install vault
        fi
    fi
    
    VAULT_ADDR="${VAULT_ADDR:-https://vault.uav-platform.com:8200}"
    VAULT_TOKEN="${VAULT_TOKEN:-}"
    
    if [ -z "$VAULT_TOKEN" ]; then
        echo "Please set VAULT_TOKEN environment variable"
        echo "  export VAULT_TOKEN=your-token-here"
        exit 1
    fi
    
    # Create/update secrets
    vault kv put secret/uav-platform/production \
        jwt_secret="$(openssl rand -base64 32)" \
        db_password="$(openssl rand -base64 24)" \
        fengwu_api_key="$(openssl rand -hex 32)" \
        encryption_key="$(openssl rand -base64 32)"
    
    echo "✅ Vault secrets created at: secret/uav-platform/production"
    echo ""
    echo "To read secrets at deploy time:"
    echo "  vault kv get -field=jwt_secret secret/uav-platform/production"
    ;;

# ─── AWS Secrets Manager ────────────────────────────────────────────────────
aws)
    echo "=== AWS Secrets Manager Integration ==="
    echo ""
    
    if ! command -v aws &>/dev/null; then
        echo "AWS CLI not found. Install from: https://aws.amazon.com/cli/"
        exit 1
    fi
    
    SECRET_NAME="uav-platform/production"
    
    # Create secret
    aws secretsmanager create-secret \
        --name "$SECRET_NAME" \
        --description "UAV Platform Production Secrets" \
        --secret-string "{
            \"jwt_secret\": \"$(openssl rand -base64 32)\",
            \"db_password\": \"$(openssl rand -base64 24)\",
            \"fengwu_api_key\": \"$(openssl rand -hex 32)\",
            \"encryption_key\": \"$(openssl rand -base64 32)\"
        }" 2>/dev/null || {
        # Update existing
        aws secretsmanager update-secret \
            --secret-id "$SECRET_NAME" \
            --secret-string "{
                \"jwt_secret\": \"$(openssl rand -base64 32)\",
                \"db_password\": \"$(openssl rand -base64 24)\",
                \"fengwu_api_key\": \"$(openssl rand -hex 32)\",
                \"encryption_key\": \"$(openssl rand -base64 32)\"
            }"
    }
    
    echo "✅ AWS Secrets Manager updated: $SECRET_NAME"
    echo ""
    echo "To retrieve at deploy time:"
    echo "  aws secretsmanager get-secret-value --secret-id $SECRET_NAME --query SecretString --output text"
    ;;

# ─── Azure Key Vault ────────────────────────────────────────────────────────
azure)
    echo "=== Azure Key Vault Integration ==="
    echo ""
    
    if ! command -v az &>/dev/null; then
        echo "Azure CLI not found. Install from: https://docs.microsoft.com/cli/azure/"
        exit 1
    fi
    
    VAULT_NAME="${AZURE_VAULT_NAME:-uav-platform-kv}"
    
    # Ensure logged in
    az account show 2>/dev/null || az login
    
    # Create vault if not exists
    az keyvault show --name "$VAULT_NAME" 2>/dev/null || \
        az keyvault create --name "$VAULT_NAME" --resource-group uav-platform-rg
    
    # Set secrets
    az keyvault secret set --vault-name "$VAULT_NAME" --name "jwt-secret" --value "$(openssl rand -base64 32)"
    az keyvault secret set --vault-name "$VAULT_NAME" --name "db-password" --value "$(openssl rand -base64 24)"
    az keyvault secret set --vault-name "$VAULT_NAME" --name "fengwu-api-key" --value "$(openssl rand -hex 32)"
    az keyvault secret set --vault-name "$VAULT_NAME" --name "encryption-key" --value "$(openssl rand -base64 32)"
    
    echo "✅ Azure Key Vault updated: $VAULT_NAME"
    echo ""
    echo "To retrieve at deploy time:"
    echo "  az keyvault secret show --vault-name $VAULT_NAME --name jwt-secret --query value -o tsv"
    ;;

# ─── Check Connectivity ─────────────────────────────────────────────────────
check)
    echo "=== Secrets Manager Connectivity Check ==="
    FAILED=0
    
    echo -n "  Vault (VAULT_ADDR=${VAULT_ADDR:-not set})... "
    if [ -n "${VAULT_ADDR:-}" ]; then
        curl -sf "$VAULT_ADDR/v1/sys/health" &>/dev/null && echo "OK" || { echo "FAIL"; FAILED=1; }
    else
        echo "SKIP (not configured)"
    fi
    
    echo -n "  AWS (profile=${AWS_PROFILE:-default})... "
    if command -v aws &>/dev/null; then
        aws sts get-caller-identity &>/dev/null && echo "OK" || { echo "FAIL"; FAILED=1; }
    else
        echo "SKIP (not installed)"
    fi
    
    echo -n "  Azure (subscription=${AZURE_SUBSCRIPTION_ID:-not set})... "
    if command -v az &>/dev/null; then
        az account show &>/dev/null && echo "OK" || { echo "FAIL"; FAILED=1; }
    else
        echo "SKIP (not installed)"
    fi
    
    exit $FAILED
    ;;

*)
    echo "Usage: $0 {vault|aws|azure|check}"
    echo ""
    echo "  vault   HashiCorp Vault integration"
    echo "  aws     AWS Secrets Manager integration"
    echo "  azure   Azure Key Vault integration"
    echo "  check   Check secrets manager connectivity"
    ;;
esac
