# Multi-Agent Intelligence Platform

> Zero-code domain extension platform with modern React UI, Clean Architecture + TDD, and real-time WebSocket streaming

![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![Backend Tests](https://img.shields.io/badge/Backend%20Tests-119%2F119%20passing-green)
![Frontend](https://img.shields.io/badge/Frontend-React%2019%2BVite-blue)
![Docker](https://img.shields.io/badge/Docker-Production%20Ready-blue)
![License](https://img.shields.io/badge/License-MIT-orange)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Quick Start](#-quick-start)
  - [Development Mode](#development-mode)
  - [Production Mode (Docker)](#production-mode-docker)
- [Architecture](#-architecture)
- [API Reference](#-api-reference)
- [WebSocket Protocol](#-websocket-protocol)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 🎯 Overview

Transform complex multi-agent orchestration into a **configuration-driven platform** where domains and agents are defined via YAML files, synced to SQLite, and exposed through a modern REST API + WebSocket streaming interface.

### Key Features

✅ **Configuration-Driven Architecture**
- Define domains and agents in YAML
- Automatic SQLite sync for SQL querying
- Zero-code domain extension

✅ **Production-Ready Backend**
- Clean Architecture (Domain → Application → Infrastructure → Presentation)
- Test-Driven Development (119+ tests passing)
- Full REST API with 25+ endpoints
- Real-time WebSocket streaming
- JWT + RBAC authentication

✅ **Modern Frontend**
- React 19 + TypeScript + Vite
- Zustand state management
- Real-time chat with streaming
- Admin panel with metrics dashboard

✅ **Multi-Agent Orchestration**
- LangGraph-based agent coordination
- Supervisor pattern with intelligent routing
- Human-in-the-loop tool approval
- Version management (DEVELOPMENT → TESTING → PRODUCTION)

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** - Backend runtime
- **Node.js 20+** - Frontend runtime (22+ recommended for Vite 7)
- **Docker & Docker Compose** - For production deployment
- **Ollama** (optional) - LLM provider

### Development Mode

Run backend and frontend separately for hot-reload development:

**1. Start Backend**
```bash
cd backend
pip install -e .
python -m uvicorn src.presentation.api.app:create_app --reload --port 8000
```

**2. Start Frontend**
```bash
cd frontend
npm install
npm run dev
```

**3. Open in Browser**
- Navigate to `http://localhost:5173`
- Login with: `admin:admin` or `dev:dev` or `user:user`

### Production Mode (Docker)

Single command to build and run the entire stack:

**Option 1: Development with hot-reload**
```bash
docker compose up -d --build
# Access at http://localhost
```

**Option 2: Production (static frontend)**
```bash
docker compose -f docker-compose.prod.yml up -d --build
# Access at http://localhost
```

**Useful Docker Commands:**
```bash
# View logs
docker logs mai-backend -f
docker logs mai-nginx -f

# Rebuild single service
docker compose -f docker-compose.prod.yml up -d --build nginx

# Stop all
docker compose -f docker-compose.prod.yml down

# Stop and remove volumes
docker compose -f docker-compose.prod.yml down -v
```

---

## 🏗️ Architecture

### Production Deployment

```
┌─────────────────────────────────────────────────────────┐
│                      Browser                             │
│                   http://localhost                       │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   nginx (port 80)                        │
│  ┌─────────────┬─────────────┬─────────────────────┐    │
│  │     /       │   /api/*    │        /ws          │    │
│  │   Static    │   REST API  │     WebSocket       │    │
│  │   React     │   Proxy     │      Proxy          │    │
│  └──────┬──────┴──────┬──────┴──────────┬──────────┘    │
└─────────┼─────────────┼─────────────────┼───────────────┘
          │             │                 │
          ▼             ▼                 ▼
┌─────────────────────────────────────────────────────────┐
│                Backend (FastAPI, port 8000)              │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Presentation   (REST API, WebSocket handlers)   │    │
│  ├─────────────────────────────────────────────────┤    │
│  │  Application    (Use Cases, Business Logic)      │    │
│  ├─────────────────────────────────────────────────┤    │
│  │  Domain         (Entities, Value Objects)        │    │
│  ├─────────────────────────────────────────────────┤    │
│  │  Infrastructure (SQLite, LLM, Repositories)      │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### Directory Structure

```
Multi-Agent-Intelligence/
├── backend/                    # FastAPI Backend
│   ├── src/
│   │   ├── domain/            # Entities, Value Objects
│   │   ├── application/       # Use Cases
│   │   ├── infrastructure/    # Repositories, LLM
│   │   └── presentation/      # API, WebSocket
│   ├── tests/                 # Unit & Integration Tests
│   └── config/                # YAML Configurations
│       ├── domains/           # Domain definitions
│       ├── agents/            # Agent definitions
│       └── tools/             # Tool definitions
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── domain/            # Types, Entities
│   │   ├── infrastructure/    # API Client, WebSocket, Stores
│   │   └── presentation/      # Components, Pages
│   └── dist/                  # Production build
│
├── nginx/                      # Nginx Configuration
│   ├── nginx.conf             # Development config
│   ├── nginx.prod.conf        # Production config
│   ├── Dockerfile             # Development Dockerfile
│   └── Dockerfile.prod        # Production Dockerfile
│
├── docs/                       # Documentation
│   └── WEBSOCKET_PROTOCOL.md  # WebSocket message reference
│
├── docker-compose.yml          # Development compose
├── docker-compose.prod.yml     # Production compose
└── README.md                   # This file
```

---

## 📡 API Reference

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/auth/login` | POST | Login with username/password |
| `/v1/auth/me` | GET | Get current user info |

**Login Request:**
```json
POST /v1/auth/login
{
  "username": "admin",
  "password": "admin"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "role": "admin"
}
```

### Domains & Agents

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/domains` | GET | List all domains |
| `/v1/domains/{id}` | GET | Get domain details |
| `/v1/agents` | GET | List all agents |
| `/v1/agents/{id}` | GET | Get agent details |
| `/v1/tools` | GET | List all tools |

### Conversations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/conversations` | GET | List conversations |
| `/v1/conversations` | POST | Create conversation |
| `/v1/conversations/{id}` | GET | Get conversation details |
| `/v1/conversations/{id}/messages` | GET | Get messages |
| `/v1/chat` | POST | Send message (REST) |

### Health & Metrics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Basic health check |
| `/health/details` | GET | Detailed health info |
| `/metrics` | GET | Prometheus metrics |

---

## 🔌 WebSocket Protocol

### Connection

```javascript
const token = localStorage.getItem('auth_token');
const ws = new WebSocket(`ws://localhost/ws?token=${token}`);
```

### Messages

**Start Conversation:**
```json
{
  "type": "start_conversation",
  "payload": { "domainId": "software_development" }
}
```

**Send Message:**
```json
{
  "type": "send_message",
  "conversationId": "uuid",
  "payload": { "content": "Hello" }
}
```

**Receive Streaming Response:**
```json
{ "type": "message_chunk", "payload": { "chunk": "Hello" } }
{ "type": "message_chunk", "payload": { "chunk": " world" } }
{ "type": "message_complete", "payload": { "content": "Hello world" } }
```

**Keep-Alive:**
```json
// Client sends
{ "type": "PING" }

// Server responds
{ "type": "PONG" }
```

📖 Full protocol documentation: [docs/WEBSOCKET_PROTOCOL.md](./docs/WEBSOCKET_PROTOCOL.md)

---

## ⚙️ Configuration

### Environment Variables

**Backend (`docker-compose.yml`):**
```yaml
environment:
  - AUTH_MODE=jwt                    # jwt | none
  - AUTH_SECRET=your-secret-key      # JWT signing secret
  - AUTH_USERS=admin:admin:admin     # username:password:role
  - DATABASE_PATH=/app/data/db.db    # SQLite path
  - LOG_LEVEL=INFO                   # DEBUG | INFO | WARNING
  - OLLAMA_BASE_URL=http://localhost:11434  # LLM endpoint
```

**Frontend (`docker-compose.yml`):**
```yaml
environment:
  - VITE_API_BASE_URL=/api           # API prefix
  - VITE_WS_URL=/ws                  # WebSocket prefix
  - BACKEND_HOST=backend             # Docker network hostname
```

### Default Users

| Username | Password | Role |
|----------|----------|------|
| admin | admin | admin |
| dev | dev | developer |
| user | user | user |

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/presentation/test_websocket_connection.py -v
```

### Frontend Tests

```bash
cd frontend

# Type checking
npm run type-check

# Linting
npm run lint

# Build check
npm run build
```

---

## 🔧 Troubleshooting

### WebSocket Connection Fails (Code 1006)

**Symptoms:** `WebSocket closed before open (code=1006)`

**Solutions:**
1. Verify nginx is running: `docker logs mai-nginx`
2. Check nginx config has WebSocket upgrade map
3. Access via `http://localhost` not `http://localhost:5173`
4. Verify token is valid: check browser localStorage

### 404 on API Requests

**Check nginx logs:**
```bash
docker logs mai-nginx | grep "api"
```

**Verify backend is healthy:**
```bash
curl http://localhost/api/v1/health
```

### Container Won't Start

```bash
# Check logs
docker logs mai-backend
docker logs mai-nginx

# Rebuild from scratch
docker compose -f docker-compose.prod.yml down -v
docker compose -f docker-compose.prod.yml up -d --build
```

### Port Already in Use

```bash
# Find process using port 80
netstat -ano | findstr :80

# Kill process (Windows)
taskkill /PID <PID> /F
```

---

## 📄 License

MIT License - See [LICENSE](./LICENSE) file for details

---

## 📚 Additional Documentation

- 📖 **[Quick Start Guide](./QUICKSTART.md)** - Detailed setup instructions
- 🔌 **[WebSocket Protocol](./docs/WEBSOCKET_PROTOCOL.md)** - Full message reference
- 🏗️ **[Implementation Summary](./IMPLEMENTATION_SUMMARY.md)** - Architecture details
- 🔧 **[Backend README](./backend/README.md)** - Backend development
- ⚛️ **[Frontend README](./frontend/README.md)** - Frontend development

---

**Status**: ✅ Production Ready  
**Last Updated**: January 23, 2026  
**Version**: 1.1.0

