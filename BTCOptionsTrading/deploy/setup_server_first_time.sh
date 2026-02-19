#!/bin/bash

# ============================================================================
# First-Time Server Setup Script for BTC Options Trading System
# ============================================================================
# This script sets up the server environment for the first time
# Run this ONCE after cloning the project to the server
#
# Usage:
#   chmod +x setup_server_first_time.sh
#   ./setup_server_first_time.sh
# ============================================================================

set -e  # Exit on any error

echo "=========================================="
echo "BTC Options Trading - First Time Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "Project root: $PROJECT_ROOT"
echo "Backend directory: $BACKEND_DIR"
echo ""

# ============================================================================
# Step 1: Check Python version
# ============================================================================
echo -e "${YELLOW}Step 1: Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed${NC}"
    echo "Please install Python 3.7 or higher first"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python version: $PYTHON_VERSION${NC}"
echo ""

# ============================================================================
# Step 2: Check pip
# ============================================================================
echo -e "${YELLOW}Step 2: Checking pip...${NC}"
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Error: pip3 is not installed${NC}"
    echo "Installing pip3..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    rm get-pip.py
fi
echo -e "${GREEN}✓ pip3 is available${NC}"
echo ""

# ============================================================================
# Step 3: Upgrade pip
# ============================================================================
echo -e "${YELLOW}Step 3: Upgrading pip...${NC}"
pip3 install --upgrade pip
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# ============================================================================
# Step 4: Install Python dependencies
# ============================================================================
echo -e "${YELLOW}Step 4: Installing Python dependencies...${NC}"
cd "$BACKEND_DIR"

if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: requirements.txt not found in $BACKEND_DIR${NC}"
    exit 1
fi

echo "Installing from requirements.txt..."
pip3 install -r requirements.txt

echo -e "${GREEN}✓ All Python dependencies installed${NC}"
echo ""

# ============================================================================
# Step 5: Create necessary directories
# ============================================================================
echo -e "${YELLOW}Step 5: Creating necessary directories...${NC}"
mkdir -p "$BACKEND_DIR/data/downloads"
mkdir -p "$BACKEND_DIR/data/exports"
mkdir -p "$BACKEND_DIR/logs"
mkdir -p "$BACKEND_DIR/config"
mkdir -p "$BACKEND_DIR/backups"

echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# ============================================================================
# Step 6: Set up environment file
# ============================================================================
echo -e "${YELLOW}Step 6: Setting up environment file...${NC}"
if [ ! -f "$BACKEND_DIR/.env" ]; then
    if [ -f "$BACKEND_DIR/.env.example" ]; then
        cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
        echo -e "${GREEN}✓ Created .env from .env.example${NC}"
        echo -e "${YELLOW}⚠ Please edit .env file with your configuration${NC}"
    else
        echo -e "${YELLOW}⚠ No .env.example found, skipping${NC}"
    fi
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi
echo ""

# ============================================================================
# Step 7: Test daily data collector
# ============================================================================
echo -e "${YELLOW}Step 7: Testing daily data collector...${NC}"
cd "$BACKEND_DIR"

if [ ! -f "daily_data_collector.py" ]; then
    echo -e "${RED}Error: daily_data_collector.py not found${NC}"
    exit 1
fi

echo "Running test collection (this may take a minute)..."
if python3 daily_data_collector.py --currency BTC --test; then
    echo -e "${GREEN}✓ Data collector test successful${NC}"
else
    echo -e "${YELLOW}⚠ Data collector test failed, but continuing...${NC}"
fi
echo ""

# ============================================================================
# Step 8: Set up cron job (optional)
# ============================================================================
echo -e "${YELLOW}Step 8: Cron job setup${NC}"
read -p "Do you want to set up automatic daily data collection? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "$BACKEND_DIR/setup_daily_collection.sh" ]; then
        chmod +x "$BACKEND_DIR/setup_daily_collection.sh"
        bash "$BACKEND_DIR/setup_daily_collection.sh"
    else
        echo -e "${RED}Error: setup_daily_collection.sh not found${NC}"
    fi
else
    echo "Skipping cron job setup"
    echo "You can set it up later by running: ./backend/setup_daily_collection.sh"
fi
echo ""

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "What was installed:"
echo "  ✓ Python dependencies from requirements.txt"
echo "  ✓ Directory structure created"
echo "  ✓ Environment file configured"
echo "  ✓ Data collector tested"
echo ""
echo "Next steps:"
echo "  1. Edit backend/.env with your configuration"
echo "  2. Test the data collector manually:"
echo "     cd $BACKEND_DIR"
echo "     python3 daily_data_collector.py --currency BTC"
echo ""
echo "  3. Start the backend API:"
echo "     cd $BACKEND_DIR"
echo "     python3 run_api.py"
echo ""
echo "  4. View collected data:"
echo "     ls -lh $BACKEND_DIR/data/"
echo ""
echo "For more information, see:"
echo "  - backend/DAILY_COLLECTION_GUIDE.md"
echo "  - deploy/COLLECTOR_DEPLOYMENT.md"
echo ""
