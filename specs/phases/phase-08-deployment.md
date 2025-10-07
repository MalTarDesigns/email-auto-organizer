# Phase 8: Deployment & Production

**Timeline**: Week 8

## Objectives

- Setup production environment configuration
- Configure production Docker setup
- Implement monitoring and logging
- Setup CI/CD pipeline
- Configure domain and SSL
- Implement backup and disaster recovery

## 8.1 Environment Configuration

### Production Environment Variables

```bash
# .env.production

# Database
DATABASE_URL=postgresql://user:password@db-host:5432/email_triage
POSTGRES_DB=email_triage
POSTGRES_USER=production_user
POSTGRES_PASSWORD=secure_password_here

# Redis
REDIS_URL=redis://redis-host:6379

# OpenAI
OPENAI_API_KEY=sk-prod-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Gmail OAuth
GOOGLE_CLIENT_ID=your-production-client-id
GOOGLE_CLIENT_SECRET=your-production-client-secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/callback

# Security
SECRET_KEY=your-super-secret-production-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# App Configuration
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://api.yourdomain.com
ENVIRONMENT=production

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO
```

## 8.2 Production Docker Configuration

### Docker Compose Production

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    restart: always
    networks:
      - app-network
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - postgres
      - redis
    restart: always
    networks:
      - app-network

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=2
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
    restart: always
    networks:
      - app-network

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.workers.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
    restart: always
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - static_files:/var/www/static
    depends_on:
      - backend
    restart: always
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:
  static_files:

networks:
  app-network:
    driver: bridge
```

### Production Dockerfile

```dockerfile
# backend/Dockerfile.prod
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
```

## 8.3 Nginx Configuration

### Reverse Proxy Setup

```nginx
# nginx/nginx.conf
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    client_max_body_size 10M;

    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location / {
        root /var/www/static;
        try_files $uri $uri/ /index.html;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;
}
```

## 8.4 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push backend
        run: |
          docker build -t yourusername/email-triage-backend:latest -f backend/Dockerfile.prod backend/
          docker push yourusername/email-triage-backend:latest

      - name: Build and push frontend
        run: |
          docker build -t yourusername/email-triage-frontend:latest frontend/
          docker push yourusername/email-triage-frontend:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.PRODUCTION_HOST }}
          username: ${{ secrets.PRODUCTION_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /app/email-auto-organizer
            git pull origin main
            docker-compose -f docker-compose.production.yml pull
            docker-compose -f docker-compose.production.yml up -d
            docker system prune -f
```

## 8.5 Monitoring and Logging

### Application Monitoring

```python
# backend/app/core/monitoring.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from app.core.config import settings

def setup_monitoring():
    """Initialize application monitoring"""
    if settings.ENVIRONMENT == 'production':
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,
            environment=settings.ENVIRONMENT
        )
```

### Logging Configuration

```python
# backend/app/core/logging_config.py
import logging
from logging.handlers import RotatingFileHandler
from app.core.config import settings

def setup_logging():
    """Configure application logging"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))

    # File handler
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(log_format))

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
```

### Health Check Endpoint

```python
# backend/app/api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from redis import Redis
from app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for monitoring"""
    health_status = {
        'status': 'healthy',
        'database': 'unknown',
        'redis': 'unknown'
    }

    # Check database
    try:
        db.execute('SELECT 1')
        health_status['database'] = 'healthy'
    except Exception as e:
        health_status['database'] = 'unhealthy'
        health_status['status'] = 'degraded'

    # Check Redis
    try:
        redis_client = Redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        health_status['redis'] = 'healthy'
    except Exception as e:
        health_status['redis'] = 'unhealthy'
        health_status['status'] = 'degraded'

    return health_status
```

## 8.6 Backup Strategy

### Database Backup Script

```bash
#!/bin/bash
# scripts/backup.sh

# Configuration
BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
docker exec postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > $BACKUP_FILE

# Upload to S3 (optional)
aws s3 cp $BACKUP_FILE s3://your-backup-bucket/postgres/

# Remove old backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_FILE"
```

### Automated Backup Cron Job

```cron
# Run daily backup at 2 AM
0 2 * * * /app/scripts/backup.sh >> /var/log/backup.log 2>&1
```

## 8.7 SSL Certificate Setup

### Let's Encrypt with Certbot

```bash
# scripts/setup-ssl.sh
#!/bin/bash

# Install certbot
apt-get update
apt-get install -y certbot

# Obtain certificate
certbot certonly --webroot \
  -w /var/www/certbot \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email

# Copy certificates to nginx directory
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /path/to/nginx/ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /path/to/nginx/ssl/

# Restart nginx
docker-compose -f docker-compose.production.yml restart nginx
```

### Auto-Renewal Cron

```cron
# Renew SSL certificate monthly
0 0 1 * * certbot renew --quiet && docker-compose -f /app/email-auto-organizer/docker-compose.production.yml restart nginx
```

## Deliverables

- ✅ Production environment configuration
- ✅ Production Docker setup with optimization
- ✅ Nginx reverse proxy configuration
- ✅ SSL/TLS certificate setup
- ✅ CI/CD pipeline implementation
- ✅ Monitoring and logging setup
- ✅ Health check endpoints
- ✅ Automated backup system
- ✅ Deployment documentation

## Success Criteria

- Application accessible via HTTPS
- Automated deployments working
- Monitoring alerts configured
- Database backups running daily
- Health checks reporting correctly
- Zero-downtime deployments
- SSL certificate auto-renewal
- All services restart automatically on failure
- 99.9% uptime SLA achieved
