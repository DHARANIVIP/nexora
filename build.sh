#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit  # Exit on error

echo "🔧 Installing Node.js dependencies..."
npm install --legacy-peer-deps

echo "🏗️ Building React frontend..."
npm run build

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "✅ Build completed successfully!"
