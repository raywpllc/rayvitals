# RayVitals Backend API

AI-powered website intelligence platform backend API built with FastAPI.

## Features

- **Website Security Analysis**: SSL, security headers, vulnerability scanning
- **Performance Testing**: Load times, Core Web Vitals, optimization recommendations
- **SEO Analysis**: Technical SEO, meta tags, structured data
- **AI Business Intelligence**: Gemini-powered analysis and recommendations
- **Async Processing**: Celery + Redis for background audit processing
- **Database**: Supabase (PostgreSQL) for data storage

## Quick Start

### Prerequisites

- Python 3.11+
- Redis server
- Supabase account (for database)
- Google Gemini API key (for AI analysis)

### Installation

1. Clone and setup:
```bash
cd rayvitals-backend
cp .env.example .env
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
DATABASE_URL=postgresql://user:password@db.your-project.supabase.co:5432/postgres

# Optional but recommended
GEMINI_API_KEY=your-gemini-api-key
PAGESPEED_API_KEY=your-pagespeed-api-key
```

3. Run locally:
```bash
# Start Redis
redis-server

# Start API
uvicorn app.main:app --reload

# Start Celery worker (separate terminal)
celery -A app.core.celery worker --loglevel=info
```

### Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up --build

# API will be available at http://localhost:8000
```

## API Usage

### Demo Audit (No Database Required)

```bash
curl -X POST "http://localhost:8000/api/v1/audit/demo" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Async Audit with Celery

```bash
# Start async audit
curl -X POST "http://localhost:8000/api/v1/audit/async" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Check task status (use task_id from response)
curl "http://localhost:8000/api/v1/audit/task/{task_id}"
```

### Database-backed Audit

```bash
# Start audit with database storage
curl -X POST "http://localhost:8000/api/v1/audit/start" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Check audit status
curl "http://localhost:8000/api/v1/audit/status/{audit_id}"

# Get audit results
curl "http://localhost:8000/api/v1/audit/results/{audit_id}"
```

### Health Check

```bash
curl "http://localhost:8000/health"
curl "http://localhost:8000/api/v1/health/detailed"
```

### Web Testing Interface

Visit `http://localhost:8000/test` for an interactive web interface to test all endpoints.

## Testing

```bash
# Run tests
pytest tests/

# Run specific test
pytest tests/test_basic.py -v
```

## API Documentation

When running with `DEBUG=True`, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Architecture

### Core Components

- **FastAPI**: Web framework and API endpoints
- **Supabase**: PostgreSQL database with real-time features
- **Redis**: Caching and message broker
- **Celery**: Background task processing
- **Google Gemini**: AI analysis and business intelligence

### Analysis Services

- **SecurityScanner**: SSL, headers, vulnerability analysis
- **PerformanceScanner**: Load times, optimization recommendations
- **AIAnalyzer**: Business intelligence and strategic insights

### Database Models

- **AuditRequest**: Main audit tracking
- **AuditResult**: Detailed category results
- **AuditMetrics**: Performance metrics
- **SiteRegistration**: WordPress site integration

## Development

### Project Structure

```
app/
├── main.py              # FastAPI application
├── core/
│   ├── config.py        # Settings and configuration
│   └── database.py      # Database connection
├── models/              # SQLAlchemy models
├── api/v1/              # API endpoints
├── services/            # Business logic
└── utils/               # Utilities
```

### Adding New Features

1. Create service in `app/services/`
2. Add database models in `app/models/`
3. Create API endpoints in `app/api/v1/endpoints/`
4. Update router in `app/api/v1/router.py`
5. Add tests in `tests/`

## Deployment

The API is designed for deployment on:
- **Digital Ocean**: App Platform or Droplets
- **Vultr**: Cloud Compute
- **Any VPS**: With Docker support

### Environment Variables

See `.env.example` for all configuration options.

## License

Private - RayVitals LLC