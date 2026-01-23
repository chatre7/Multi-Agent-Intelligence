# Docker Setup Guide - Multi-Agent Intelligence Platform

## 🐳 Quick Start with Docker

### Prerequisites
- Docker Desktop installed and running
- Docker Compose v2.0+
- At least 8GB RAM available for Docker

### Step 1: Clone and Setup
```bash
cd Multi-Agent-Intelligence
```

### Step 2: (Optional) Configure Environment
```bash
cp .env.example .env
# Edit .env if needed
```

### Step 3: Build and Start All Services
```bash
docker-compose up --build
```

Or run in detached mode:
```bash
docker-compose up -d --build
```

### Step 4: Pull Ollama Models
After all services are running, pull the required LLM models:

```bash
# Pull the models (one-time setup)
docker-compose exec ollama ollama pull gpt-oss:120b-cloud
docker-compose exec ollama ollama pull nomic-embed-text
```

### Step 5: Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Ollama**: http://localhost:11434

### Default Login Credentials
- **Admin**: `admin:admin`
- **Developer**: `dev:dev`
- **User**: `user:user`

---

## 📋 Available Commands

### Start Services
```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Build and start
docker-compose up --build
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ DELETES DATA)
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f ollama
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Execute Commands in Containers
```bash
# Backend shell
docker-compose exec backend bash

# Run backend tests
docker-compose exec backend pytest tests/unit -v

# Frontend shell
docker-compose exec frontend sh

# Ollama commands
docker-compose exec ollama ollama list
```

---

## 🔧 Service Details

### Ollama Service
- **Port**: 11434
- **Volume**: `ollama_data` (persists downloaded models)
- **Image**: `ollama/ollama:latest`
- **Health Check**: Checks API tags endpoint every 30s

### Backend Service
- **Port**: 8000
- **Framework**: FastAPI + Python 3.11
- **Volumes**:
  - `./backend` → `/app` (source code)
  - `backend_data` → `/app/data` (database)
  - `backend_logs` → `/app/logs` (logs)
- **Dependencies**: Ollama service must be healthy
- **Auto-reload**: Enabled for development

### Frontend Service
- **Port**: 5173
- **Framework**: React 19 + Vite 5
- **Volume**: `./frontend` → `/app` (source code with node_modules excluded)
- **Dependencies**: Backend service must be healthy
- **Hot Reload**: Enabled for development

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :5173
netstat -ano | findstr :11434

# Stop the container and change port in docker-compose.yml if needed
```

### Services Not Starting
```bash
# Check service status
docker-compose ps

# Check logs for errors
docker-compose logs

# Rebuild without cache
docker-compose build --no-cache
docker-compose up
```

### Ollama Model Downloaded but Not Found
```bash
# List downloaded models
docker-compose exec ollama ollama list

# Download again if needed
docker-compose exec ollama ollama pull gpt-oss:120b-cloud
```

### Backend Database Locked
```bash
# Remove the database volume (⚠️ DELETES DATA)
docker-compose down
docker volume rm multi-agent-intelligence_backend_data
docker-compose up
```

### Frontend Can't Connect to Backend
1. Check backend is running: `docker-compose ps`
2. Verify backend health: `curl http://localhost:8000/health`
3. Check CORS settings in backend
4. Verify `VITE_API_BASE_URL` in frontend environment

### Out of Disk Space
```bash
# Clean up unused Docker resources
docker system prune -a

# Remove unused volumes
docker volume prune
```

---

## 📦 Data Persistence

Docker volumes are used to persist data across container restarts:

- **ollama_data**: Downloaded LLM models (~5-10GB per model)
- **backend_data**: SQLite database (checkpoints.db)
- **backend_logs**: Application logs

To backup your data:
```bash
# Backup database
docker-compose exec backend cp /app/data/checkpoints.db /app/data/backup.db
docker cp mai-backend:/app/data/backup.db ./backup.db

# View volume location
docker volume inspect multi-agent-intelligence_backend_data
```

---

## 🚀 Production Deployment

For production deployment, create a separate `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - LOG_LEVEL=WARNING
      - JWT_SECRET=${JWT_SECRET}
    command: gunicorn src.presentation.api.app:create_app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    command: npx serve -s dist -l 5173
```

Run with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 📊 Monitoring

### Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Ollama health
curl http://localhost:11434/api/tags

# Docker health status
docker-compose ps
```

### Resource Usage
```bash
# View resource usage
docker stats

# Specific container
docker stats mai-backend
```

### Logs
```bash
# Stream all logs
docker-compose logs -f --tail=100

# Filter by service
docker-compose logs -f backend --tail=50
```

---

## 🔒 Security Notes

1. **Change Default Credentials**: Update demo user credentials before production
2. **Environment Variables**: Never commit `.env` file with secrets
3. **JWT Secret**: Set a strong JWT_SECRET in production
4. **Network Isolation**: Services communicate via internal Docker network
5. **Volume Permissions**: Backend data is isolated in Docker volumes

---

## ⚙️ Configuration

### Changing Ports

Edit `docker-compose.yml`:
```yaml
services:
  backend:
    ports:
      - "8080:8000"  # Change host port to 8080
```

### Adding Environment Variables

Edit `.env` file or add to `docker-compose.yml`:
```yaml
services:
  backend:
    environment:
      - NEW_VAR=value
```

### Using Different LLM Models

```bash
# Pull different model
docker-compose exec ollama ollama pull llama2

# List available models
docker-compose exec ollama ollama list
```

---

## 📝 Next Steps

1. ✅ Start all services with `docker-compose up -d`
2. ✅ Pull Ollama models
3. ✅ Access frontend at http://localhost:5173
4. ✅ Login with demo credentials
5. ✅ Start chatting with agents!

For detailed feature documentation, see [QUICKSTART.md](./QUICKSTART.md)

---

**Last Updated**: January 22, 2026
