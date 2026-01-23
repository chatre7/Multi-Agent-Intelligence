# Docker Setup Summary

## 📦 Files Created

The following Docker-related files have been added to the project:

### Core Docker Files
✅ **docker-compose.yml** - Main orchestration file with 3 services (ollama, backend, frontend)
✅ **backend/Dockerfile** - Python 3.11 FastAPI backend container
✅ **frontend/Dockerfile** - Node 18 React + Vite frontend container
✅ **backend/.dockerignore** - Excludes Python cache and test files
✅ **frontend/.dockerignore** - Excludes node_modules and build files

### Configuration Files
✅ **.env.example** - Template for environment variables
✅ **.gitignore** - Updated to ignore Docker-generated files

### Helper Scripts & Documentation
✅ **docker.ps1** - PowerShell script for Windows users (recommended)
✅ **Makefile** - Unix-style shortcuts for Docker commands
✅ **README.docker.md** - Complete Docker setup guide (detailed)
✅ **DOCKER_QUICKSTART.md** - Quick reference guide (concise)
✅ **DOCKER_SETUP_SUMMARY.md** - This file

---

## 🚀 Quick Start Commands

### For Windows Users (Recommended)
```powershell
# Full setup (build + start + pull models)
.\docker.ps1 setup

# Or step by step
.\docker.ps1 build
.\docker.ps1 up
.\docker.ps1 pull-models
```

### For Linux/Mac Users
```bash
# Using Makefile
make setup

# Or using docker-compose directly
docker-compose up -d --build
docker-compose exec ollama ollama pull gpt-oss:120b-cloud
docker-compose exec ollama ollama pull nomic-embed-text
```

---

## 🐳 Services Architecture

```
┌─────────────────────────────────────────────┐
│  Frontend (React + Vite)                    │
│  Port: 5173                                 │
│  Volume: ./frontend → /app                  │
└─────────────────┬───────────────────────────┘
                  │
                  │ HTTP/WebSocket
                  ▼
┌─────────────────────────────────────────────┐
│  Backend (FastAPI + Python)                 │
│  Port: 8000                                 │
│  Volumes:                                   │
│    - ./backend → /app                       │
│    - backend_data → /app/data               │
│    - backend_logs → /app/logs               │
└─────────────────┬───────────────────────────┘
                  │
                  │ HTTP API
                  ▼
┌─────────────────────────────────────────────┐
│  Ollama (LLM Service)                       │
│  Port: 11434                                │
│  Volume: ollama_data → /root/.ollama        │
└─────────────────────────────────────────────┘

Network: mai-network (bridge)
```

---

## 📊 Service Details

### Ollama (LLM Service)
- **Image**: `ollama/ollama:latest`
- **Port**: 11434
- **Volume**: `ollama_data` (persistent model storage ~10-20GB)
- **Health Check**: Checks `/api/tags` endpoint every 30s
- **Purpose**: Runs local LLM models (gpt-oss:120b-cloud, nomic-embed-text)

### Backend (API Server)
- **Base Image**: `python:3.11-slim`
- **Port**: 8000
- **Development**: Hot reload enabled via uvicorn --reload
- **Database**: SQLite stored in `backend_data` volume
- **Logs**: Stored in `backend_logs` volume
- **Dependencies**: Ollama must be healthy before starting

### Frontend (Web UI)
- **Base Image**: `node:18-alpine`
- **Port**: 5173
- **Development**: Vite dev server with hot reload
- **Build Tool**: Vite 7.2.4
- **Dependencies**: Backend must be healthy before starting

---

## 🔧 Environment Variables

Create `.env` from `.env.example`:

