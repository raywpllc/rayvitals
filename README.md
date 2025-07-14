# RavVitals - Website Audit Platform

A comprehensive website audit platform that provides security, performance, and business intelligence analysis for websites.

## Features

- **Security Analysis**: SSL certificate validation, security headers assessment, and vulnerability scanning
- **Performance Testing**: Load time measurement, HTTP response analysis, and performance optimization recommendations
- **AI Business Intelligence**: Google Gemini-powered analysis with comprehensive website insights
- **Async Processing**: Background task architecture for handling large-scale audits
- **RESTful API**: FastAPI-based backend with comprehensive endpoint documentation

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Redis (for background tasks)
- PostgreSQL (via Supabase)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd RavVitals
   ```

2. **Set up Python environment**
   ```bash
   cd rayvitals-backend
   python -m venv rayvitals-env
   source rayvitals-env/bin/activate  # On Windows: rayvitals-env\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database configuration
   ```

4. **Run with Docker**
   ```bash
   docker-compose up --build
   ```

5. **Run locally**
   ```bash
   cd rayvitals-backend
   python main.py
   ```

### API Documentation

Once running, access the interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Testing Interface

A simple web interface for testing is available at:
- **Test Interface**: `rayvitals-backend/test_interface.html`

## API Endpoints

### Core Endpoints

- `POST /api/v1/audit/start` - Start a new website audit
- `GET /api/v1/audit/status/{audit_id}` - Get audit status and results
- `GET /api/v1/health` - Health check endpoint

### Example Usage

```bash
# Start an audit
curl -X POST "http://localhost:8000/api/v1/audit/start" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Check audit status
curl "http://localhost:8000/api/v1/audit/status/{audit_id}"
```

## Architecture

### Backend Structure

```
rayvitals-backend/
├── app/
│   ├── api/v1/              # API endpoints
│   ├── core/                # Core configuration
│   ├── models/              # Database models
│   ├── services/            # Business logic
│   ├── tasks/               # Background tasks
│   └── utils/               # Utilities
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
└── tests/                   # Test suite
```

### Key Components

- **FastAPI**: Modern, fast web framework for building APIs
- **Supabase**: PostgreSQL database with real-time capabilities
- **Celery**: Distributed task queue for background processing
- **Redis**: In-memory data store for caching and task queue
- **Google Gemini**: AI integration for business intelligence analysis

## Development

### Running Tests

```bash
cd rayvitals-backend
python -m pytest tests/ -v
```

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

## Deployment

### Docker Deployment

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

Required environment variables:
- `DATABASE_URL`: Supabase database connection string
- `REDIS_URL`: Redis connection string
- `GOOGLE_API_KEY`: Google Gemini API key
- `SECRET_KEY`: Application secret key

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure code quality
5. Submit a pull request

## License

This project is licensed under the MIT License.