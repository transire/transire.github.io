#!/bin/bash
# Install pre-commit hooks for transire.github.io

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_DIR="$(git rev-parse --git-dir 2>/dev/null)"

if [ -z "$GIT_DIR" ]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

echo "📦 Installing pre-commit hooks..."

# Copy pre-commit hook
cp "$SCRIPT_DIR/pre-commit" "$GIT_DIR/hooks/pre-commit"
chmod +x "$GIT_DIR/hooks/pre-commit"

echo "✅ Pre-commit hooks installed successfully!"
echo ""
echo "The following checks will run before each commit:"
echo "  • YAML linting (mkdocs.yml)"
echo "  • Documentation build (strict mode)"
echo "  • Broken link detection"
echo "  • TODO/FIXME comment check"
echo "  • Build artifact validation"
echo ""
echo "To skip hooks temporarily, use: git commit --no-verify"
echo ""
