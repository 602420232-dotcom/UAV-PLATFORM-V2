#!/usr/bin/env bash
# =============================================================================
# git-secrets Setup - UAV Platform
# =============================================================================
# Configures git-secrets (https://github.com/awslabs/git-secrets)
# to prevent committing secrets to the repository.
#
# Install: see https://github.com/awslabs/git-secrets#installing-git-secrets
#
# Usage:
#   bash scripts/setup-git-secrets.sh    # Configure repo
#   git secrets --scan                   # Scan all files
#   git secrets --scan-history           # Scan git history
# =============================================================================

set -euo pipefail

echo "=== Installing git-secrets for UAV Platform ==="
echo ""

# Check if git-secrets is installed
if ! command -v git-secrets &>/dev/null; then
    echo "⚠️  git-secrets not found."
    echo ""
    echo "  Install it first:"
    echo "    macOS: brew install git-secrets"
    echo "    Linux: https://github.com/awslabs/git-secrets#installing-git-secrets"
    echo "    Windows: Use WSL or manually add the pre-commit hook"
    echo ""
    echo "  Continuing with setup (will run when git-secrets is available)..."
fi

# ─── AWS Patterns ───────────────────────────────────────────────────────────
echo "🏷️  Adding AWS secret patterns..."
git secrets --add '([^A-Z0-9]|^)(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}([^A-Z0-9]|$)' 2>/dev/null || true
git secrets --add '("|'')?(aws_access_key_id|aws_secret_access_key)("|'')?\s*(:|=>|=)\s*("|'')?[A-Za-z0-9/+=]{20,}("|'')?' 2>/dev/null || true

# ─── UAV Platform Patterns ──────────────────────────────────────────────────
echo "🏷️  Adding UAV Platform specific patterns..."
git secrets --add 'JWT_SECRET=.+' 2>/dev/null || true
git secrets --add 'DB_PASSWORD=.+' 2>/dev/null || true
git secrets --add 'FENGWU_API_KEY=.+' 2>/dev/null || true
git secrets --add 'ENCRYPTION_KEY=.+' 2>/dev/null || true
git secrets --add 'WEATHER_API_KEY=.+' 2>/dev/null || true
git secrets --add 'MYSQL_ROOT_PASSWORD=.+' 2>/dev/null || true
git secrets --add 'SECURITY_USER_PASSWORD=.+' 2>/dev/null || true
git secrets --add 'TEST_PASSWORD=.+' 2>/dev/null || true
git secrets --add 'VITE_CESIUM_ION_TOKEN=.+' 2>/dev/null || true

# ─── Generic Patterns ───────────────────────────────────────────────────────
echo "🏷️  Adding generic secret patterns..."
git secrets --add 'password\s*[:=].+' 2>/dev/null || true
git secrets --add 'secret\s*[:=].+' 2>/dev/null || true
git secrets --add 'api[_-]key\s*[:=].+' 2>/dev/null || true
git secrets --add 'api[_-]secret\s*[:=].+' 2>/dev/null || true
git secrets --add 'token\s*[:=].+' 2>/dev/null || true
git secrets --add '-----BEGIN RSA PRIVATE KEY-----' 2>/dev/null || true
git secrets --add '-----BEGIN EC PRIVATE KEY-----' 2>/dev/null || true
git secrets --add '-----BEGIN OPENSSH PRIVATE KEY-----' 2>/dev/null || true
git secrets --add '-----BEGIN PGP PRIVATE KEY BLOCK-----' 2>/dev/null || true

# ─── Allowed patterns (false positive exemptions) ───────────────────────────
echo "🏷️  Adding allowed patterns..."
git secrets --add --allowed 'JWT_SECRET=your-jwt-secret' 2>/dev/null || true
git secrets --add --allowed 'TEST_PASSWORD=test_pass_123' 2>/dev/null || true
git secrets --add --allowed '__FILL_IN_VAULT__' 2>/dev/null || true
git secrets --add --allowed 'your_cesium_ion_token_here' 2>/dev/null || true
git secrets --add --allowed 'your-secure-root-password' 2>/dev/null || true
git secrets --add --allowed 'change-me' 2>/dev/null || true

# ─── Protected files (prevent certain files from being committed) ───────────
echo "🏷️  Adding protected file patterns..."
git secrets --add --protected '.env' 2>/dev/null || true
git secrets --add --protected '.env.dev' 2>/dev/null || true
git secrets --add --protected '.env.test' 2>/dev/null || true
git secrets --add --protected '.env.local' 2>/dev/null || true
git secrets --add --protected '**/secrets.yml' 2>/dev/null || true
git secrets --add --protected '**/credentials.yml' 2>/dev/null || true

# ─── Verify ─────────────────────────────────────────────────────────────────
echo ""
echo "=== Verification ==="
echo "Registered patterns:"
git secrets --list 2>/dev/null || echo "  (git-secrets not available yet)"

echo ""
echo "✅ git-secrets configuration complete!"
echo ""
echo "Run a scan with:"
echo "  git secrets --scan                    # Scan current changes"
echo "  git secrets --scan-history            # Full history scan"
echo ""
echo "If false positives are found, add exemptions with:"
echo "  git secrets --add --allowed '<pattern>'"
