# Multi-Agent Intelligence Platform

> Zero-code domain extension platform with modern React UI, Clean Architecture + TDD, and real-time WebSocket streaming

![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![Backend Tests](https://img.shields.io/badge/Backend%20Tests-150%2B%20passing-green)
![Frontend](https://img.shields.io/badge/Frontend-React%2019%2BVite-blue)
![Docker](https://img.shields.io/badge/Docker-Production%20Ready-blue)
![License](https://img.shields.io/badge/License-MIT-orange)

---

## 📢 Latest Updates (v1.3.1) - Jan 27, 2026

### 🐛 Bug Fixes & Test Improvements
- **Orchestration Tests**: Fixed critical routing and JSON import issues, achieving **100% test pass rate** (10/10 orchestration tests now passing)
  - Fixed missing `json` module import in workflow strategies
  - Corrected router step tracking expectations
  - Added pytest-compatible integration tests
  - See [ORCHESTRATION_FIXES.md](ORCHESTRATION_FIXES.md) for detailed analysis
- **Test Coverage**: Improved from 0/5 to 10/10 passing for workflow orchestration tests

### 🌟 Previous Features (v1.3.0)
- **Workflow Observability v2**:
  - **Persistent Event Logs**: All agent thoughts, handoffs, and decisions are now saved to SQLite for historical analysis.
  - **Interactive Visualizer Table**: A high-density table view in the visualizer sidebar with real-time timestamps and status indicators.
  - **Log Management**: Ability to manually refresh and **delete** individual workflow logs via the UI.
  - **Robust Routing**: Enhanced LLM router with Regex-based JSON extraction, significantly reducing "invalid response" errors for smaller models.
- **Enhanced Sidebar UI**: Expanded visualizer sidebar (500px) to accommodate detailed event logs and agent reasoning.

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
- [Changelog](#-changelog)
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
- Full REST API with 30+ endpoints
- Real-time WebSocket streaming
- JWT + RBAC authentication

✅ **Modern Frontend**
- React 19 + TypeScript + Vite
- **Workflow Visualizer**: Real-time graph visualization of agent interactions.
- **Persistent Logs**: History of agent reasoning and handoffs.
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

---

## 🔀 Multi-Workflow Capabilities

The platform now supports three distinct workflow strategies configurable per domain:

### 1. Orchestrator Strategy
**Best for**: Defined processes like software development or data pipelines.
- **Behavior**: Executes agents in a fixed, linear order.

### 2. Few-Shot Strategy
**Best for**: Chatbots, customer support, and dynamic conversations.
- **Behavior**: Agents decide who talks next based on conversation context and few-shot examples.

### 3. Hybrid Strategy
**Best for**: Complex research or multi-phase tasks.
- **Behavior**: Combines rigid planning phases with flexible execution phases.

---

## 🏗️ Architecture

### Production Deployment

```
┌─────────────────────────────────────────────────────────┐
│                      Browser                             │
│                   http://localhost                       │
│  (React Flow Visualizer + Tailwind + Persistent Logs)    │
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
                         ▼
┌─────────────────────────────────────────────────────────┐
│                Backend (FastAPI, port 8000)              │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Presentation   (Workflow Log API, WebSocket)     │    │
│  ├─────────────────────────────────────────────────┤    │
│  │  Application    (SendMessageUseCase, Logging)    │    │
│  ├─────────────────────────────────────────────────┤    │
│  │  Domain         (WorkflowLog Entities)           │    │
│  ├─────────────────────────────────────────────────┤    │
│  │  Infrastructure (SQLite WorkflowLogs, LLM Router) │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 📡 API Reference (Modified/New)

### Workflow Logs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/conversations/{id}/workflow-logs` | GET | List all persistent logs for a conversation |
| `/v1/workflow-logs/{id}` | DELETE | Delete a specific log entry |

### Conversations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/conversations` | GET | List conversations |
| `/v1/conversations` | POST | Create conversation |
| `/v1/conversations/{id}/messages` | GET | Get messages |

---

## 📜 Changelog

### [1.3.0] - 2026-01-25
#### Added
- **Workflow Logging System**: Backend persistence for agent reasoning and decisions in SQLite.
- **Visualizer Table Interface**: New high-density table in the Visualizer sidebar with status, agent name, message, and timestamp.
- **Log Deletion**: API and UI support for removing specific log entries.
- **Regex JSON Extraction**: New robust router logic to handle LLM conversational noise.
#### Changed
- Increased Visualizer sidebar width to **500px** for better readability.
- Replaced Web Socket reconstruction with API-driven log fetching in Visualizer.
- Improved Router robustness by falling back to `LLM_MODEL`.

### [1.2.0] - 2026-01-23
#### Added
- Multi-Workflow Strategies (`orchestrator`, `few_shot`, `hybrid`).
- Thai language support for autonomous handoffs.
#### Improved
- Fast test collection (50x speedup).
- Optimized Docker build context size.

---

## ⚙️ Configuration

### Environment Variables

**Backend (`docker-compose.yml` or `.env`):**
```yaml
environment:
  - CONVERSATION_REPO=sqlite           # Required for log persistence
  - CONVERSATION_DB=/app/data/conversations.db
  - LLM_PROVIDER=openai
  - OPENAI_BASE_URL=http://host.docker.internal:11434/v1
  - LLM_MODEL=llama3
  - ROUTER_MODEL=llama3                # Model used for agent switching
```

---

## 🧪 Testing

### Backend Tests

**Quick Test Run**:
```bash
cd backend
uv run pytest  # Run all tests
```

**Orchestration Tests** (100% passing):
```bash
# Run workflow strategy tests
pytest tests/test_orchestrator_validation.py -v  # 2/2 ✅
pytest tests/test_fewshot_router.py -v           # 2/2 ✅
pytest tests/test_hybrid_summary.py -v           # 3/3 ✅
pytest tests/test_workflow_integration.py -v     # 3/3 ✅
```

**Test Coverage**:
```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html to view detailed coverage
```

**Test Status Summary**:
- ✅ **Orchestration Tests**: 10/10 passing (100%)
- ✅ **Workflow Strategies**: All 3 strategies validated (Orchestrator, Few-Shot, Hybrid)
- ✅ **Integration Tests**: End-to-end workflow execution verified
- 📊 **Total Backend Tests**: 150+ passing

For detailed orchestration test fixes, see [ORCHESTRATION_FIXES.md](ORCHESTRATION_FIXES.md).

---

## 🔮 Roadmap

### 1. ✅ Live Workflow Visualizer (Observability)
- **Status**: Completed in v1.3.0.
- Real-time graph + Persistent Table Logs.

### 2. Human-in-the-Loop (Approval Center)
- **Concept**: Dashboard for admins to approve sensitive actions (e.g., DB writes, Emails).
- **Tech**: Existing `ApproveToolRun` API + Admin UI.

### 3. Python Code Interpreter (Sandbox)
- **Concept**: Secure Docker sandbox for agents to write/run Python.

### 4. Voice Mode (Real-time Audio)
- **Concept**: Hands-free interaction via Whisper + ElevenLabs.

---

## 📄 License

MIT License - See [LICENSE](./LICENSE) file for details

---

**Status**: ✅ Production Ready  
**Last Updated**: January 25, 2026  
**Version**: 1.3.0
