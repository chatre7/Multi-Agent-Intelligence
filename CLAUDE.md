# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Testing
```bash
# Run all tests (Note: Some tests have import errors - see Known Issues below)
pytest

# Run specific test file
pytest testing/test_intent_classifier.py

# Run specific test function
pytest testing/test_intent_classifier.py::TestIntentClassifier::test_classification

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html

# Run tests in parallel
pytest -n auto

# Skip tests with import errors
pytest --ignore=test_auth_system.py --ignore=testing/test_auth_middleware.py --ignore=testing/test_health_monitor.py --ignore=testing/test_orchestration_comprehensive.py --ignore=testing/test_system_integration.py --ignore=testing/test_token_tracker.py --ignore=testing/test_user_management_api.py
```

### Running Applications
```bash
# Main Streamlit web interface
streamlit run app.py

# User Management API (FastAPI server on port 8000)
python apis/user_api.py

# Health monitoring system
python monitoring/health_monitor.py

# Demo scripts
python demos/demo.py
python demos/demo_agent_versioning.py

# System integration
python system_integration.py
```

### Code Quality
```bash
# Lint with ruff
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .

# Type checking with mypy
mypy .
```

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start Ollama service (required - must run in separate terminal)
ollama serve

# Pull required models
ollama pull nomic-embed-text
ollama pull gpt-oss:120b-cloud
```

## Architecture Overview

This is a multi-agent system built with LangGraph, LangChain, and Ollama, implementing Microsoft's multi-agent architecture best practices. **Note:** Core features are fully functional with 75% test pass rate. Advanced features need test refinement.

### Core Components

1. **Orchestrator (planner_agent_team_v3.py)**
   - Central coordinator using LangGraph StateGraph
   - Routes tasks to specialized agents via supervisor pattern
   - Implements human-in-the-loop approval for tool execution
   - Uses SqliteSaver for state persistence in `data/checkpoints.db`

2. **Intent Classifier (intent_classifier.py)**
   - Separate NLU/LLM cascade component for intelligent routing
   - Classifies user intents before agent selection
   - Implements fallback mechanisms for uncertain classifications

3. **Agent Registry (planner_agent_team_v3.py:AgentRegistry)**
   - Dynamic agent discovery and capability tracking
   - Integrates with version manager for agent lifecycle (dev → test → prod)
   - Stores agent metadata: version, description, author, status

4. **Memory System (planner_agent_team_v3.py:MemoryManager)**
   - Vector embeddings using ChromaDB stored in `./agent_brain` directory
   - Uses Ollama's nomic-embed-text model for embeddings
   - Provides save() and search() tools for agent knowledge retention

5. **Authentication & Authorization (auth_system.py)**
   - JWT-based authentication with bcrypt password hashing
   - RBAC with roles: ADMIN, DEVELOPER, OPERATOR, USER, AGENT, GUEST
   - Permission system for granular access control
   - Rate limiting and account lockout protection

6. **Health Monitoring (monitoring/health_monitor.py)**
   - FastAPI-based health check system
   - Periodic monitoring of all registered agents
   - Provides `/health`, `/health/agents/{name}`, `/status/all`, `/metrics` endpoints

7. **Token Tracking (monitoring/token_tracker.py)**
   - Real-time token consumption monitoring
   - Cost estimation and budget enforcement
   - Usage callbacks and session summaries
   - Exports to JSON in `data/` directory

8. **MCP Protocol (mcp_server.py, mcp_client.py)**
   - Model Context Protocol for standardized tool integration
   - Server registers tools, client executes them
   - Used for agent-to-tool communication

9. **Web Search Integration (search_provider.py, search_cache.py, search_cost_manager.py)**
   - DuckDuckGo-based search with caching
   - Budget management for search operations
   - Result filtering and formatting

10. **Database Management (database_manager.py)**
    - SQLite-based storage for structured data
    - Tables: users, conversations, agent_metrics, search_cache, session_data
    - Thread-safe connection management
    - Replaces older JSON-based storage

11. **Advanced Specialized Agents (advanced_agents.py)**
    - Domain-specific agents with expertise levels
    - Multi-agent orchestrator for complex task delegation
    - Performance metrics tracking per agent

### Agent Roles

The system uses a **supervisor pattern** with specialized agents:

- **Planner**: Breaks down complex tasks into actionable steps
- **Coder**: Writes Python code and saves to files
- **Critic**: Reviews code logic and quality before testing
- **Tester**: Runs scripts and validates output
- **Reviewer**: Final verification of results
- **Supervisor**: Orchestrates agent workflow and routing decisions

### Key Architectural Patterns

1. **State Management**
   - LangGraph's `AgentState` TypedDict with messages list and sender tracking
   - Messages use `reduce=operator.add` to append to conversation history
   - SqliteSaver provides persistent checkpointing across sessions

2. **Tool Definition**
   - All tools decorated with `@tool` decorator
   - Include detailed docstrings for LLM understanding
   - Tools registered with ToolNode in graph construction

3. **Human-in-the-Loop**
   - Interrupt workflow before tool execution
   - User approval required for code execution and file operations
   - Implemented via LangGraph's interrupt mechanism

4. **Version Management**
   - Agents transition through states: DEVELOPMENT → TESTING → PRODUCTION → RETIRED
   - State machine enforced by `agent_versioning.py`
   - Metadata stored in `data/agent_versions.json`

5. **Observability**
   - Prometheus metrics via `metrics.py`
   - Counters: agent_token_usage_total, agent_calls_total, tool_calls_total, agent_errors_total
   - Histogram: agent_latency_seconds

### Critical File Locations

- **Agent logic**: `planner_agent_team_v3.py` (core orchestrator)
- **Auth system**: `auth_system.py`, `auth/` directory for middleware and dependencies
- **APIs**: `apis/user_api.py`, `apis/users_router.py`
- **Database**: `data/checkpoints.db` (LangGraph state), `data/agent_system.db` (app data)
- **Vector store**: `./agent_brain/` (ChromaDB embeddings)
- **Config data**: `data/users.json`, `data/agent_versions.json`, `data/search_budget.json`, `data/search_cache.json`
- **Tests**: `testing/` directory (all test files prefixed with `test_`)
- **Logs**: `logs/` directory (agent_system.log, health_monitor.log, api_access.log)

## Code Style Requirements

These are strictly enforced in this codebase:

- **Type hints**: Required for all function parameters and return values
- **Docstrings**: Google/Numpy style with Parameters, Returns, and Raises sections
- **Naming**: snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE_CASE for constants
- **Function length**: Target max 50 lines
- **Import order**: stdlib → third-party → local (with blank lines between groups)
- **Error handling**: Use specific exception types, include descriptive messages
- **String formatting**: Use f-strings exclusively

### Testing Requirements

- All new code must have corresponding tests
- Test files in `testing/` directory, named `test_*.py`
- Use pytest fixtures and parametrize for efficiency
- Include integration tests for new features

### Test Status

**Current Status:** 297 tests collected, 223 passing (75.1% success rate)

**Test Results:**
- ✅ 223 PASSED (75.1%)
- ❌ 38 FAILED (12.8%)
- 💥 30 ERRORS (10.1%)
- ⏭️ 6 SKIPPED (2.0%)

**Components with 100% Pass Rate:**
- Intent Classifier (16/16)
- Agent Versioning (25/25)
- MCP Protocol (31/31)

**Components with High Pass Rate (>90%):**
- Auth System Core (27/29 = 93%)
- Metrics System (28/30 = 93%)

**Known Failing Tests:**
- Advanced Agents (21 tests) - Async/LLM mocking issues
- Database Manager (9 tests) - Module import issues
- Web Search (13 tests) - API mocking issues
- FastAPI Integration (7 tests) - Test client setup
- Orchestration (5 tests) - Agent coordination issues

**Root Causes:**
- Async/await patterns need better mocking
- External dependencies (LLM, APIs) need mocking
- Some integration tests need running services

## Common Development Workflows

### Adding a New Agent

1. Define agent in `planner_agent_team_v3.py` or `advanced_agents.py`
2. Create system prompt with role and capabilities
3. Register with AgentRegistry
4. Add to supervisor routing logic
5. Create version entry via version_manager
6. Write comprehensive tests in `testing/test_agents_comprehensive.py`

### Adding a New Tool

1. Define tool function with `@tool` decorator in appropriate module
2. Add detailed docstring explaining purpose and parameters
3. Register with MCP server in `mcp_server.py`
4. Add tool to agent's available tools list
5. Test tool execution in isolation

### Adding a New API Endpoint

1. Define route in `apis/users_router.py` or create new router
2. Use auth dependencies from `auth/auth_dependencies.py` for RBAC
3. Add Pydantic models for request/response in `auth/user_models.py`
4. Implement business logic with proper error handling
5. Add comprehensive tests in `testing/test_user_api.py`
6. Update OpenAPI docs if needed

### Modifying Authentication/Authorization

1. Update roles in `auth_system.py:UserRole` if adding new role
2. Define permissions in `auth_system.py:Permission`
3. Update RBAC mappings in `RBACManager._init_role_permissions()`
4. Update auth middleware in `auth/auth_middleware.py`
5. Test with all existing roles in `testing/test_auth_system.py`

## Important Notes

### LangGraph Specifics

- **Node names**: Cannot contain ':' (reserved character) - use '_' instead
- **State updates**: Always return dict with updated state keys
- **Checkpointing**: Requires thread_id in config: `{"configurable": {"thread_id": "user-session-123"}}`
- **Conditional edges**: Use functions that return agent name or "END"

### Ollama Models

- Default LLM: `gpt-oss:120b-cloud`
- Embedding model: `nomic-embed-text`
- Models must be pulled before use: `ollama pull <model-name>`
- Ollama service must be running: `ollama serve`

### Data Persistence

- LangGraph checkpoints: `data/checkpoints.db` (SQLite)
- Application data: `data/agent_system.db` (SQLite)
- Vector embeddings: `./agent_brain/` (ChromaDB)
- JSON configs: `data/*.json` (legacy, being migrated to SQLite)

### Security Considerations

- JWT tokens stored in memory, never logged
- Passwords hashed with bcrypt (12 rounds)
- Rate limiting enabled by default (100 req/min)
- Input validation on all API endpoints
- Prompt injection prevention in intent classifier
- SQL injection protection via parameterized queries

### SpecKit Integration

This project uses SpecKit for spec-driven development:
- Constitution: `.specify/memory/constitution.md`
- Specs: `.specify/specs/` directory
- Templates: `.specify/templates/` directory
- Commands available but use sparingly in automation

## Troubleshooting

### Ollama Connection Issues
- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Check models are pulled: `ollama list`
- Restart service: `ollama serve`

### Database Lock Issues
- Ensure proper connection management with context managers
- Check no hanging connections in `database_manager.py`
- Delete `data/checkpoints.db` to reset state (loses session history)

### Memory/ChromaDB Issues
- Clear vector store: `rm -rf agent_brain/`
- Check disk space in `./agent_brain/` directory
- Verify nomic-embed-text model is available

### Test Failures
- Run with verbose: `pytest -v`
- Check specific test: `pytest testing/test_file.py::test_name -s`
- Clear pytest cache: `pytest --cache-clear`

## Dependencies

Core libraries:
- **langchain**: 1.2.6 (core LangChain framework)
- **langgraph**: >=0.2.0 (state graph orchestration)
- **langchain-ollama**: 1.0.1 (Ollama integration)
- **langchain-chroma**: 1.1.0 (vector storage)
- **chromadb**: 1.4.1 (vector database)
- **ollama**: 0.6.1 (LLM runtime)
- **streamlit**: 1.41.1 (web interface)
- **fastapi**: >=0.115.0 (API server)
- **PyJWT**: >=2.0.0 (authentication)
- **prometheus-client**: >=0.20.0 (metrics)

See `requirements.txt` for complete list.
