#!/bin/bash
# Build frontend and copy to static/ for production serving

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
STATIC_DIR="$PROJECT_ROOT/procler/static"

echo "Building frontend..."
cd "$FRONTEND_DIR"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build for production
npm run build

# Clean old static files
echo "Cleaning old static files..."
rm -rf "$STATIC_DIR"
mkdir -p "$STATIC_DIR"

# Copy build output
echo "Copying build to static/..."
cp -r "$FRONTEND_DIR/dist/"* "$STATIC_DIR/"

echo "Build complete! Static files in: $STATIC_DIR"
ls -la "$STATIC_DIR"
