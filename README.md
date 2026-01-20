# Multi-Agent Intelligence Platform

A production-ready multi-agent system built with LangGraph, LangChain, and Ollama, implementing Microsoft's multi-agent architecture best practices including RBAC Authentication, Agent Versioning, MCP (Model Context Protocol), and comprehensive observability with 100% test coverage (198/198 tests passing).

## Features

- **Multi-Agent Architecture**: Orchestrated team of specialized agents (Planner, Coder, Critic, Tester, Reviewer)
- **Intent Classifier**: Separate NLU/LLM cascade component for intelligent routing
- **Memory System**: Long-term knowledge storage using ChromaDB vector embeddings
- **Agent Registry**: Dynamic agent discovery and capability tracking
- **Health Monitoring**: FastAPI-based health check system with periodic monitoring
- **Token Tracking**: Real-time consumption monitoring with cost estimation
- **RBAC Authentication**: JWT-based authentication with role-based access control
- **Agent Versioning**: State machine for dev → test → prod lifecycle management
- **MCP Protocol**: Model Context Protocol for standardized tool integration
- **Observability**: Prometheus metrics integration for performance monitoring
- **Human-in-the-Loop**: Approval workflow for tool execution
- **Persistent State**: SQLite checkpointing for session continuity
- **Web Interface**: Streamlit-based UI for agent interaction

## Architecture

```
User Application (Streamlit)
       ↓
   Orchestrator (Supervisor)
       ↓
    Intent Classifier ← NEW
       ↓
   Agent Registry → Specialized Agents
       ↓         ↓         ↓
    Memory System (ChromaDB)  Health Monitor ← NEW  MCP Server ← NEW
       ↓         ↓         ↓
    Token Tracker ← NEW  Prometheus Metrics ← NEW  MCP Client ← NEW
```

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Ollama Setup

```bash
# Pull required models
ollama pull nomic-embed-text
ollama pull gpt-oss:120b-cloud
```

### Run Application

```bash
# Start Streamlit app (Main interface)
streamlit run app.py

# Start Health Monitor API (Optional)
python health_monitor.py

# Start Metrics Server (Optional)
python metrics.py

# Run Integration Tests
python system_integration.py
```

## Agent Roles

| Agent | Description |
|-------|-------------|
| **Planner** | Breaks down complex tasks into actionable steps |
| **Coder** | Writes Python code and saves to files |
| **Critic** | Reviews code logic and quality before testing |
| **Tester** | Runs scripts and validates output |
| **Reviewer** | Final verification of results |
| **Supervisor** | Orchestrates agent workflow and routing |

## Development

### Testing

```bash
# Install test dependencies
pip install prometheus-client

# Run all tests (113 tests)
pytest

# Run specific test
pytest test_intent_classifier.py::TestIntentClassifier::test_initialization_default_config

# With coverage (100% coverage achieved)
pytest --cov=. --cov-report=html

# Run specific component tests
pytest test_intent_classifier.py test_health_monitor.py
```

### Linting & Formatting

```bash
# Check code
ruff check .

# Auto-fix
ruff check --fix .

# Format code
ruff format .

# Type checking
mypy .
```

## Project Structure

```
.
├── app.py                      # Streamlit web interface
├── planner_agent_team_v3.py   # Core agent system with orchestrator
├── intent_classifier.py         # Separate intent classification component
├── health_monitor.py           # Health check system with FastAPI
├── metrics.py                 # Prometheus metrics integration
├── token_tracker.py           # Token consumption and cost tracking
├── agent_versioning.py        # Agent versioning state machine
├── auth_system.py             # RBAC authentication system
├── auth_middleware.py         # FastAPI auth middleware
├── mcp_server.py             # MCP server for tool management
├── mcp_client.py              # MCP client for tool invocation
├── system_integration.py       # Main integration module
├── architecture.py            # Architecture documentation
├── agent_brain/               # Vector embeddings storage
├── checkpoints.db             # LangGraph state persistence
├── AGENTS.md                  # Agent development guidelines
├── MICROSOFT_COMPLIANCE.md    # Microsoft architecture compliance check
├── TESTING.md                 # Test suite documentation
├── TEST_RESULTS.md            # Unit test results summary
├── requirements.txt            # Python dependencies
├── test_*.py                  # Unit test files (198 tests, 100% pass)
└── .gitignore                 # Git ignore rules
```

## Test Coverage Results

| Component | Tests | Coverage |
|-----------|-------|----------|
| Intent Classifier | 16/16 | ✅ 100% |
| Health Monitor | 22/22 | ✅ 100% |
| Metrics System | 30/30 | ✅ 100% |
| Token Tracker | 25/25 | ✅ 100% |
| Agent Versioning | 25/25 | ✅ 100% |
| MCP Protocol | 31/31 | ✅ 100% |
| RBAC/Authentication | 29/29 | ✅ 100% |
| System Integration | 20/20 | ✅ 100% |
| **Total** | **198/198** | **100%** |

All tests pass with comprehensive coverage including edge cases and error handling.

## Best Practices

See [AGENTS.md](AGENTS.md) for comprehensive guidelines on:
- Code style and conventions
- Agent development patterns
- Testing strategies
- Security and resilience
- Architecture patterns

## Observability & Monitoring

### Health Monitor API

```bash
# Start health monitor server
python health_monitor.py
```

Available endpoints:
- `GET /health` - Overall system health
- `GET /health/agents/{name}` - Specific agent health
- `GET /status/all` - Current agent statuses
- `GET /metrics` - System metrics summary

### Metrics (Prometheus)

```bash
# Start metrics server
python metrics.py
```

Metrics exposed at `http://localhost:8000/metrics`:
- `agent_token_usage_total` - Token consumption per agent
- `agent_calls_total` - Agent invocation count
- `agent_latency_seconds` - Execution time histogram
- `tool_calls_total` - Tool invocation count
- `agent_errors_total` - Error rate tracking

### Token Tracking

```python
from token_tracker import get_token_tracker

tracker = get_token_tracker(daily_cost_limit=10.0)
tracker.register_usage_callback(lambda record: print(f"Used {record.total_tokens} tokens"))

# Get usage summary
summary = tracker.get_session_summary()
print(f"Total cost: ${summary['total_cost']:.2f}")
```

### MCP (Model Context Protocol)

```bash
# Access MCP tools programmatically
from system_integration import get_system

system = get_system()
tools = system.get_mcp_tools()
print(f"Available tools: {len(tools)}")

# Invoke a tool
import asyncio
async def use_tool():
    result = await system.invoke_mcp_tool("save_file", {
        "filename": "example.py",
        "code": "print('Hello, MCP!')"
    })
    print(f"Tool result: {result}")

asyncio.run(use_tool())
```

MCP provides standardized tool interface with:
- Tool discovery and metadata
- Schema validation
- Secure invocation
- Execution tracking
- Error handling

## Security

- JWT-based authentication with secure token management
- Role-based access control (RBAC) with granular permissions
- Input validation and sanitization
- Prompt injection prevention
- Audit logging and monitoring
- Rate limiting and abuse detection
- Token consumption monitoring
- Account lockout protection

**Roles & Permissions:**
- **Admin**: Full system access, user management
- **Developer**: Agent creation, tool access, monitoring
- **Operator**: Agent deployment, system monitoring
- **User**: Basic agent interaction
- **Agent**: Inter-agent communication

## License

MIT
