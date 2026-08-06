#!/bin/bash
# ============================================================
# Hody-Telepro — Automated PyPI Publishing Script
# ============================================================
# Usage:
#   ./publish.sh              # Full publish to PyPI
#   ./publish.sh test         # Publish to TestPyPI (for testing)
#   ./publish.sh build-only   # Build only, don't upload
# ============================================================

set -e

echo "🚀 Hody-Telepro Publishing Script"
echo "================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ─── Step 1: Install dependencies ───────────────────────────

echo -e "${CYAN}[1/6]${NC} Installing build tools..."
pip install --upgrade build setuptools wheel twine 2>/dev/null

# ─── Step 2: Clean previous builds ──────────────────────────

echo -e "${CYAN}[2/6]${NC} Cleaning previous builds..."
rm -rf build/ dist/ src/hody_telepro.egg-info/
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# ─── Step 3: Run tests ──────────────────────────────────────

echo -e "${CYAN}[3/6]${NC} Running tests..."
PYTHONPATH=src python3 -m pytest tests/ -v --tb=short
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Tests failed! Aborting publish.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ All tests passed.${NC}"

# ─── Step 4: Build package ──────────────────────────────────

echo -e "${CYAN}[4/6]${NC} Building package..."
python3 -m build

echo ""
echo -e "${GREEN}📦 Built files:${NC}"
ls -lh dist/
echo ""

# ─── Step 5: Check package ──────────────────────────────────

echo -e "${CYAN}[5/6]${NC} Checking package metadata..."
twine check dist/*

# ─── Step 6: Upload ─────────────────────────────────────────

MODE="${1:-publish}"

if [ "$MODE" = "build-only" ]; then
    echo -e "${YELLOW}⏭️  Skipping upload (build-only mode).${NC}"
    exit 0
fi

if [ "$MODE" = "test" ]; then
    echo -e "${YELLOW}[6/6]${NC} Uploading to TestPyPI..."
    twine upload --repository testpypi dist/*
elif [ "$MODE" = "publish" ]; then
    echo -e "${YELLOW}[6/6]${NC} Uploading to PyPI..."
    echo -e "${RED}⚠️  This will publish to the LIVE PyPI!${NC}"
    echo -e "   Press Ctrl+C to cancel, or Enter to continue..."
    read -r
    twine upload dist/*
else
    echo -e "${RED}Unknown mode: $MODE${NC}"
    echo "Usage: ./publish.sh [publish|test|build-only]"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Successfully published to PyPI!${NC}"
echo -e "${CYAN}   pip install hody-telepro${NC}"
echo ""
echo "================================="
echo "🎉 Hody-Telepro is now live!"
echo "================================="
