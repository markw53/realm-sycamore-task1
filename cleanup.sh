#!/usr/bin/env bash
set -e

echo "=== Cleaning source_repo ==="

# Navigate to the repo root (adjust if needed)
cd "$(dirname "$0")/source_repo"

echo "Removing .git directory..."
rm -rf .git

echo "Removing virtual environments..."
rm -rf .venv venv env

echo "Removing Python cache directories..."
find . -type d -name "__pycache__" -exec rm -rf {} +

echo "Removing .pyc files..."
find . -type f -name "*.pyc" -delete

echo "Removing editor swap files..."
find . -type f -name "*.swp" -delete

echo "Removing macOS junk files..."
find . -type f -name ".DS_Store" -delete

echo "=== Cleanup complete ==="
echo "Remaining top-level contents:"
ls -al
