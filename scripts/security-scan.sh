#!/usr/bin/env bash
# =============================================================================
# Security Scanner - UAV Platform
# =============================================================================
# Unified entry point for all secret scanning tools.
# Detects the available tools and runs them in sequence.
#
# Usage:
#   bash scripts/security-scan.sh                 # Scan working directory
#   bash scripts/security-scan.sh --ci            # CI mode (exit on first fail)
#   bash scripts/security-scan.sh --all           # Full scan (including history)
#   bash scripts/security-scan.sh --install       # Install all detectors
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'
ALL_PASSED=0

MODE="${1:-default}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  UAV Platform - Security Scanner${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ─── Pre-commit Hook Check ──────────────────────────────────────────────────
check_precommit() {
    echo -e "${YELLOW}[1/4]${NC} Checking pre-commit hook..."
    if [ -f ".git/hooks/pre-commit" ] || git config core.hooksPath | grep -q ".githooks"; then
        echo -e "  ${GREEN}✅ Pre-commit hook is installed${NC}"
    else
        echo -e "  ${YELLOW}⚠  Pre-commit hook NOT installed${NC}"
        echo -e "     Run: bash scripts/install-githooks.sh"
    fi
}

# ─── git-secrets Scan ──────────────────────────────────────────────────────
scan_git_secrets() {
    echo ""
    echo -e "${YELLOW}[2/4]${NC} Running git-secrets..."
    
    if command -v git-secrets &>/dev/null; then
        if [ "$MODE" = "--all" ]; then
            OUTPUT=$(git secrets --scan-history 2>&1 || true)
        else
            OUTPUT=$(git secrets --scan 2>&1 || true)
        fi
        
        if echo "$OUTPUT" | grep -q "error\|violation\|forbidden"; then
            echo -e "  ${RED}❌ Secrets detected by git-secrets${NC}"
            echo "$OUTPUT"
            ALL_PASSED=1
        else
            echo -e "  ${GREEN}✅ No secrets detected${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠  git-secrets not installed${NC}"
        echo -e "     Install: https://github.com/awslabs/git-secrets"
    fi
}

# ─── Pre-commit Hook Direct Scan ────────────────────────────────────────────
scan_precommit() {
    echo ""
    echo -e "${YELLOW}[3/4]${NC} Running pre-commit secret scanner..."
    
    if [ -f ".githooks/pre-commit" ]; then
        # Run the pre-commit scanner logic directly on all files
        if OUTPUT=$(bash .githooks/pre-commit 2>&1); then
            echo -e "  ${GREEN}✅ No secrets detected${NC}"
        else
            echo -e "  ${RED}❌ Potential secrets found${NC}"
            echo "$OUTPUT" | grep -E "⚠|→" || true
            ALL_PASSED=1
        fi
    else
        echo -e "  ${YELLOW}⚠  Pre-commit hook script not found${NC}"
    fi
}

# ─── Manual Pattern Scan ────────────────────────────────────────────────────
scan_manual() {
    echo ""
    echo -e "${YELLOW}[4/4]${NC} Running manual pattern scan..."
    
    # Quick grep for high-priority patterns
    PATTERNS=(
        "-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----"
        "AKIA[0-9A-Z]{16}"
        "ghp_[A-Za-z0-9_]{36}"
        "xox[baprs]-[0-9]{10}"
    )
    
    FOUND=0
    for pattern in "${PATTERNS[@]}"; do
        if git grep -lE "$pattern" -- .gitignore 2>/dev/null || true; then
            FILES=$(git grep -lE "$pattern" 2>/dev/null || true)
            if [ -n "$FILES" ]; then
                echo -e "  ${RED}⚠  Pattern found: ${pattern:0:30}...${NC}"
                echo "$FILES" | head -5 | while read f; do echo "      $f"; done
                FOUND=1
                ALL_PASSED=1
            fi
        fi
    done
    
    if [ "$FOUND" -eq 0 ]; then
        echo -e "  ${GREEN}✅ No critical patterns found${NC}"
    fi
}

# ─── Main ───────────────────────────────────────────────────────────────────

check_precommit
scan_git_secrets
scan_precommit
scan_manual

echo ""
echo -e "${BLUE}========================================${NC}"
if [ "$ALL_PASSED" -eq 0 ]; then
    echo -e "${GREEN}  ✅ All security checks passed${NC}"
else
    echo -e "${RED}  ❌  Some checks found issues${NC}"
    echo -e "     Review the output above before committing"
fi
echo -e "${BLUE}========================================${NC}"

exit "$ALL_PASSED"
