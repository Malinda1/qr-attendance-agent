#!/bin/bash

# QR Attendance Agent - Railway Deployment Startup Script

echo "================================================"
echo "🚀 Starting QR Attendance Agent"
echo "================================================"

# Install system dependencies for Chrome/Chromium
echo "📦 Installing system dependencies..."
apt-get update
apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1

# Install Chrome
echo "🌐 Installing Google Chrome..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
apt-get update
apt-get install -y google-chrome-stable

# Verify Chrome installation
echo "✅ Chrome installed: $(google-chrome --version)"

# Create necessary directories
echo "📁 Creating application directories..."
mkdir -p logs qr_codes screenshots

# Set permissions
chmod +x start.sh

# Set environment variables
export PYTHONUNBUFFERED=1

# Get port from Railway or default to 8000
PORT=${PORT:-8000}
echo "🌍 Server will run on port: $PORT"

# Start the application
echo "================================================"
echo "🎯 Starting FastAPI application..."
echo "================================================"

cd backend
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --log-level info