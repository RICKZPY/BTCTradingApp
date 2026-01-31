# Bitcoin Trading System Backend

Event-driven Bitcoin trading system with AI-powered sentiment analysis and technical indicators.

## Features

- Multi-source data collection (Web3 news, Twitter, economic data)
- AI-powered sentiment analysis using OpenAI GPT-4
- Technical indicator calculations (RSI, MACD, Bollinger Bands)
- Automated trading via Binance API
- Risk management and portfolio tracking
- Real-time data processing with Celery
- Time series data storage with InfluxDB
- Caching and message queue with Redis

## Architecture

- **FastAPI**: High-performance web framework
- **PostgreSQL**: Primary database for trading records and configuration
- **InfluxDB**: Time series database for market data and indicators
- **Redis**: Caching and message queue
- **Celery**: Distributed task processing
- **SQLAlchemy**: ORM for database operations

## Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+
- InfluxDB 2.7+
- Redis 7+

### Installation

1. Clone the repository and navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment configuration:
```bash
cp .env.example .env
```

5. Update `.env` file with your API keys and database credentials.

### Database Setup

1. Start databases with Docker Compose:
```bash
docker-compose up postgres influxdb redis -d
```

2. Initialize database migrations:
```bash
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### Running the Application

1. Start the FastAPI server:
```bash
uvicorn main:app --reload
```

2. Start Celery worker (in another terminal):
```bash
celery -A celery_app worker --loglevel=info
```

3. Start Celery beat scheduler (in another terminal):
```bash
celery -A celery_app beat --loglevel=info
```

### Using Docker

Run the entire stack with Docker Compose:
```bash
docker-compose up
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

## Configuration

Key configuration options in `.env`:

### Database
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `INFLUXDB_URL`, `INFLUXDB_TOKEN`, `INFLUXDB_ORG`, `INFLUXDB_BUCKET`
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`

### API Keys
- `OPENAI_API_KEY` - OpenAI API for sentiment analysis
- `BINANCE_API_KEY`, `BINANCE_SECRET_KEY` - Binance trading API
- `TWITTER_BEARER_TOKEN` - Twitter API for social sentiment
- `NEWSAPI_KEY` - News API for data collection

### Trading Parameters
- `MAX_POSITION_SIZE` - Maximum position size (default: 0.1 = 10%)
- `MAX_DAILY_LOSS` - Maximum daily loss limit (default: 0.05 = 5%)
- `STOP_LOSS_PERCENTAGE` - Stop loss percentage (default: 0.02 = 2%)
- `MIN_CONFIDENCE_THRESHOLD` - Minimum confidence for trades (default: 0.7)

## Development

### Code Style
```bash
black .
flake8 .
mypy .
```

### Testing
```bash
pytest
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Monitoring

- Application logs are structured JSON format
- Health check endpoint at `/health`
- Celery monitoring with Flower (optional)
- Database metrics via InfluxDB

## Security

- API keys encrypted in database
- Rate limiting on external API calls
- Input validation with Pydantic
- SQL injection protection with SQLAlchemy ORM

## License

MIT License