```env
# Backend
OLLAMA_BASE_URL=http://ollama:11434
DATABASE_PATH=/app/data/checkpoints.db
LOG_LEVEL=INFO

# Frontend
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

---

## 📝 Common Commands Reference

### PowerShell (Windows)
```powershell
.\docker.ps1 help         # Show all commands
.\docker.ps1 build        # Build images
.\docker.ps1 up           # Start services
.\docker.ps1 down         # Stop services
.\docker.ps1 logs         # View logs
.\docker.ps1 pull-models  # Download LLM models
.\docker.ps1 test         # Run backend tests
.\docker.ps1 status       # Check service status
.\docker.ps1 clean        # Remove everything
```

### Docker Compose (Cross-platform)
```bash
docker-compose up -d              # Start in background
docker-compose down               # Stop services
docker-compose logs -f            # Stream logs
docker-compose ps                 # List services
docker-compose restart            # Restart all
docker-compose exec backend bash  # Backend shell
docker-compose exec frontend sh   # Frontend shell
```

### Makefile (Linux/Mac)
```bash
make help          # Show all commands
make setup         # Full setup
make up            # Start services
make down          # Stop services
make logs          # View logs
make pull-models   # Download LLM models
make test          # Run tests
```

---

## 📦 Data Persistence

Docker volumes ensure data persists across container restarts:

| Volume | Size | Purpose |
|--------|------|---------|
| `ollama_data` | ~10-20GB | LLM models (gpt-oss, nomic-embed-text) |
| `backend_data` | ~100MB | SQLite database (checkpoints.db) |
| `backend_logs` | ~10MB | Application logs |

### Backup Data
```bash
# Backup database
docker cp mai-backend:/app/data/checkpoints.db ./backup.db

# List volumes
docker volume ls

# Inspect volume location
docker volume inspect multi-agent-intelligence_backend_data
```

---

## 🎯 Access Points

Once all services are running:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Ollama API**: http://localhost:11434

### Default Login Credentials
- Admin: `admin:admin`
- Developer: `dev:dev`
- User: `user:user`

---

## 🐛 Troubleshooting

### Services Won't Start
```bash
# Check logs for errors
docker-compose logs backend
docker-compose logs frontend
docker-compose logs ollama

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Port Conflicts
```bash
# Check what's using the port (Windows)
netstat -ano | findstr :8000
netstat -ano | findstr :5173
netstat -ano | findstr :11434

# Kill process by PID
taskkill /PID <PID> /F
```

### Out of Disk Space
```bash
# Clean up unused Docker resources
docker system prune -a
docker volume prune

# Remove specific volume (⚠️ DELETES DATA)
docker volume rm multi-agent-intelligence_ollama_data
```

### Database Locked
```bash
# Stop services and remove data volume
docker-compose down
docker volume rm multi-agent-intelligence_backend_data
docker-compose up
```

### Models Not Loading
```bash
# Check if models are downloaded
docker-compose exec ollama ollama list

# Re-download models
docker-compose exec ollama ollama pull gpt-oss:120b-cloud
docker-compose exec ollama ollama pull nomic-embed-text
```

---

## 🚀 Development Workflow

### 1. Start Development Environment
```powershell
.\docker.ps1 setup
```

### 2. Make Code Changes
- **Backend**: Edit files in `./backend/src/` - auto-reload enabled
- **Frontend**: Edit files in `./frontend/src/` - hot reload enabled

### 3. View Logs
```powershell
.\docker.ps1 logs
```

### 4. Run Tests
```powershell
.\docker.ps1 test
```

### 5. Stop When Done
```powershell
.\docker.ps1 down
```

---

## 📚 Documentation Links

- **[DOCKER_QUICKSTART.md](./DOCKER_QUICKSTART.md)** - Quick reference (start here!)
- **[README.docker.md](./README.docker.md)** - Complete Docker guide
- **[QUICKSTART.md](./QUICKSTART.md)** - Feature walkthrough
- **[README.md](./README.md)** - Main project overview

---

## ✅ Next Steps

After setup is complete:

1. ✅ Verify all services are running: `.\docker.ps1 status`
2. ✅ Open frontend: http://localhost:5173
3. ✅ Login with `admin:admin`
4. ✅ Select a domain and agent
5. ✅ Start chatting with the multi-agent system!

---

## 🎓 What You've Achieved

With this Docker setup, you now have:

✅ **Zero-manual setup** - Everything automated in docker-compose
✅ **Isolated environment** - No conflicts with local Python/Node
✅ **Persistent data** - Models and database survive restarts
✅ **Hot reload** - Backend and frontend code changes reload automatically
✅ **Health checks** - Services wait for dependencies before starting
✅ **Easy cleanup** - Remove everything with one command

---

**Created**: January 22, 2026  
**Last Updated**: January 22, 2026  
**Version**: 1.0.0
