# Railway Procfile for ThreatWatch
# Defines processes to run on Railway deployment

# Web process - FastAPI server
web: cd backend && gunicorn server:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001 --timeout 120

# Celery worker - Processes background tasks
worker: cd backend && celery -A celery_app worker --loglevel=info --concurrency=2

# Celery beat - Schedules periodic tasks
beat: cd backend && celery -A celery_app beat --loglevel=info
