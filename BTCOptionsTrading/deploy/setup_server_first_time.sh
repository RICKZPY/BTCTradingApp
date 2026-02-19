#!/bin/bash

# First-Time Server Setup Script for Daily Data Collector
# This script sets up the project on a fresh server

set -e  # Exit on any error

echo "=========================================="
echo "First-Time Server Setup"
echo "=========================================="
echo ""

# Configuration
REPO_URL="https://github.com/RICKZPY/BTCTradingApp.git"
PROJECT_DIR="/root/BTCTradingApp"
BACKEND_DIR="$PROJECT_DIR/BTCOptionsTrading/backend"

# Step 1: Check if git is installed
echo "Step 1: Checking git installation..."
if ! command -v git &> /dev/null; then
    echo "Git not found. Installing git..."
    yum install -y git || apt-get install -y git
else
    echo "✓ Git is already installed"
fi

# Step 2: Check if Python 3 is installed
echo ""
echo "Step 2: Checking Python 3 installation..."
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Installing Python 3..."
    yum install -y python3 python3-pip || apt-get install -y python3 python3-pip
else
    echo "✓ Python 3 is already installed"
    python3 --version
fi

# Step 3: Clone or update repository
echo ""
echo "Step 3: Setting up repository..."
if [ -d "$PROJECT_DIR" ]; then
    echo "Project directory exists. Pulling latest changes..."
    cd "$PROJECT_DIR"
    git pull origin main || git pull origin master
else
    echo "Cloning repository..."
    git clone "$REPO_URL" "$PROJECT_DIR"
fi

# Step 4: Navigate to backend directory
echo ""
echo "Step 4: Navigating to backend directory..."
cd "$BACKEND_DIR"
echo "✓ Current directory: $(pwd)"

# Step 5: Install Python dependencies
echo ""
echo "Step 5: Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    echo "✓ Dependencies installed"
else
    echo "⚠ Warning: requirements.txt not found"
fi

# Step 6: Create necessary directories
echo ""
echo "Step 6: Creating necessary directories..."
mkdir -p logs
mkdir -p data/daily_snapshots
mkdir -p data/downloads
mkdir -p data/exports
echo "✓ Directories created"

# Step 7: Set permissions
echo ""
echo "Step 7: Setting file permissions..."
chmod +x daily_data_collector.py
chmod +x setup_daily_collection.sh
echo "✓ Permissions set"

# Step 8: Test the collector
echo ""
echo "Step 8: Testing data collector..."
echo "Running test collection for BTC..."
python3 daily_data_collector.py --currency BTC --test

# Step 9: Setup cron job
echo ""
echo "Step 9: Setting up daily cron job..."
read -p "Do you want to setup the daily cron job now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./setup_daily_collection.sh
    echo "✓ Cron job configured"
else
    echo "⚠ Skipped cron job setup. Run './setup_daily_collection.sh' manually later."
fi

# Step 10: Summary
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Project location: $BACKEND_DIR"
echo "Logs location: $BACKEND_DIR/logs"
echo "Data location: $BACKEND_DIR/data/daily_snapshots"
echo ""
echo "To manually run the collector:"
echo "  cd $BACKEND_DIR"
echo "  python3 daily_data_collector.py --currency BTC"
echo ""
echo "To check cron jobs:"
echo "  crontab -l"
echo ""
echo "To view logs:"
echo "  tail -f $BACKEND_DIR/logs/daily_collector.log"
echo ""
