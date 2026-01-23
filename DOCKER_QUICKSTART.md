# 🐳 Docker Quick Start

Get the entire Multi-Agent Intelligence Platform running with just a few commands!

## Prerequisites
- Docker Desktop installed and running
- At least 8GB RAM available

## Quick Start (3 Commands)

### 1. Build and Start All Services
```bash
# Using PowerShell script (Windows)
.\docker.ps1 setup

# Or using docker-compose directly
docker-compose up -d --build
```

### 2. Pull Ollama Models
```bash
# Using PowerShell script
.\docker.ps1 pull-models

# Or using docker-compose directly
docker-compose exec ollama ollama pull gpt-oss:120b-cloud
docker-compose exec ollama ollama pull nomic-embed-text
```

### 3. Open in Browser
Navigate to **http://localhost** (port 80) and login with:
- **Admin**: `admin:admin`
- **Developer**: `dev:dev`
- **User**: `user:user`

---

## Available Services

All services are accessed through **Nginx reverse proxy on port 80**:

| Service | URL | Description |
|---------|-----|-------------|
| **Application** | http://localhost | Main UI (Frontend via Nginx) |
| API Endpoints | http://localhost/api | Backend REST API |
| API Docs | http://localhost/docs | Swagger UI |
| Health Check | http://localhost/health | System Health |
| WebSocket | ws://localhost/ws | Real-time Chat |

**Note**: Frontend (port 5173) and Backend (port 8000) are **not exposed** directly - all access is through Nginx on port 80.

---

## Common Commands

### Using PowerShell Script (Recommended for Windows)
```bash
.\docker.ps1 help        # Show all commands
.\docker.ps1 up          # Start services
.\docker.ps1 down        # Stop services
.\docker.ps1 logs        # View logs
.\docker.ps1 status      # Check status
.\docker.ps1 test        # Run backend tests
```

### Using Docker Compose Directly
```bash
docker-compose up -d              # Start in background
docker-compose down               # Stop services
docker-compose logs -f            # View logs
docker-compose logs -f backend    # View backend logs only
docker-compose ps                 # Check status
docker-compose restart            # Restart all services
```

---

## Troubleshooting

### Services not starting?
```bash
# Check status
docker-compose ps

# View logs
docker-compose logs

# Rebuild
docker-compose down
docker-compose up --build
```

### Port already in use?
Check what's using ports 5173, 8000, or 11434 and stop those processes, or change the port mapping in `docker-compose.yml`.

### Out of disk space?
```bash
# Clean up Docker
docker system prune -a
docker volume prune
```

---

## Full Documentation

For detailed Docker setup, configuration, and troubleshooting:
- **[README.docker.md](./README.docker.md)** - Complete Docker guide

For feature documentation:
- **[QUICKSTART.md](./QUICKSTART.md)** - Feature walkthrough
- **[README.md](./README.md)** - Main project overview

---

## What's Running?

The Docker setup includes:
1. **Ollama** - LLM service with model persistence
2. **Backend** - FastAPI server with auto-reload
3. **Frontend** - React + Vite with hot reload

All services are networked together and data is persisted in Docker volumes.

---

**Last Updated**: January 22, 2026
