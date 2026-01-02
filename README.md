# Company Management API

Professional FastAPI application for company and task management.

## Project Structure

```
company-management-production/
├── app/                    # Application code
│   ├── api/               # API routes and handlers
│   ├── core/              # Core functionality and config
│   ├── models/            # Data models
│   ├── services/          # External services (Firebase)
│   └── main.py           # FastAPI app instance
├── config/                # Configuration files
│   ├── .env              # Environment variables
│   └── firebase-key.json # Firebase credentials
├── tests/                 # Test suites
│   └── unit/             # Unit tests (Python)
├── docs/                  # Documentation
├── scripts/               # Utility scripts
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
└── Dockerfile           # Container configuration
```

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment: Update `config/.env`
3. Run application: `python main.py`
4. Run tests: `pytest tests/unit/`

## API Documentation

Visit `/docs` when running for interactive API documentation.