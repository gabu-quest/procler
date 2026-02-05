#!/bin/bash
# Install git hooks for local development

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
SCRIPTS_HOOKS="$REPO_ROOT/scripts/hooks"

echo "Installing git hooks..."

# Install pre-push hook
if [ -f "$SCRIPTS_HOOKS/pre-push" ]; then
    cp "$SCRIPTS_HOOKS/pre-push" "$HOOKS_DIR/pre-push"
    chmod +x "$HOOKS_DIR/pre-push"
    echo "✅ Installed pre-push hook (runs tests before push)"
fi

# pre-commit is managed by pre-commit tool, not this script
echo ""
echo "Note: pre-commit hooks are managed by 'pre-commit install'"
echo "Run 'uv run pre-commit install' if not already set up."
echo ""
echo "Done!"
