# Multi-Agent Intelligence Platform

> **Build, simulate, and orchestrate expert AI agents with zero code.**
> A configuration-driven platform featuring real-time character-by-character streaming, clean architecture, and modern React UI.

![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![Backend Tests](https://img.shields.io/badge/Backend%20Tests-150%2B%20passing-green)
![Threads](https://img.shields.io/badge/Threads-Persistence%20%2B%20History-blueviolet)
![Streaming](https://img.shields.io/badge/Streaming-Real--time%20Tokens-blue)
![Frontend](https://img.shields.io/badge/Frontend-React%2019%2BVite-blue)
![Docker](https://img.shields.io/badge/Docker-Production%20Ready-blue)
![License](https://img.shields.io/badge/License-MIT-orange)

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development](#local-development)
  - [Production (Docker)](#production-docker)
- [Configuration Guide](#-configuration-guide)
  - [Defining Agents](#defining-agents)
  - [Domains & Strategies](#domains--strategies)
- [API Reference](#-api-reference)
- [Troubleshooting](#-troubleshooting)
- [Changelog](#-changelog)
- [License](#-license)

---

## 🎯 Overview

The **Multi-Agent Intelligence Platform** transforms complex agent orchestration into a simple, configuration-based workflow. Instead of writing boilerplate Python for every new agent, you define their persona, model, and skills in **YAML**. The system handles the heavy lifting: state management, LLM communication, streaming responses to the frontend, and persisting conversation history.

Whether you're building a customer support swarm, a creative writing team, or a research analysis pipeline, this platform provides the robust foundation you need.

---

## 🌟 Key Features

### 1. **Zero-Code Domain Extension**
Add new agents and domains strictly through configuration files.
- **Agents**: Define `backend/configs/agents/*.yaml` (e.g., "Storyteller", "Code Reviewer").
- **Domains**: Define `backend/configs/domains/*.yaml` which groups agents into functional units.
- **Hot-Reload**: The system detects changes and updates available agents instantly.

### 2. **Real-Time Streaming Orchestration**
Experience a "ChatGPT-like" feel with our advanced streaming architecture.
- **Character-by-Character**: Tokens are pushed to the UI via WebSockets/SSE the moment they are generated.
- **Multi-Agent Handoff**: Streaming continues seamlessly even as control passes from one agent to another.
- **Thought Visualization**: See the "Thinking..." process and tool usage in real-time.

### 3. **Social Simulation Engine**
Create dynamic multi-agent conversations where AI characters talk to *each other*.
- **Round-Robin & Dynamic Turn-Taking**: Agents speak in a natural flow based on the configured strategy.
- **Observer Mode**: Watch agents debate, brainstorm, or chat without human intervention.
- **Artifact Cleaning**: Automatic removal of LLM artifacts (e.g., `<think>` tags) for a clean reading experience.

### 4. **Stateful Threads & History**
Never lose context.
- **Persistence**: All messages, including intermediate agent thoughts, are saved to SQLite/PostgreSQL.
- **Deep Linking**: Share or return to specific conversations via URL (`/threads/:id`).
- **Sidebar Navigation**: Quickly access your recent simulations and chats.

### 5. **Clean Architecture & TDD**
Built for maintainability and scale.
- **Separation of Concerns**: Strict boundaries between Domain, Application, Infrastructure, and Presentation layers.
- **Test Coverage**: 150+ unit and integration tests ensuring stability.
- **Type Safety**: Fully typed Python (Pydantic) and TypeScript codebases.

---

## 🏗️ Architecture

The platform follows a strict **Clean Architecture** pattern to ensure modularity and testability.

### High-Level Data Flow

```mermaid
graph TD
    Client[React Frontend] <-->|WebSocket / HTTP| API[FastAPI Gateway]
    API -->|Command| UC[Use Cases]
    UC -->|Load| Repo[Repositories (SQLite)]
    UC -->|Execute| Engine[Workflow Engine]
    Engine -->|Stream| Queue[Event Queue]
    Queue -->|Push| API
    
    subgraph "Domain Layer"
    Entities[Agent, Message, Domain]
    end
    
    subgraph "Infrastructure"
    LLM[LLM Provider (OpenAI/Ollama)]
    DB[(Database)]
    end
    
    UC --> Entities
    Engine --> LLM
    Repo --> DB
```

### Streaming Mechanism
The system uses a side-channel queue to decouple LLM generation from HTTP response mechanisms, ensuring:
1. **Low Latency**: First token arrives in milliseconds.
2. **Resilience**: Long-running agent tasks don't time out HTTP requests.
3. **Observability**: Tool executions and state changes are streamed as distinct events.

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.11+**
- **Node.js 20+**
- **Docker & Docker Compose** (for production/containerized runs)
- **Ollama** (optional, for local LLM inference)

### Local Development

#### 1. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies (editable mode)
pip install -e .

# Run the API server with hot-reload
python -m uvicorn src.presentation.api.app:create_app --factory --reload --port 8000
```
*API docs available at: `http://localhost:8000/docs`*

#### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
*Access UI at: `http://localhost:5173`*

### Production (Docker)
Deploy the full stack (Nginx + React Static Build + FastAPI + Database) with one command.

```bash
# Build and start all services
docker compose up -d --build

# View logs
docker compose logs -f
```
*Access Application at: `http://localhost`*

---

## ⚙️ Configuration Guide

### Defining Agents
Create a YAML file in `backend/configs/agents/`.

**Example: `backend/configs/agents/storyteller.yaml`**
```yaml
id: storyteller
name: Creative Storyteller
role: "Expert Novelist"
model_name: "gpt-4o" # or "llama3"
temperature: 0.9
max_tokens: 2048
system_prompt: |
  You are an expert novelist. 
  Focus on vivid imagery and emotional depth.
skills: 
  - "narrative_design"
  - "character_development"
```

### Domains & Strategies
Domains group agents and define how they interact.

**Example: `backend/configs/domains/creative_writing.yaml`**
```yaml
id: creative_writing
name: "Creative Writing Studio"
description: "Collaborative story writing environment"
agents:
  - storyteller
  - editor
  - illustrator
strategy: "social_simulation" # or "orchestrator", "few_shot"
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | System health check |
| `GET` | `/api/v1/agents` | List all available agents |
| `POST` | `/api/v1/conversations` | Create a new conversation thread |
| `POST` | `/api/v1/conversations/{id}/message` | Send a message to a thread |
| `GET` | `/api/v1/conversations/{id}` | Get full conversation history |
| `GET` | `/api/v1/conversations` | List recent threads |

---

## ❓ Troubleshooting

**Q: frontend cannot connect to backend?**
- Ensure backend is running on port `8000`.
- Check CORS settings in `app.py`.
- If using Docker, ensure services share the same network.

**Q: Streaming is working but "Thinking" UI is hidden?**
- In v1.5+, "Thinking" mode is toggleable. Check the conversation settings in the UI to enable "Show Reasoning".

**Q: LLM returns garbage or artifacts?**
- Check `backend/configs/agents/*.yaml` temperature settings.
- Ensure your local Ollama model is loaded: `ollama list`.

---

## 📜 Changelog

### [1.6.0] - 2026-01-29
#### Added
- **Threads Persistence**: Deep linking (`/threads/:id`) and full history storage.
- **Recent Threads**: Sidebar navigation for past conversations.
- **Social Simulation v1.1**: Round-robin turn-taking and artifact cleaning.

### [1.5.0] - 2026-01-28
#### Added
- **Thinking Mode**: Toggleable/Collapsible reasoning UI.
- **Skill Badges**: Visual indicators for active agent skills.

### [1.4.0] - 2026-01-27
#### Added
- **Token Streaming**: Core architecture update for real-time feedback.

---

## 📄 License

MIT License - Copyright © 2026 Multi-Agent Team.
