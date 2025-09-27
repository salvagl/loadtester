# LoadTester Deployment Guide

## Overview

LoadTester is designed to run in a containerized environment using Docker Compose. This guide covers local deployment, production considerations, and troubleshooting.

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows 10+ with WSL2
- **CPU**: Intel Core i7 8th gen or equivalent (minimum requirement)
- **RAM**: 16GB (as specified in requirements)
- **Disk Space**: 10GB free space minimum
- **Network**: Internet access for downloading dependencies and AI services

### Required Software

1. **Docker** (version 20.10+)
   ```bash
   # Install Docker (Ubuntu/Debian)
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Add user to docker group
   sudo usermod -aG docker $USER
   ```

2. **Docker Compose** (version 2.0+)
   ```bash
   # Usually included with Docker Desktop
   # Or install separately
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **UV Package Manager** (for development)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

---

## Quick Start Deployment

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd loadtester

# Create required directories
mkdir -p shared/{database,data/uploads,data/mocked,reports/generated}
mkdir -p k6/{scripts/generated,results/generated}

# Create .gitkeep files for empty directories
touch shared/database/.gitkeep
touch shared/data/uploads/.gitkeep
touch shared/data/mocked/.gitkeep
touch shared/reports/generated/.gitkeep
touch k6/scripts/generated/.gitkeep
touch k6/results/generated/.gitkeep
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (REQUIRED)
nano .env
```

**Minimum required configuration:**
```bash
# Add at least one AI service API key
GOOGLE_API_KEY=your_google_gemini_api_key_here
# OR
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# OR  
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Deploy

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up --build -d
```

### 4. Verify Deployment

```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health

# View logs
docker-compose logs -f
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "LoadTester", 
  "version": "0.0.1"
}
```

---

## Service Configuration

### Backend Configuration

The backend service can be configured through environment variables in `.env`:

```bash
# Application Settings
APP_NAME=LoadTester
APP_VERSION=0.0.1
LOG_LEVEL=INFO
DEBUG=false

# Load Testing Configuration
DEGRADATION_RESPONSE_TIME_MULTIPLIER=5.0
DEGRADATION_ERROR_RATE_THRESHOLD=0.5
DEFAULT_TEST_DURATION=60
MAX_CONCURRENT_JOBS=1
INITIAL_USER_PERCENTAGE=0.1
USER_INCREMENT_PERCENTAGE=0.5
STOP_ERROR_THRESHOLD=0.6

# File Upload Configuration
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_FILE_EXTENSIONS=.csv,.json,.xlsx

# Security (change in production)
SECRET_KEY=your-secret-key-change-this-in-production
```

### Frontend Configuration

```bash
# Frontend Settings
BACKEND_URL=http://backend:8000
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Database Configuration

```bash
# SQLite Database
DATABASE_URL=sqlite:///data/loadtester.db
```

---

## AI Services Setup

LoadTester requires at least one AI service to function. Configure the appropriate API keys:

### Google Gemini (Recommended - Free Tier Available)

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to `.env`:
   ```bash
   GOOGLE_API_KEY=your_google_api_key_here
   ```

### Anthropic Claude

1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Create an API key
3. Add to `.env`:
   ```bash
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

### OpenAI GPT

1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create an API key
3. Add to `.env`:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```

---

## Production Deployment

### Security Considerations

1. **Change Default Secrets**
   ```bash
   # Generate strong secret key
   SECRET_KEY=$(openssl rand -base64 32)
   ```

2. **Secure API Keys**
   - Store API keys in a secure secret management system
   - Use Docker secrets or Kubernetes secrets
   - Never commit API keys to version control

3. **Network Security**
   ```yaml
   # In docker-compose.yml, remove port mappings for internal services
   backend:
     # ports:
     #   - "8000:8000"  # Remove this in production
     expose:
       - "8000"
   ```

4. **HTTPS Setup**
   - Use a reverse proxy (nginx, traefik) with SSL certificates
   - Configure proper CORS settings
   - Enable security headers

### Resource Scaling

```yaml
# docker-compose.yml production settings
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
      restart_policy:
        condition: on-failure
        max_attempts: 3
```

### Production Environment Variables

```bash
# Production .env
DEBUG=false
LOG_LEVEL=WARNING

# Increase limits for production
MAX_CONCURRENT_JOBS=3
MAX_FILE_SIZE=52428800  # 50MB

# Performance tuning
WORKER_PROCESSES=4
WORKER_CONNECTIONS=2000
```

### Monitoring and Logging

```yaml
# Add logging driver
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## Docker Compose Services

