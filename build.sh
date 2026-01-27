#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit  # Exit on error
set -o pipefail # Catch errors in pipes
set -o nounset  # Exit on undefined variables

echo "=================================="
echo "🚀 Deep-detection Build Process"
echo "=================================="

# Install system dependencies for OpenCV
echo ""
echo "📦 Installing system dependencies..."
apt-get update -qq
apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libfontconfig1 \
    || echo "⚠️  Warning: Some system packages may not be available"

# Install Node.js dependencies
echo ""
echo "🔧 Installing Node.js dependencies..."
npm ci --legacy-peer-deps --prefer-offline --no-audit || npm install --legacy-peer-deps

# Build React frontend
echo ""
echo "🏗️  Building React frontend..."
npm run build

# Verify build output
if [ ! -d "dist" ]; then
    echo "❌ Error: Frontend build failed - dist directory not found"
    exit 1
fi
echo "✅ Frontend build successful"

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --no-cache-dir --upgrade pip setuptools wheel

# Install Python dependencies
echo ""
echo "🐍 Installing Python dependencies..."
pip install --no-cache-dir -r backend/requirements.txt

# Create storage directory
echo ""
echo "📁 Creating storage directories..."
mkdir -p storage/scans

echo ""
echo "=================================="
echo "✅ Build completed successfully!"
echo "=================================="
