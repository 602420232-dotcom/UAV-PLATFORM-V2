#!/usr/bin/env bash
# =============================================================================
# Install Git Hooks
# =============================================================================
# Links all hooks from .githooks/ to .git/hooks/
# Run this after cloning the repository.
# =============================================================================

set -euo pipefail

HOOKS_DIR=".githooks"
GIT_HOOKS_DIR=".git/hooks"

if [ ! -d "$HOOKS_DIR" ]; then
    echo "❌ Hooks directory not found: $HOOKS_DIR"
    exit 1
fi

if [ ! -d "$GIT_HOOKS_DIR" ]; then
    echo "❌ Git hooks directory not found: $GIT_HOOKS_DIR"
    echo "   Are you in the project root?"
    exit 1
fi

echo "🔗 Installing git hooks from $HOOKS_DIR..."
INSTALLED=0

for hook in "$HOOKS_DIR"/*; do
    hook_name=$(basename "$hook")
    target="$GIT_HOOKS_DIR/$hook_name"
    
    if [ -f "$hook" ]; then
        # Remove existing hook if it's a symlink we created
        if [ -L "$target" ]; then
            rm "$target"
        elif [ -f "$target" ]; then
            echo "  ⚠️  Backing up existing $hook_name to ${target}.bak"
            mv "$target" "${target}.bak"
        fi
        
        # Create symlink
        ln -sf "../../$hook" "$target"
        chmod +x "$target"
        echo "  ✅ Installed: $hook_name"
        INSTALLED=$((INSTALLED + 1))
    fi
done

echo ""
echo "✅ $INSTALLED hooks installed"

# Configure git to use hooks path
git config core.hooksPath .githooks 2>/dev/null || true

echo "💡 Git configured to use core.hooksPath=.githooks"
echo ""

# Test the hook
echo "📝  Testing pre-commit hook..."
echo ""
echo "  Run: git commit -m \"test\"  (should trigger secret scan)"
echo "  Or:  bash .githooks/pre-commit  (test directly)"
