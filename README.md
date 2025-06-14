# PRISMY Ultimate - Translation Service

A powerful async translation service combining PRISMY Clean architecture with Celery queue processing.

## Features

- 🚀 Async processing with Celery & Redis
- 📄 PDF and text file translation
- 🌐 Multiple translation tiers (Basic, Standard, Premium)
- 📊 Job tracking and monitoring
- 🔄 RESTful API with FastAPI
- 📈 Flower dashboard for queue monitoring

## Quick Start

### Prerequisites

- Python 3.11+
- Redis
- Virtual environment

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd prismy-ultimate

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Service

```bash
# Start all services
python start_services.py

# Stop all services
python stop_services.py
```

Services will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Flower Monitor: http://localhost:5555

## API Endpoints

### Translation

#### Async Text Translation
```bash
POST /api/v2/translate/text/async
Content-Type: application/x-www-form-urlencoded

Parameters:
- text: string (required) - Text to translate
- target_language: string (required) - Target language code (e.g., 'vi', 'es', 'fr')
- tier: string (optional) - Translation tier: 'basic', 'standard', 'premium' (default: 'basic')

Response:
{
  "job_id": "uuid",
  "status": "processing",
  "message": "Translation job submitted successfully"
}
```

#### Async PDF Translation
```bash
POST /api/v2/translate/pdf/async
Content-Type: multipart/form-data

Parameters:
- file: file (required) - PDF file to translate
- target_language: string (required) - Target language code
- tier: string (optional) - Translation tier (default: 'basic')

Response:
{
  "job_id": "uuid",
  "status": "processing",
  "message": "Translation job submitted successfully"
}
```

### Job Management

#### Check Job Status
```bash
GET /api/v2/translate/job/{job_id}

Response:
{
  "id": "uuid",
  "status": "completed|processing|failed",
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "output_file": "path/to/file",
  "download_url": "/api/v2/translate/job/{job_id}/download"
}
```

#### Download Result
```bash
GET /api/v2/translate/job/{job_id}/download

Returns: Translated file
```

#### List All Jobs
```bash
GET /api/v2/translate/jobs
Optional query parameter: ?status=completed|processing|failed

Response:
{
  "total": 10,
  "jobs": [...]
}
```

## Project Structure

```
prismy-ultimate/
├── src/
│   ├── api/              # FastAPI endpoints
│   ├── celery_tasks/     # Celery task definitions
│   ├── processors/       # Document processors
│   ├── services/         # Business logic
│   └── workers/          # Background workers
├── storage/              # File storage
├── logs/                 # Application logs
├── celery_app.py         # Celery configuration
├── start_services.py     # Start script
└── requirements.txt      # Dependencies
```

## Configuration

### Environment Variables

Create a `.env` file:

```env
# Redis
REDIS_URL=redis://localhost:6379/0

# Translation APIs (when implemented)
GOOGLE_TRANSLATE_API_KEY=your_key
OPENAI_API_KEY=your_key
DEEPL_API_KEY=your_key

# Storage
STORAGE_PATH=./storage
```

## Development

### Running Tests
```bash
pytest tests/
```

### Adding New Translation Providers

1. Create provider in `src/providers/`
2. Register in translation worker
3. Update tier mappings

## Deployment

### Docker

```bash
docker-compose up -d
```

### Production

- Use environment variables for configuration
- Set up proper Redis persistence
- Configure reverse proxy (nginx)
- Enable SSL/TLS
- Set up monitoring and alerts

## License

MIT License

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request# Last updated: Sat Jun 14 12:48:15 +07 2025
