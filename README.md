# Multi-Agent Intelligence Platform

> Zero-code domain extension platform with modern React UI, Clean Architecture + TDD, and real-time character-by-character streaming orchestration.

![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![Backend Tests](https://img.shields.io/badge/Backend%20Tests-150%2B%20passing-green)
![Streaming](https://img.shields.io/badge/Streaming-Real--time%20Tokens-blue)
![Frontend](https://img.shields.io/badge/Frontend-React%2019%2BVite-blue)
![Docker](https://img.shields.io/badge/Docker-Production%20Ready-blue)
![License](https://img.shields.io/badge/License-MIT-orange)

---

## 📢 Latest Updates (v1.4.0) - Jan 27, 2026

### 🚀 Real-Time Token Streaming & Reliability
- **Smooth Streaming UI**: Tokens now stream character-by-character to the frontend, even when executing complex multi-agent workflows. 
- **Concurrency Overhaul**: Implemented a `Thread + Queue` pattern in the `SendMessageUseCase` to capture side-channel tokens from LangGraph nodes without blocking the event loop.
- **Workflow Callback System**: Added `token_callback` support to `OrchestratorStrategy`, `Few-ShotStrategy`, and `HybridStrategy`, ensuring complete transparency during agent reasoning.
- **LLM Robustness**: 
  - Fixed critical `TypeError` where `max_tokens` was missing in internal LLM calls.
  - Enforced strict token limit validation based on agent YAML configuration.
  - Successfully tested with **Large Language Models** (120B+ parameters) via Ollama/OpenAI adapters.
- **Infrastructure Stability**: Resolved Nginx production healthcheck issues by switching to local IPv4 loopback (127.0.0.1).

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

Transform complex multi-agent orchestration into a **configuration-driven platform** where domains and agents are defined via YAML files, synced to SQLite, and exposed through a modern React UI with **instant streaming feedback**.

### Key Features

✅ **Streaming Orchestration**
- Character-by-character token delivery even across multi-agent handoffs.
- Non-blocking execution using Python threading/queueing.
- Real-time visualization of agent thoughts and decisions.

✅ **Configuration-Driven Architecture**
- Define domains and agents in YAML (e.g., `max_tokens`, `temperature`, `skills`).
- Automatic SQLite sync for SQL querying.
- Zero-code domain extension.

✅ **Production-Ready Backend**
- Clean Architecture (Domain → Application → Infrastructure → Presentation).
- **TDD First**: 150+ comprehensive unit & integration tests.
- JWT + RBAC authentication.
- Optimized Nginx production container with robust healthchecks.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** - Backend runtime
- **Node.js 20+** - Frontend runtime
- **Docker & Docker Compose** - For production deployment
- **Ollama** (optional) - Recommended for local LLM (OpenAI-compatible)

### Development Mode

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
- Credentials: `admin:admin`, `dev:dev`, or `user:user`

### Production Mode (Docker)

```bash
# Production optimized build (Nginx + Static React + FastAPI)
docker compose up -d --build
# Access at http://localhost
```

---

## 🔀 Multi-Workflow Capabilities

Every domain can utilize a specific strategy defined in its metadata:

| Strategy | Best For | Behavior |
|----------|----------|----------|
| **Orchestrator** | Pipelines (DevOps, RAG) | Fixed, linear sequence of specialist agents. |
| **Few-Shot** | Customer Support, RP | LLM decides routing based on dynamic examples. |
| **Hybrid** | Research, Planning | Orchestrated planning followed by flexible execution. |

*Streaming is natively supported across all three strategies via the new `token_callback` interface.*

---

## 🏗️ Architecture

### Real-Time Streaming Flow (v1.4.0)

```
[UI] <--- (SSE/WebSocket) --- [FastAPI] --- (Queue) <--- [Streaming Thread]
                                                             │
                                                     [LangGraph Execution]
                                                             │
                                                     [Agent Node 1 (Streamed)]
                                                             │
                                                     [Agent Node 2 (Streamed)]
```

This architecture ensures that as soon as an LLM provider (Ollama/OpenAI) yields a token, it is pushed through the side-channel queue and emitted to the user, bypassing the traditional "wait-for-finish" bottleneck of LangGraph nodes.

---

## 📜 Changelog

### [1.4.0] - 2026-01-27
#### Added
- **Token Streaming Side-Channel**: Implementation of `queue.Queue` and `threading.Thread` in `SendMessageUseCase.stream` to allow real-time token delivery from inside LangGraph nodes.
- **Workflow Callback Interface**: New `token_callback` parameter added to all `WorkflowStrategy` execution methods.
- **Storyteller Verification**: Confirmed and fixed streaming for high-token creative agents.
#### Fixed
- **LLM Signatures**: Corrected `max_tokens` argument missing in internal LLM factory calls causing system crashes.
- **Nginx Healthcheck**: Fixed production image failing healthchecks due to `localhost` resolution issues in Alpine/Debian containers.

### [1.3.1] - 2026-01-25
#### Added
- **Workflow Logging**: Backend persistence for agent reasoning and decisions in SQLite.
- **Regex JSON Extraction**: Enhanced router robustness for smaller model parsing.

---

## ⚙️ Configuration

### Agent Definition (`agents/*.yaml`)
```yaml
id: storyteller
name: Creative Storyteller
model_name: "gpt-oss:120b-cloud" # Matches your local provider
temperature: 0.9
max_tokens: 1024 # Now strictly enforced
skills: ["narrative_design"]
```

### Environment
```env
LLM_PROVIDER=openai
OPENAI_BASE_URL=http://host.docker.internal:11434/v1
LLM_MODEL=llama3
```

---

## 🧪 Testing

```bash
cd backend
# Run all tests
pytest
# Run strategy-specific tests
pytest tests/test_orchestrator_validation.py -v
```

---

## 📄 License

MIT License - See [LICENSE](./LICENSE) file for details

---

**Status**: ✅ Production Ready  
**Version**: 1.4.0 | **Updated**: January 27, 2026
