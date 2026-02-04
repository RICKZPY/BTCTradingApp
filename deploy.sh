#!/bin/bash

# Bitcoin Trading System Deployment Script
# This script sets up and deploys the complete trading system

set -e

echo "🚀 Starting Bitcoin Trading System Deployment..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/influxdb
mkdir -p data/redis

# Set permissions
chmod 755 logs
chmod 755 data

# Copy environment files if they don't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend environment file..."
    cat > backend/.env << EOF
# Environment Configuration
ENVIRONMENT=production
DEBUG=false

# Database Configuration
DATABASE_URL=postgresql://trading_user:secure_password_123@postgres:5432/bitcoin_trading
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your_influxdb_token_here
INFLUXDB_ORG=bitcoin_trading
INFLUXDB_BUCKET=market_data

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# API Keys (Replace with your actual keys)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Security
SECRET_KEY=your_very_secure_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here

# Trading Configuration
INITIAL_CAPITAL=10000.0
MAX_POSITION_SIZE=0.1
STOP_LOSS_PERCENTAGE=0.05
TAKE_PROFIT_PERCENTAGE=0.15
EOF
    echo "⚠️  Please edit backend/.env with your actual API keys and configuration"
fi

# Build and start services
echo "🔨 Building and starting services..."
docker-compose down --remove-orphans
docker-compose build --no-cache
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check backend health
if curl -f http://localhost:8000/api/v1/health/ > /dev/null 2>&1; then
    echo "✅ Backend service is healthy"
else
    echo "❌ Backend service is not responding"
    docker-compose logs backend
fi

# Check frontend
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend service is healthy"
else
    echo "❌ Frontend service is not responding"
    docker-compose logs frontend
fi

# Check database connections
echo "🔍 Checking database connections..."
if docker-compose exec -T postgres pg_isready -U trading_user -d bitcoin_trading > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📊 Access your Bitcoin Trading System:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""
echo "🔧 Management Commands:"
echo "   View logs: docker-compose logs -f [service_name]"
echo "   Stop system: docker-compose down"
echo "   Restart system: docker-compose restart"
echo "   Update system: ./deploy.sh"
echo ""
echo "⚠️  Important Notes:"
echo "   1. Edit backend/.env with your actual API keys"
echo "   2. This is a demo system - do not use with real trading funds"
echo "   3. Monitor the system logs for any issues"
echo ""