# Bitcoin Trading System - Deployment Guide

## 🚀 Quick Start

### Prerequisites

- Docker (version 20.0 or higher)
- Docker Compose (version 2.0 or higher)
- 4GB+ RAM available
- 10GB+ disk space

### One-Click Deployment

```bash
# Clone the repository
git clone <repository-url>
cd bitcoin-trading-system

# Run deployment script
./deploy.sh
```

The system will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Databases     │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   PostgreSQL    │
│   Port: 3000    │    │   Port: 8000    │    │   InfluxDB      │
└─────────────────┘    └─────────────────┘    │   Redis         │
                                              └─────────────────┘
```

## 📊 Features

### ✅ Implemented Features

1. **Real-time Market Data**
   - Live BTC price from Binance API
   - Historical K-line data
   - Order book data
   - 30-second data caching

2. **Trading Interface**
   - Manual trading controls
   - Order history
   - Auto-trading toggle (demo mode)
   - Portfolio management

3. **Analysis Tools**
   - Price charts with real data
   - Technical indicators visualization
   - Sentiment analysis display
   - Market analysis dashboard

4. **Backtesting System**
   - Historical strategy testing
   - Performance metrics calculation
   - Equity curve visualization
   - Risk metrics (Sharpe ratio, max drawdown)

5. **System Monitoring**
   - Real-time health monitoring
   - Performance metrics
   - System alerts
   - Resource usage tracking

6. **Security Features**
   - API key encryption
   - Configuration management
   - Access control
   - Error handling

## 🔧 Configuration

### Environment Variables

Edit `backend/.env` with your configuration:

```env
# API Keys (Required for full functionality)
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
OPENAI_API_KEY=your_openai_api_key

# Trading Parameters
INITIAL_CAPITAL=10000.0
MAX_POSITION_SIZE=0.1
STOP_LOSS_PERCENTAGE=0.05
TAKE_PROFIT_PERCENTAGE=0.15

# Database URLs (Auto-configured for Docker)
DATABASE_URL=postgresql://trading_user:secure_password_123@postgres:5432/bitcoin_trading
REDIS_URL=redis://redis:6379/0
```

### Trading Configuration

The system supports various trading strategies and risk parameters:

- **Position Sizing**: 1-20% of portfolio
- **Stop Loss**: 1-10% per trade
- **Take Profit**: 5-50% per trade
- **Risk Management**: Automated position sizing
- **Market Conditions**: Volatility and volume filters

## 🔍 Monitoring & Maintenance

### Health Checks

```bash
# Check all services
docker-compose ps

# Check specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Check system health via API
curl http://localhost:8000/api/v1/system/monitoring/health
```

### Performance Monitoring

The system provides real-time monitoring through:

1. **System Health Dashboard** (`/monitoring`)
   - CPU, Memory, Disk usage
   - API response times
   - Error rates
   - Database connections

2. **Trading Metrics**
   - Market data updates
   - Cache hit rates
   - API call counts
   - Trading performance

3. **Alerts System**
   - Automatic issue detection
   - Performance threshold alerts
   - System component status

### Backup & Recovery

```bash
# Backup database
docker-compose exec postgres pg_dump -U trading_user bitcoin_trading > backup.sql

# Backup configuration
cp backend/.env backup_env

# Restore database
docker-compose exec -T postgres psql -U trading_user bitcoin_trading < backup.sql
```

## 🚨 Important Security Notes

### ⚠️ Demo System Warning

**This is a demonstration system. DO NOT use with real trading funds.**

- Auto-trading is simulated only
- No real orders are placed
- Market data is real, but trading is mock
- Use paper trading accounts only

### Security Best Practices

1. **API Keys**: Store securely, never commit to version control
2. **Network**: Use HTTPS in production
3. **Database**: Change default passwords
4. **Access**: Implement proper authentication
5. **Monitoring**: Enable logging and alerts

## 🛠️ Development

### Local Development Setup

```bash
# Backend development
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python simple_real_market_api.py

# Frontend development
cd frontend
npm install
npm start
```

### Testing

```bash
# Run backend tests
cd backend
python -m pytest tests/

# Run frontend tests
cd frontend
npm test
```

### API Documentation

- **Interactive API Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 📈 Usage Examples

### 1. Running a Backtest

```bash
curl -X POST "http://localhost:8000/api/v1/backtesting/run" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "days": 30,
    "initial_capital": 10000,
    "strategy_name": "Moving Average Strategy"
  }'
```

### 2. Getting Market Data

```bash
# Current price
curl "http://localhost:8000/api/v1/trading/market-data/BTCUSDT"

# Historical K-lines
curl "http://localhost:8000/api/v1/trading/market-data/BTCUSDT/klines?interval=1h&limit=24"
```

### 3. System Monitoring

```bash
# System health
curl "http://localhost:8000/api/v1/system/monitoring/health"

# Performance metrics
curl "http://localhost:8000/api/v1/system/monitoring/metrics"
```

## 🔧 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Change ports in docker-compose.yml
   ports:
     - "3001:3000"  # Frontend
     - "8001:8000"  # Backend
   ```

2. **Database Connection Issues**
   ```bash
   # Reset database
   docker-compose down -v
   docker-compose up -d postgres
   ```

3. **API Key Issues**
   ```bash
   # Check environment variables
   docker-compose exec backend env | grep API
   ```

4. **Memory Issues**
   ```bash
   # Increase Docker memory limit
   # Docker Desktop > Settings > Resources > Memory
   ```

### Log Analysis

```bash
# View all logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f backend

# Search logs for errors
docker-compose logs | grep ERROR
```

## 📞 Support

For issues and questions:

1. Check the logs: `docker-compose logs`
2. Verify configuration: `backend/.env`
3. Test API endpoints: http://localhost:8000/docs
4. Monitor system health: http://localhost:3000/monitoring

## 🎯 Next Steps

To extend the system:

1. **Real Trading**: Integrate with live trading APIs
2. **Advanced Strategies**: Implement ML-based strategies
3. **Multi-Asset**: Support multiple cryptocurrencies
4. **Notifications**: Add email/SMS alerts
5. **Mobile App**: Create mobile interface
6. **Cloud Deployment**: Deploy to AWS/GCP/Azure

---

**Remember**: This is a demonstration system. Always test thoroughly before any real trading implementation.