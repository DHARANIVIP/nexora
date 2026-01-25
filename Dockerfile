# Stage 1: Build React Frontend
FROM node:20-alpine as build-step

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code and build
COPY . .
RUN npm run build

# Stage 2: Python Backend
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (needed for OpenCV)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy Backend Code
COPY backend ./backend

# Copy Built Frontend from Stage 1
# This puts the React build (dist/) into the root of the container
COPY --from=build-step /app/dist ./dist

# Create necessary directories for storage
RUN mkdir -p storage/scans

# Expose port (railway/render usually ignore this and set their own env var PORT, but good for documentation)
EXPOSE 8000

# Run the application
# Use PORT environment variable if set, otherwise default to 8000
CMD python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}