### Service Overview

| Service | Port | Purpose | Dependencies |
|---------|------|---------|--------------|
| backend | 8000 | FastAPI backend | k6 |
| frontend | 8501 | Streamlit UI | backend |
| k6 | - | Load testing engine | - |

### Service Dependencies

```
frontend → backend → k6
```

### Volume Mounts

| Volume | Purpose | Persistence |
|--------|---------|-------------|
| `./shared/database` | SQLite database | Yes |
| `./shared/data` | Upload/mock data | Yes |
| `./shared/reports` | Generated PDFs | Yes |
| `./k6/scripts` | K6 test scripts | No |
| `./k6/results` | K6 test results | No |

---

## Database Management

### Backup

```bash
# Backup SQLite database
docker-compose exec backend cp /app/data/loadtester.db /app/data/backup_$(date +%Y%m%d_%H%M%S).db

# Copy backup to host
docker cp loadtester-backend:/app/data/backup_*.db ./backups/
```

### Restore

```bash
# Stop services
docker-compose down

# Restore database
cp ./backups/backup_20240115_103000.db ./shared/database/loadtester.db

# Start services
docker-compose up -d
```

### Migration

```bash
# Database migrations are automatic on startup
# Check migration status
docker-compose logs backend | grep -i migration
```

---

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

**Check logs:**
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

**Common causes:**
- Missing `.env` file
- Invalid API keys
- Port conflicts
- Insufficient disk space

#### 2. AI Services Not Working

**Verify API keys:**
```bash
# Test API key
curl -H "Authorization: Bearer $GOOGLE_API_KEY" \
  "https://generativelanguage.googleapis.com/v1beta/models"
```

**Check service logs:**
```bash
docker-compose logs backend | grep -i "ai\|error"
```

#### 3. K6 Execution Fails

**Check K6 container:**
```bash
docker-compose exec k6 k6 version
docker-compose logs k6
```

**Common solutions:**
- Ensure K6 container is running
- Check script generation in backend logs
- Verify network connectivity

#### 4. Database Issues

**Reset database:**
```bash
docker-compose down
rm ./shared/database/loadtester.db
docker-compose up -d
```

#### 5. Frontend Not Loading

**Check backend connection:**
```bash
curl http://localhost:8000/health
```

**Check frontend logs:**
```bash
docker-compose logs frontend
```

### Performance Issues

#### High Memory Usage

```bash
# Monitor container resources
docker stats

# Limit container memory
# Add to docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 2G
```

#### Slow Response Times

1. **Check AI service response times**
2. **Monitor database performance**
3. **Review K6 execution logs**
4. **Verify system resources**

### Debug Mode

```bash
# Enable debug mode
echo "DEBUG=true" >> .env
echo "LOG_LEVEL=DEBUG" >> .env

# Restart services
docker-compose restart backend
```

---

## Maintenance

### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### Cleanup

```bash
# Remove old containers and images
docker-compose down --rmi all --volumes --remove-orphans

# Clean up Docker system
docker system prune -af
```

### Log Rotation

```bash
# Clean up old logs
docker-compose logs --timestamps | head -1000 > logs_archive.txt
docker-compose restart
```

---

## Development Deployment

### Local Development Setup

```bash
# Install Python dependencies
cd backend
uv sync --dev

# Run backend in development mode
uv run uvicorn app.main:app --reload --port 8000

# In another terminal, run frontend
cd frontend
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

### Development Environment Variables

```bash
# Development .env
DEBUG=true
LOG_LEVEL=DEBUG
BACKEND_URL=http://localhost:8000
```

### Hot Reload

The development setup includes:
- FastAPI auto-reload on code changes
- Streamlit auto-reload on file changes
- Live log streaming

---

## Support

### Getting Help

1. **Check logs first:**
   ```bash
   docker-compose logs -f
   ```

2. **Verify configuration:**
   ```bash
   docker-compose config
   ```

3. **Health checks:**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8501/_stcore/health
   ```

### Report Issues

When reporting issues, please include:
- Operating system and version
- Docker and Docker Compose versions
- Complete error logs
- Steps to reproduce
- Configuration (without sensitive data)

### Useful Commands

```bash
# View all services status
docker-compose ps

# Follow logs for specific service
docker-compose logs -f backend

# Execute commands inside containers
docker-compose exec backend bash
docker-compose exec k6 sh

# View resource usage
docker stats

# Inspect networks
docker network ls
docker network inspect loadtester_loadtester-network
```