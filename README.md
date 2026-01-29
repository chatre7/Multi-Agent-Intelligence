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

### 4. **Threads as Pull Requests**
Review simulations as if they were code.
- **PR-style Workflow**: Threads have statuses: `Open`, `Review Requested`, `Merged`, and `Closed`.
- **Merge Action**: "Merging" a thread automatically generates a conversation summary and uploads it to the Knowledge Base.
- **Collaborative Review**: Highlighted timeline of agent interactions for easy auditing.

### 5. **Eternal Agent Recall (Knowledge Base)**
Agents learn from past conversations.
- **ChromaDB Integration**: Merged threads are vectorized and stored for semantic retrieval.
- **Knowledge Capture**: Transform casual brainstorming into structured team intelligence.
- **RAG-Ready**: Future agents can query the Knowledge Base to reference past decisions.

### 6. **Clean Architecture & TDD**
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
    UC -->|Query/Add| KB[Knowledge Base - Chroma]
    UC -->|Execute| Engine[Workflow Engine]
    Engine -->|Stream| Queue[Event Queue]
    Queue -->|Push| API
    
    subgraph "Domain Layer"
    Entities[Agent, Message, Domain, Conversation]
    end
    
    subgraph "Infrastructure"
    LLM[LLM Provider (OpenAI/Ollama)]
    DB[(SQLite/PG)]
    VecDB[(ChromaDB)]
    end
    
    UC --> Entities
    Engine --> LLM
    Repo --> DB
    KB --> VecDB
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
- **Docker & Docker Compose**
- **ChromaDB** (included in Docker stack)

### Local Development

#### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m uvicorn src.presentation.api.app:create_app --factory --reload --port 8000
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Production (Docker)
```bash
docker compose up -d --build
```

---

## ⚙️ Configuration Guide

### Defining Agents
Create a YAML file in `backend/configs/agents/`.

**Example: `storyteller.yaml`**
```yaml
id: storyteller
name: Creative Storyteller
role: "Expert Novelist"
model_name: "gpt-4o"
temperature: 0.9
skills: ["narrative_design", "character_development"]
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
| `GET` | `/api/v1/conversations` | List recent threads |
| `POST` | `/api/v1/conversations` | Start a new thread |
| `PATCH` | `/api/v1/conversations/{id}/status` | Update thread status (open/merged/etc) |
| `POST` | `/api/v1/conversations/{id}/merge` | Process thread and add to Knowledge Base |
| `GET` | `/api/v1/knowledge` | List documents in the KB |

---

## ❓ Troubleshooting

**Q: frontend cannot connect to backend?**
- Ensure backend is running on port `8000`.
- Check `mai-nginx` logs if using Docker.

**Q: Merging a thread fails?**
- Ensure the `summarizer` agent is configured in `brainstorming.yaml`.
- Check if ChromaDB container is healthy.

---

## 📜 Changelog

### [1.7.0] - 2026-01-30
#### Added
- **Threads as Pull Requests**: Full workflow support with statuses and "Merge" functionality.
- **Knowledge Base (ChromaDB)**: Automatic capture of merged threads into vector storage.
- **UI Refinement**: Harmonized Shadcn-inspired design across Threads and Admin pages.
- **Lazy Loading**: Route-based bundle optimization for the frontend.

### [1.6.0] - 2026-01-29
#### Added
- **Threads Persistence**: Deep linking (`/threads/:id`) and full history storage.
- **Recent Threads**: Sidebar navigation for past conversations.

---

## 📄 License

MIT License - Copyright © 2026 Multi-Agent Team.
