# Multi-Agent Intelligence Platform

> Zero-code domain extension platform with modern React UI, Clean Architecture + TDD, and real-time WebSocket streaming

![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![Backend Tests](https://img.shields.io/badge/Backend%20Tests-150%2B%20passing-green)
![Frontend](https://img.shields.io/badge/Frontend-React%2019%2BVite-blue)
![Docker](https://img.shields.io/badge/Docker-Production%20Ready-blue)
![License](https://img.shields.io/badge/License-MIT-orange)

---

## 📢 Latest Updates (v1.2.0) - Jan 23, 2026

### 🌟 New Features
- **Multi-Workflow Strategies**: Flexible agent orchestration tailored to your needs:
  - `orchestrator`: Deterministic, step-by-step pipelines (e.g., Software Dev: Plan -> Code -> Review)
  - `few_shot`: LLM-driven autonomous handoffs with Thai language support (e.g., Social Chat: Empath -> Comedian)
  - `hybrid`: Combining both strategies for complex domains.
- **Real LLM Integration**: 
  - Full support for **Ollama** (local), OpenAI, and compatible providers.
  - Streaming responses with real-time token delivery.
- **Improved Performance**:
  - **Optimized Docker Builds**: Reduced build context size by 90% via `.dockerignore`.
  - **Fast Tests**: Mocked heavy dependencies (transformers/torch) speeding up test collection by 50x.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Quick Start](#-quick-start)
  - [Development Mode](#development-mode)
  - [Production Mode (Docker)](#production-mode-docker)
  - [Using Ollama (Local LLM)](#using-ollama-local-llm)
- [Multi-Workflow Capabilities](#-multi-workflow-capabilities)
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
- **TDD First**: 150+ comprehensive unit & integration tests
- Full REST API with 25+ endpoints
- Real-time WebSocket streaming
- JWT + RBAC authentication

✅ **Modern Frontend**
- React 19 + TypeScript + Vite
- Zustand state management
- Real-time chat with streaming
- Admin panel with metrics dashboard

✅ **Intelligent Orchestration**
- **Dynamic Routing**: Agents can hand off tasks autonomously.
- **Workflow Strategies**: Choose between rigid pipelines or flexible conversations.
- **Human-in-the-loop**: Tool approval workflows.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** - Backend runtime
- **Node.js 20+** - Frontend runtime (22+ recommended for Vite 7)
- **Docker & Docker Compose** - For production deployment
- **Ollama** (optional) - Recommended for local LLM

### Development Mode

Run backend and frontend separately for hot-reload development:

**1. Start Backend**
```bash
cd backend
pip install -e .
python -m uvicorn src.presentation.api.app:create_app --factory --reload --port 8000
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

```bash
# Optimized production build with Nginx
docker compose -f docker-compose.prod.yml up -d --build
# Access at http://localhost
```

### Using Ollama (Local LLM)

1. Install and run Ollama: `ollama run llama3`
2. Update `.env` or `docker-compose.prod.yml`:
```env
LLM_PROVIDER=openai
OPENAI_BASE_URL=http://host.docker.internal:11434/v1  # or http://localhost:11434/v1
OPENAI_API_KEY=ollama
LLM_MODEL=llama3
```

---

## 🔀 Multi-Workflow Capabilities

The platform now supports three distinct workflow strategies configurable per domain:

### 1. Orchestrator Strategy
**Best for**: Defined processes like software development or data pipelines.
- **Behavior**: Executes agents in a fixed, linear order.
- **Config**:
  ```yaml
  workflow_type: orchestrator
  orchestration:
    pipeline: ["planner", "coder", "reviewer"]
  ```

### 2. Few-Shot Strategy
**Best for**: Chatbots, customer support, and dynamic conversations.
- **Behavior**: Agents decide who talks next based on conversation context and few-shot examples.
- **Config**:
  ```yaml
  workflow_type: few_shot
  few_shot:
    max_handoffs: 5
    examples_enabled: true
  ```
- **Note**: Now allows Thai language handoffs (e.g., "เครียดจัง" -> handoff to Comedian).

### 3. Hybrid Strategy
**Best for**: Complex research or multi-phase tasks.
- **Behavior**: Combines rigid planning phases with flexible execution phases.
- **Config**:
  ```yaml
  workflow_type: hybrid
  hybrid:
    orchestrator_decides: ["planning", "validation"]
    llm_decides: ["agent_selection"]
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
│  │  Domain         (Entities, Workflow Strategies)  │    │
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
│   │   ├── infrastructure/    # Repositories, LLM, LangGraph
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
├── docs/                       # Documentation
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

**Backend (`docker-compose.yml` or `.env`):**
```yaml
environment:
  - MVP_MODE=false                   # Enable full features
  - AUTH_MODE=jwt
  - AUTH_SECRET=your-secret-key
  - LLM_PROVIDER=openai              # Use 'openai' for Ollama/OpenAI
  - OPENAI_BASE_URL=http://host.docker.internal:11434/v1
  - LLM_MODEL=llama3
```

**Frontend (`docker-compose.yml`):**
```yaml
environment:
  - VITE_API_BASE_URL=/api
  - VITE_WS_URL=/ws
  - BACKEND_HOST=backend
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

# Run all tests (fast collection enabled)
uv run pytest

# Run manual workflow test script
uv run python scripts/test_workflows.py
```

### Frontend Tests

```bash
cd frontend
npm run type-check
npm run lint
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

# Rebuild from scratch (clean slate)
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

## 🔮 Roadmap

### 1. Live Workflow Visualizer (Observability)
**Visualizing Agent Thoughts in Real-time**
- **Concept**: Interactive UI graph showing active agents and message flow.
- **Tech**: React Flow + WebSocket events.
- **Value**: See exactly when `Empath` decides to hand off to `Comedian`.

### 2. Human-in-the-Loop (Approval Center)
**Safety First for Powerful Tools**
- **Concept**: Dashboard for admins to approve sensitive actions (e.g., DB writes, Emails).
- **Tech**: Existing `ApproveToolRun` API + Admin UI.
- **Value**: Secure control over autonomous agents.

### 3. Python Code Interpreter (Sandbox)
**Agents that can Code**
- **Concept**: Secure Docker sandbox for agents to write/run Python for data analysis.
- **Tech**: Docker API + Jupyter Kernel.
- **Value**: Dynamic problem solving and data visualization.

### 4. Voice Mode (Real-time Audio)
**Conversational Interface**
- **Concept**: Hands-free interaction via voice.
- **Tech**: Whisper (STT) + Edge TTS / ElevenLabs.
- **Value**: Natural, human-like interaction experience.

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
**Version**: 1.2.0

