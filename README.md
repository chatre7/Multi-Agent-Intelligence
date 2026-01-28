# Multi-Agent Intelligence Platform

> Zero-code domain extension platform with modern React UI, Clean Architecture + TDD, and real-time character-by-character streaming orchestration.

![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![Backend Tests](https://img.shields.io/badge/Backend%20Tests-150%2B%20passing-green)
![Threads](https://img.shields.io/badge/Threads-Persistence%20%2B%20History-blueviolet)
![Streaming](https://img.shields.io/badge/Streaming-Real--time%20Tokens-blue)
![Frontend](https://img.shields.io/badge/Frontend-React%2019%2BVite-blue)
![Docker](https://img.shields.io/badge/Docker-Production%20Ready-blue)
![License](https://img.shields.io/badge/License-MIT-orange)

---

## 📢 Latest Updates (v1.6.0) - Jan 28, 2026

### 🧵 Threads Persistence & Deep-Linking
- **Stateful Refresh**: Threads now support `/threads/:id` routing. Refreshing the browser no longer loses simulation state.
- **Full History Preservation**: Backend now persists *every* agent message in a multi-agent simulation, not just the final response.
- **Recent Threads Sidebar**: A new "Recent Threads" section in the sidebar allows users to quickly jump between past simulations.

### 🎭 Social Simulation Engine v1.1
- **Balanced Participation**: Implemented a **Round-Robin** speaker selection to ensure equal participation from all agents in a domain.
- **Aggressive Sanitization**: Multi-stage regex cleaning removes LLM artifacts (like `<think>` leftovers, role classifications, or scores) for a pure conversational experience.
- **Domain Isolation**: Agents are now strictly filtered based on the active domain configuration.

### 🧠 Thinking Mode & Integrated Reasoning (v1.5)
- **Per-Conversation Toggle**: Control visibility of the AI's reasoning process per chat.
- **Integrated UI**: Reasoning is embedded with a collapsible, "Deep Research" inspired design.

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

✅ **Stateful Threads & History** (New)
- **Deep Linking**: Direct access/refresh support via `/threads/:id`.
- **Simulation Persistence**: All intermediate agent posts are saved to the database.
- **Recents Navigation**: Sidebar integration for quick thread switching.

✅ **Advanced Reasoning & Observability**
- **Thinking Mode**: Toggleable Chain-of-Thought visibility for deep reasoning tasks.
- **Skill Badges**: Real-time visual feedback when agents apply specific skills.

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

### Real-Time Streaming Flow (v1.5.0)

```
[UI] <--- (SSE/WebSocket) --- [FastAPI] --- (Queue) <--- [Streaming Thread]
                                                              │
                                                      [LangGraph Execution]
                                                              │
                                                      [Agent Node] --(Stream)--> [Tokens]
                                                              │
                                                      [Thought Extraction Engine]
                                                              │
                                                 (Intercepts <think> & [SKILL] tags)
```

This architecture ensures that as soon as an LLM provider yields a token, it is pushed through a side-channel queue. Simultaneously, the **Thought Extraction Engine** scans for semantic tags (`<think>`, `[USING SKILL]`) to update the UI state (e.g., showing a badge or expanding a card) **before** the text even renders, enhancing perceived responsiveness.

---

## 🚧 Known Issues

### 🤖 Social Simulation Artifacts
While the `social_simulation` strategy provides a realistic autonomous thread experience, some models may still exhibit **Prompt Leakage** or **Technical Meta-data** in their outputs (e.g., orphaned `</likes>` tags or role classification lists like `Test Engineer: 1`).

- **Current Mitigation**: A regex-based sanitizer in `SocialSimulationStrategy._clean_content` strips most common artifacts.
- **Future Fix**: We plan to improve the system prompt robustness and implement a Pydantic-based output validator to ensure 100% clean casual text.

---

## 📜 Changelog

### [1.6.0] - 2026-01-28
#### Added
- **Threads Persistence**: Multi-message saving for social simulations.
- **Thread History UI**: "Recent Threads" sidebar component.
- **Deep Routing**: URL support for individual threads (`/threads/:id`).
- **Round-Robin Selection**: Balanced agent participation in simulations.
#### Fixed
- **Simulation Cleanup**: Aggressive regex cleaning for LLM artifacts/scores.
- **Entity Stability**: Added missing `metadata` attribute to `Agent` entities.
- **LLM Invocations**: Switched from `.invoke()` to `.stream_chat()` for OpenAI-compatible providers.
- **Frontend Build**: Resolved missing API client methods and relative import path level errors.

### [1.5.0] - 2026-01-28
#### Added
- **Thinking Mode Toggle**: Per-conversation UI toggle to enable/disable reasoning display.
- **Skill Observability**: "Zap Badges" that appear in real-time when agents apply skills.
- **Integrated Reasoning UI**: Redesigned "Thinking" section with "Deep Research" aesthetics (collapsible, attributed).
#### Changed
- **System Prompt Injection**: Dynamic injection of thinking instructions based on client-side toggle.
- **Token Streaming**: Enhanced `WebSocketClient` to handle `isStreaming` state more accurately during handoffs.
#### Fixed
- **Handoff Persistence**: Resolved bug where thoughts disappeared when switching agents.
- **Data Ingestion**: Fixed unwrapping of WebSocket payloads for thought events.
- **Strategy Context**: Fixed `FewShotStrategy` ignoring initial system messages.

### [1.4.0] - 2026-01-27
#### Added
- **Token Streaming Side-Channel**: Implementation of `queue.Queue` and `threading.Thread` in `SendMessageUseCase.stream`.
- **Workflow Callback Interface**: New `token_callback` parameter added to all `WorkflowStrategy` execution methods.

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
**Version**: 1.6.0 | **Updated**: January 28, 2026
