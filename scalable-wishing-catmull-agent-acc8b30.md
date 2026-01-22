# Clean Architecture Plan: Configuration-Driven Multi-Agent Platform

## Executive Summary

Transform the existing Multi-Agent Intelligence system from a hard-coded Python/Streamlit application into a configuration-driven, zero-code domain extension platform with a modern React frontend and clean architecture backend.

---

## 1. Current System Analysis

### 1.1 Existing Architecture Components

| Component | File | Purpose |
|-----------|------|---------|
| Orchestrator | `planner_agent_team_v3.py` | LangGraph StateGraph with supervisor pattern |
| Specialized Agents | `advanced_agents.py` | Domain-specific agents (CodeReview, Research, etc.) |
| Auth System | `auth_system.py` | JWT + RBAC with bcrypt |
| Database | `database_manager.py` | SQLite with thread-safe connections |
| API | `apis/user_api.py`, `apis/users_router.py` | FastAPI REST endpoints |
| MCP Protocol | `mcp_server.py`, `mcp_client.py` | Tool registration and invocation |
| Versioning | `agent_versioning.py` | Agent lifecycle state machine |
| Metrics | `metrics.py` | Prometheus metrics collection |
| Health Monitor | `monitoring/health_monitor.py` | FastAPI health endpoints |
| Intent Classifier | `intent_classifier.py` | NLU/LLM cascade routing |
| UI | `app.py` | Streamlit web interface |

### 1.2 Current Data Storage

- **SQLite**: `data/agent_system.db`, `data/checkpoints.db`
- **JSON Files**: `data/users.json`, `data/agent_versions.json`, `data/search_*.json`
- **Vector Store**: `./agent_brain/` (ChromaDB)

### 1.3 Key Patterns to Preserve

1. **Supervisor Pattern**: Central coordinator routing to specialized agents
2. **State Machine**: Agent lifecycle (dev -> test -> prod)
3. **Human-in-the-Loop**: Tool execution approval workflow
4. **MCP Protocol**: Standardized tool interface
5. **RBAC**: Role-based access control with permissions

---

## 2. Target Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React + Vite)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Chat UI   │  │   Domain    │  │   Agent     │  │    Admin Panel      │ │
│  │  (shadcn)   │  │  Browser    │  │  Explorer   │  │  (Metrics/Users)    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                              │ WebSocket + REST │                            │
└──────────────────────────────┼──────────────────┼────────────────────────────┘
                               │                  │
┌──────────────────────────────┼──────────────────┼────────────────────────────┐
│                              ▼                  ▼                            │
│                         BACKEND (FastAPI + Clean Architecture)               │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        PRESENTATION LAYER                               ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ ││
│  │  │ REST API     │  │ WebSocket    │  │ GraphQL      │  │ Auth        │ ││
│  │  │ Controllers  │  │ Handlers     │  │ (Optional)   │  │ Middleware  │ ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        APPLICATION LAYER                                ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ ││
│  │  │ Use Cases    │  │ DTOs         │  │ Event        │  │ Config      │ ││
│  │  │ (Services)   │  │ (Schemas)    │  │ Handlers     │  │ Loader      │ ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                          DOMAIN LAYER                                   ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ ││
│  │  │ Entities     │  │ Value        │  │ Domain       │  │ Repository  │ ││
│  │  │ (Agent,Tool) │  │ Objects      │  │ Services     │  │ Interfaces  │ ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                       INFRASTRUCTURE LAYER                              ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ ││
│  │  │ Repositories │  │ LangGraph    │  │ External     │  │ Config      │ ││
│  │  │ (SQLite)     │  │ Adapter      │  │ Services     │  │ Sync        │ ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
    ┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
    │  YAML Configs   │ │   SQLite    │ │   ChromaDB      │
    │  (Domains/      │ │  (Runtime   │ │  (Vector        │
    │   Agents/Tools) │ │   State)    │ │   Embeddings)   │
    └─────────────────┘ └─────────────┘ └─────────────────┘
```

---

## 3. Backend Architecture (Python/FastAPI)

### 3.1 Complete Folder Structure

```
backend/
├── src/
│   ├── __init__.py
│   │
│   ├── domain/                          # DOMAIN LAYER (Core Business Logic)
│   │   ├── __init__.py
│   │   │
│   │   ├── entities/                    # Domain Entities
│   │   │   ├── __init__.py
│   │   │   ├── agent.py                 # Agent entity
│   │   │   ├── domain_config.py         # Domain configuration entity
│   │   │   ├── tool.py                  # Tool entity
│   │   │   ├── user.py                  # User entity
│   │   │   ├── conversation.py          # Conversation entity
│   │   │   ├── message.py               # Message entity
│   │   │   └── workflow.py              # Workflow entity
│   │   │
│   │   ├── value_objects/               # Value Objects (Immutable)
│   │   │   ├── __init__.py
│   │   │   ├── agent_state.py           # AgentState enum (dev/test/prod)
│   │   │   ├── agent_id.py              # AgentId value object
│   │   │   ├── domain_id.py             # DomainId value object
│   │   │   ├── user_role.py             # UserRole enum
│   │   │   ├── permission.py            # Permission enum
│   │   │   └── version.py               # SemanticVersion value object
│   │   │
│   │   ├── services/                    # Domain Services
│   │   │   ├── __init__.py
│   │   │   ├── agent_orchestration.py   # Core orchestration logic
│   │   │   ├── intent_classification.py # Intent routing logic
│   │   │   ├── tool_execution.py        # Tool execution logic
│   │   │   └── version_management.py    # Version state machine
│   │   │
│   │   ├── events/                      # Domain Events
│   │   │   ├── __init__.py
│   │   │   ├── agent_events.py          # AgentCreated, AgentPromoted, etc.
│   │   │   ├── conversation_events.py   # MessageReceived, ConversationEnded
│   │   │   └── tool_events.py           # ToolExecuted, ToolApprovalRequired
│   │   │
│   │   └── repositories/                # Repository Interfaces (Ports)
│   │       ├── __init__.py
│   │       ├── agent_repository.py      # IAgentRepository
│   │       ├── domain_repository.py     # IDomainRepository
│   │       ├── tool_repository.py       # IToolRepository
│   │       ├── user_repository.py       # IUserRepository
│   │       ├── conversation_repository.py
│   │       └── config_repository.py     # IConfigRepository
│   │
│   ├── application/                     # APPLICATION LAYER (Use Cases)
│   │   ├── __init__.py
│   │   │
│   │   ├── use_cases/                   # Use Cases (Application Services)
│   │   │   ├── __init__.py
│   │   │   │
│   │   │   ├── agents/                  # Agent Management Use Cases
│   │   │   │   ├── __init__.py
│   │   │   │   ├── create_agent.py
│   │   │   │   ├── update_agent.py
│   │   │   │   ├── promote_agent.py
│   │   │   │   ├── list_agents.py
│   │   │   │   └── get_agent_metrics.py
│   │   │   │
│   │   │   ├── domains/                 # Domain Management Use Cases
│   │   │   │   ├── __init__.py
│   │   │   │   ├── create_domain.py
│   │   │   │   ├── update_domain.py
│   │   │   │   ├── list_domains.py
│   │   │   │   └── sync_domain_config.py
│   │   │   │
│   │   │   ├── conversations/           # Conversation Use Cases
│   │   │   │   ├── __init__.py
│   │   │   │   ├── start_conversation.py
│   │   │   │   ├── send_message.py
│   │   │   │   ├── approve_tool.py
│   │   │   │   ├── reject_tool.py
│   │   │   │   └── get_history.py
│   │   │   │
│   │   │   ├── tools/                   # Tool Management Use Cases
│   │   │   │   ├── __init__.py
│   │   │   │   ├── register_tool.py
│   │   │   │   ├── execute_tool.py
│   │   │   │   └── list_tools.py
│   │   │   │
│   │   │   ├── auth/                    # Authentication Use Cases
│   │   │   │   ├── __init__.py
│   │   │   │   ├── login.py
│   │   │   │   ├── logout.py
│   │   │   │   ├── refresh_token.py
│   │   │   │   └── change_password.py
│   │   │   │
│   │   │   └── users/                   # User Management Use Cases
│   │   │       ├── __init__.py
│   │   │       ├── create_user.py
│   │   │       ├── update_user.py
│   │   │       ├── delete_user.py
│   │   │       └── list_users.py
│   │   │
│   │   ├── dto/                         # Data Transfer Objects
│   │   │   ├── __init__.py
│   │   │   ├── agent_dto.py
│   │   │   ├── domain_dto.py
│   │   │   ├── tool_dto.py
│   │   │   ├── user_dto.py
│   │   │   ├── conversation_dto.py
│   │   │   ├── message_dto.py
│   │   │   └── config_dto.py
│   │   │
│   │   ├── interfaces/                  # Application Interfaces
│   │   │   ├── __init__.py
│   │   │   ├── config_loader.py         # IConfigLoader
│   │   │   ├── event_publisher.py       # IEventPublisher
│   │   │   └── streaming_service.py     # IStreamingService
│   │   │
│   │   └── event_handlers/              # Event Handlers
│   │       ├── __init__.py
│   │       ├── agent_event_handlers.py
│   │       ├── conversation_event_handlers.py
│   │       └── metrics_event_handlers.py
│   │
│   ├── infrastructure/                  # INFRASTRUCTURE LAYER (Adapters)
│   │   ├── __init__.py
│   │   │
│   │   ├── persistence/                 # Database Implementations
│   │   │   ├── __init__.py
│   │   │   ├── sqlite/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── database.py          # SQLite connection manager
│   │   │   │   ├── agent_repository.py  # SQLite AgentRepository
│   │   │   │   ├── domain_repository.py
│   │   │   │   ├── tool_repository.py
│   │   │   │   ├── user_repository.py
│   │   │   │   ├── conversation_repository.py
│   │   │   │   └── models.py            # SQLAlchemy models
│   │   │   │
│   │   │   └── chromadb/
│   │   │       ├── __init__.py
│   │   │       └── vector_repository.py # ChromaDB vector storage
│   │   │
│   │   ├── config/                      # Configuration Management
│   │   │   ├── __init__.py
│   │   │   ├── yaml_loader.py           # YAML config loader
│   │   │   ├── config_validator.py      # Pydantic/JSON Schema validation
│   │   │   ├── config_sync.py           # YAML to SQLite sync
│   │   │   ├── hot_reload.py            # File watcher for hot reload
│   │   │   └── schemas/
│   │   │       ├── __init__.py
│   │   │       ├── domain_schema.py
│   │   │       ├── agent_schema.py
│   │   │       └── tool_schema.py
│   │   │
│   │   ├── langgraph/                   # LangGraph Integration
│   │   │   ├── __init__.py
│   │   │   ├── graph_builder.py         # Dynamic graph construction
│   │   │   ├── node_factory.py          # Agent node creation
│   │   │   ├── state_manager.py         # State persistence adapter
│   │   │   ├── streaming_adapter.py     # WebSocket streaming
│   │   │   └── checkpointer.py          # Custom checkpointer
│   │   │
│   │   ├── llm/                         # LLM Integration
│   │   │   ├── __init__.py
│   │   │   ├── ollama_adapter.py        # Ollama LLM adapter
│   │   │   ├── openai_adapter.py        # OpenAI adapter (optional)
│   │   │   └── llm_factory.py           # LLM factory
│   │   │
│   │   ├── mcp/                         # MCP Protocol
│   │   │   ├── __init__.py
│   │   │   ├── mcp_server.py            # Tool registration
│   │   │   ├── mcp_client.py            # Tool invocation
│   │   │   └── tool_registry.py         # Dynamic tool registry
│   │   │
│   │   ├── auth/                        # Authentication Infrastructure
│   │   │   ├── __init__.py
│   │   │   ├── jwt_service.py           # JWT token management
│   │   │   ├── password_service.py      # Bcrypt password hashing
│   │   │   └── rbac_service.py          # RBAC implementation
│   │   │
│   │   ├── messaging/                   # Event/Message Infrastructure
│   │   │   ├── __init__.py
│   │   │   ├── event_bus.py             # In-memory event bus
│   │   │   ├── websocket_manager.py     # WebSocket connection manager
│   │   │   └── redis_adapter.py         # Redis pub/sub (optional)
│   │   │
│   │   └── external/                    # External Service Adapters
│   │       ├── __init__.py
│   │       ├── search_service.py        # Web search integration
│   │       └── metrics_service.py       # Prometheus metrics
│   │
│   └── presentation/                    # PRESENTATION LAYER (API)
│       ├── __init__.py
│       │
│       ├── api/                         # REST API
│       │   ├── __init__.py
│       │   ├── main.py                  # FastAPI app creation
│       │   │
│       │   ├── v1/                      # API v1 Routes
│       │   │   ├── __init__.py
│       │   │   ├── agents.py            # /api/v1/agents
│       │   │   ├── domains.py           # /api/v1/domains
│       │   │   ├── tools.py             # /api/v1/tools
│       │   │   ├── conversations.py     # /api/v1/conversations
│       │   │   ├── users.py             # /api/v1/users
│       │   │   ├── auth.py              # /api/v1/auth
│       │   │   ├── config.py            # /api/v1/config
│       │   │   ├── health.py            # /api/v1/health
│       │   │   └── metrics.py           # /api/v1/metrics
│       │   │
│       │   ├── middleware/
│       │   │   ├── __init__.py
│       │   │   ├── auth_middleware.py   # JWT authentication
│       │   │   ├── cors_middleware.py   # CORS handling
│       │   │   ├── rate_limit.py        # Rate limiting
│       │   │   └── error_handler.py     # Global error handling
│       │   │
│       │   └── dependencies/
│       │       ├── __init__.py
│       │       ├── auth.py              # Auth dependencies
│       │       ├── database.py          # DB session dependencies
│       │       └── services.py          # Service dependencies
│       │
│       └── websocket/                   # WebSocket API
│           ├── __init__.py
│           ├── handlers.py              # WebSocket route handlers
│           ├── protocol.py              # Message protocol definitions
│           └── connection_manager.py    # Connection lifecycle
│
├── configs/                             # Configuration Files
│   ├── domains/                         # Domain Configurations
│   │   ├── software_development.yaml
│   │   ├── data_analysis.yaml
│   │   ├── research.yaml
│   │   └── documentation.yaml
│   │
│   ├── agents/                          # Agent Configurations
│   │   ├── core/
│   │   │   ├── planner.yaml
│   │   │   ├── coder.yaml
│   │   │   ├── critic.yaml
│   │   │   ├── tester.yaml
│   │   │   └── reviewer.yaml
│   │   │
│   │   └── specialized/
│   │       ├── code_review.yaml
│   │       ├── research.yaml
│   │       ├── data_analysis.yaml
│   │       ├── documentation.yaml
│   │       └── devops.yaml
│   │
│   ├── tools/                           # Tool Configurations
│   │   ├── file_operations.yaml
│   │   ├── code_execution.yaml
│   │   ├── web_search.yaml
│   │   └── memory.yaml
│   │
│   └── system/                          # System Configuration
│       ├── app.yaml                     # Application settings
│       ├── auth.yaml                    # Auth settings
│       ├── llm.yaml                     # LLM provider settings
│       └── logging.yaml                 # Logging configuration
│
├── tests/                               # Test Suite
│   ├── __init__.py
│   ├── conftest.py                      # Pytest fixtures
│   │
│   ├── unit/                            # Unit Tests
│   │   ├── domain/
│   │   │   ├── test_entities.py
│   │   │   ├── test_value_objects.py
│   │   │   └── test_domain_services.py
│   │   │
│   │   ├── application/
│   │   │   ├── test_use_cases.py
│   │   │   └── test_event_handlers.py
│   │   │
│   │   └── infrastructure/
│   │       ├── test_repositories.py
│   │       ├── test_config_loader.py
│   │       └── test_langgraph_adapter.py
│   │
│   ├── integration/                     # Integration Tests
│   │   ├── test_api_endpoints.py
│   │   ├── test_websocket.py
│   │   ├── test_config_sync.py
│   │   └── test_agent_workflow.py
│   │
│   └── e2e/                             # End-to-End Tests
│       ├── test_conversation_flow.py
│       └── test_domain_creation.py
│
├── migrations/                          # Database Migrations
│   └── versions/
│
├── scripts/                             # Utility Scripts
│   ├── migrate_from_legacy.py           # Migration from current system
│   ├── seed_data.py                     # Initial data seeding
│   └── validate_configs.py              # Config validation script
│
├── pyproject.toml                       # Project configuration
├── requirements.txt                     # Dependencies
├── Dockerfile                           # Container configuration
└── docker-compose.yml                   # Multi-service setup
```

### 3.2 Key Domain Entities

```python
# backend/src/domain/entities/agent.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..value_objects.agent_state import AgentState
from ..value_objects.agent_id import AgentId
from ..value_objects.version import SemanticVersion


@dataclass
class Agent:
    """Core Agent Entity - represents a configurable AI agent."""
    
    id: AgentId
    name: str
    domain_id: str
    description: str
    version: SemanticVersion
    state: AgentState
    
    # Configuration
    system_prompt: str
    capabilities: List[str]
    tools: List[str]  # Tool IDs
    
    # LLM Settings
    model_name: str
    temperature: float = 0.0
    max_tokens: int = 4096
    timeout_seconds: float = 120.0
    
    # Routing
    keywords: List[str] = field(default_factory=list)
    priority: int = 0
    
    # Metadata
    author: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Performance
    test_results: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def can_handle(self, intent: str, keywords: List[str]) -> float:
        """Calculate confidence score for handling a request."""
        score = 0.0
        for kw in keywords:
            if kw.lower() in [k.lower() for k in self.keywords]:
                score += 0.2
        return min(score, 1.0)
    
    def promote(self, target_state: AgentState) -> None:
        """Promote agent to target state with validation."""
        valid_transitions = {
            AgentState.DEVELOPMENT: [AgentState.TESTING],
            AgentState.TESTING: [AgentState.PRODUCTION, AgentState.DEVELOPMENT],
            AgentState.PRODUCTION: [AgentState.DEPRECATED],
            AgentState.DEPRECATED: [AgentState.ARCHIVED],
        }
        
        if target_state not in valid_transitions.get(self.state, []):
            raise ValueError(f"Invalid transition from {self.state} to {target_state}")
        
        self.state = target_state
        self.updated_at = datetime.utcnow()
```

```python
# backend/src/domain/entities/domain_config.py
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime


@dataclass
class DomainConfig:
    """Domain Configuration Entity - defines a business domain."""
    
    id: str
    name: str
    description: str
    
    # Agent Configuration
    agents: List[str]  # Agent IDs in this domain
    default_agent: str  # Default agent for routing
    
    # Workflow
    workflow_type: str  # "supervisor", "sequential", "parallel"
    max_iterations: int = 10
    
    # Routing Rules
    routing_rules: List[Dict[str, Any]] = field(default_factory=list)
    fallback_agent: str = "planner"
    
    # Permissions
    allowed_roles: List[str] = field(default_factory=lambda: ["user", "developer", "admin"])
    
    # Metadata
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
```

```python
# backend/src/domain/entities/tool.py
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime


@dataclass
class Tool:
    """Tool Entity - represents an executable tool."""
    
    id: str
    name: str
    description: str
    
    # Schema
    parameters_schema: Dict[str, Any]  # JSON Schema
    returns_schema: Dict[str, Any]
    
    # Execution
    handler_path: str  # Python path to handler function
    timeout_seconds: float = 30.0
    max_retries: int = 3
    
    # Security
    requires_approval: bool = False
    allowed_roles: List[str] = field(default_factory=lambda: ["developer", "admin"])
    
    # Categorization
    tags: List[str] = field(default_factory=list)
    domain: Optional[str] = None
    
    # Metadata
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
```

### 3.3 Repository Interfaces (Ports)

```python
# backend/src/domain/repositories/agent_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.agent import Agent
from ..value_objects.agent_id import AgentId
from ..value_objects.agent_state import AgentState


class IAgentRepository(ABC):
    """Port for Agent persistence operations."""
    
    @abstractmethod
    async def save(self, agent: Agent) -> Agent:
        """Persist an agent."""
        pass
    
    @abstractmethod
    async def find_by_id(self, agent_id: AgentId) -> Optional[Agent]:
        """Find agent by ID."""
        pass
    
    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Agent]:
        """Find agent by name."""
        pass
    
    @abstractmethod
    async def find_by_domain(self, domain_id: str) -> List[Agent]:
        """Find all agents in a domain."""
        pass
    
    @abstractmethod
    async def find_by_state(self, state: AgentState) -> List[Agent]:
        """Find agents by lifecycle state."""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Agent]:
        """Get all agents."""
        pass
    
    @abstractmethod
    async def delete(self, agent_id: AgentId) -> bool:
        """Delete an agent."""
        pass
    
    @abstractmethod
    async def find_by_keywords(self, keywords: List[str]) -> List[Agent]:
        """Find agents matching keywords."""
        pass
```

### 3.4 Use Case Example

```python
# backend/src/application/use_cases/conversations/send_message.py
from dataclasses import dataclass
from typing import AsyncGenerator, Optional
from ....domain.entities.conversation import Conversation
from ....domain.entities.message import Message
from ....domain.repositories.conversation_repository import IConversationRepository
from ....domain.repositories.agent_repository import IAgentRepository
from ....application.interfaces.streaming_service import IStreamingService
from ....application.dto.message_dto import MessageDTO, StreamChunkDTO


@dataclass
class SendMessageInput:
    conversation_id: str
    content: str
    user_id: str


@dataclass
class SendMessageOutput:
    message_id: str
    conversation_id: str
    stream: AsyncGenerator[StreamChunkDTO, None]


class SendMessageUseCase:
    """Use case for sending a message and streaming agent response."""
    
    def __init__(
        self,
        conversation_repo: IConversationRepository,
        agent_repo: IAgentRepository,
        streaming_service: IStreamingService,
    ):
        self._conversation_repo = conversation_repo
        self._agent_repo = agent_repo
        self._streaming_service = streaming_service
    
    async def execute(self, input_data: SendMessageInput) -> SendMessageOutput:
        """Execute the send message use case."""
        # 1. Get or create conversation
        conversation = await self._conversation_repo.find_by_id(
            input_data.conversation_id
        )
        if not conversation:
            raise ValueError("Conversation not found")
        
        # 2. Create user message
        user_message = Message(
            conversation_id=input_data.conversation_id,
            role="user",
            content=input_data.content,
            sender_id=input_data.user_id,
        )
        await self._conversation_repo.add_message(user_message)
        
        # 3. Get agent response stream
        stream = self._streaming_service.stream_response(
            conversation=conversation,
            message=user_message,
        )
        
        return SendMessageOutput(
            message_id=user_message.id,
            conversation_id=conversation.id,
            stream=stream,
        )
```

---

## 4. Configuration Schema Design

### 4.1 Domain Configuration Schema

```yaml
# configs/domains/software_development.yaml
domain:
  id: "software_development"
  name: "Software Development"
  description: "Domain for software development tasks including coding, testing, and code review"
  version: "1.0.0"
  
  # Workflow Configuration
  workflow:
    type: "supervisor"  # supervisor | sequential | parallel | consensus
    max_iterations: 15
    timeout_seconds: 300
    
  # Agent Assignments
  agents:
    default: "planner"
    fallback: "planner"
    members:
      - "planner"
      - "coder"
      - "critic"
      - "tester"
      - "reviewer"
      - "code_review_agent"
      - "devops_agent"
  
  # Routing Rules
  routing:
    rules:
      - keywords: ["plan", "strategy", "design", "architect"]
        agent: "planner"
        priority: 1
      
      - keywords: ["code", "implement", "write", "create", "build"]
        agent: "coder"
        priority: 2
      
      - keywords: ["review", "check", "analyze", "quality"]
        agent: "code_review_agent"
        priority: 2
      
      - keywords: ["test", "verify", "validate", "run"]
        agent: "tester"
        priority: 3
      
      - keywords: ["deploy", "ci/cd", "pipeline", "docker"]
        agent: "devops_agent"
        priority: 2
    
    # Fallback handling
    fallback:
      agent: "planner"
      message: "I'll help you plan this task."
  
  # Human-in-the-Loop Settings
  approval:
    required_for:
      - "file_write"
      - "code_execution"
      - "external_api_call"
    bypass_roles:
      - "admin"
      - "developer"
  
  # Permissions
  permissions:
    allowed_roles: ["user", "developer", "operator", "admin"]
    restricted_tools:
      admin_only: ["delete_file", "modify_config"]
      developer_only: ["code_execution", "git_operations"]
  
  # Metadata
  metadata:
    author: "system"
    created_at: "2026-01-22T00:00:00Z"
    tags: ["development", "coding", "software"]
```

### 4.2 Agent Configuration Schema

```yaml
# configs/agents/core/coder.yaml
agent:
  id: "coder"
  name: "Coder"
  domain: "software_development"
  version: "1.0.0"
  state: "production"  # development | testing | production | deprecated
  
  # Role Definition
  role:
    description: "Expert Python developer who writes clean, efficient code"
    expertise:
      - "Python programming"
      - "Clean code principles"
      - "Design patterns"
      - "Error handling"
      - "File operations"
    
  # System Prompt
  prompt:
    system: |
      You are an expert Python developer.
      
      Your responsibilities:
      1. Write clean, well-documented code
      2. Follow PEP 8 style guidelines
      3. Include proper error handling
      4. Save code to appropriate files
      5. Ask Critic to review your code after saving
      
      Always use the save_file tool to persist your code.
      After saving, say: "I have saved the code. Critic, please review."
    
    # Optional context injection
    context_template: |
      Project context: {project_description}
      Recent files: {recent_files}
      Current task: {task_description}
  
  # LLM Configuration
  llm:
    provider: "ollama"
    model: "gpt-oss:120b-cloud"
    temperature: 0.0
    max_tokens: 4096
    timeout_seconds: 120
  
  # Tools Available
  tools:
    - "save_file"
    - "save_memory"
    - "search_memory"
  
  # Routing Keywords
  routing:
    keywords:
      - "code"
      - "implement"
      - "write"
      - "create"
      - "build"
      - "develop"
      - "program"
    priority: 2
    
  # Collaboration
  collaboration:
    reports_to: "supervisor"
    hands_off_to:
      - agent: "critic"
        on_completion: true
        message: "Code saved. Critic, please review."
    receives_from:
      - "planner"
      - "supervisor"
  
  # Performance Settings
  performance:
    max_retries: 3
    retry_delay_seconds: 2
    circuit_breaker:
      failure_threshold: 5
      reset_timeout_seconds: 60
  
  # Metadata
  metadata:
    author: "system"
    created_at: "2026-01-22T00:00:00Z"
    updated_at: "2026-01-22T00:00:00Z"
    test_results:
      passed: 25
      failed: 0
      coverage: 95.0
```

### 4.3 Tool Configuration Schema

```yaml
# configs/tools/file_operations.yaml
tools:
  - id: "save_file"
    name: "save_file"
    description: "Saves content to a file with security validation"
    version: "1.0.0"
    
    # Handler
    handler:
      module: "src.infrastructure.mcp.tool_handlers.file_operations"
      function: "save_file_handler"
    
    # Parameters Schema (JSON Schema)
    parameters:
      type: "object"
      required: ["filename", "content"]
      properties:
        filename:
          type: "string"
          description: "Relative file path (e.g., 'script.py' or 'output/data.json')"
          pattern: "^[a-zA-Z0-9_./\\-]+$"
        content:
          type: "string"
          description: "Content to write to the file"
    
    # Return Schema
    returns:
      type: "object"
      properties:
        success:
          type: "boolean"
        message:
          type: "string"
        file_path:
          type: "string"
    
    # Security
    security:
      requires_approval: true
      allowed_roles: ["developer", "operator", "admin"]
      sandbox:
        allowed_directories:
          - "./workspace"
          - "./output"
          - "./temp"
        allowed_extensions:
          - ".py"
          - ".txt"
          - ".md"
          - ".json"
          - ".yaml"
        deny_patterns:
          - ".."
          - "~"
    
    # Execution
    execution:
      timeout_seconds: 30
      max_retries: 2
      async: false
    
    # Categorization
    tags: ["file", "io", "coding"]
    domain: "software_development"
```

---

## 5. Frontend Architecture (React + Vite + shadcn/ui)

### 5.1 Complete Folder Structure

```
frontend/
├── src/
│   ├── main.tsx                        # Application entry point
│   ├── App.tsx                         # Root component with providers
│   ├── vite-env.d.ts                   # Vite type definitions
│   │
│   ├── domain/                          # DOMAIN LAYER
│   │   ├── entities/                    # Domain Entities
│   │   │   ├── index.ts
│   │   │   ├── Agent.ts
│   │   │   ├── Domain.ts
│   │   │   ├── Tool.ts
│   │   │   ├── User.ts
│   │   │   ├── Conversation.ts
│   │   │   └── Message.ts
│   │   │
│   │   ├── value-objects/               # Value Objects
│   │   │   ├── index.ts
│   │   │   ├── AgentState.ts
│   │   │   ├── UserRole.ts
│   │   │   ├── MessageType.ts
│   │   │   └── ToolApprovalStatus.ts
│   │   │
│   │   └── services/                    # Domain Services
│   │       ├── index.ts
│   │       ├── MessageService.ts
│   │       └── ValidationService.ts
│   │
│   ├── application/                     # APPLICATION LAYER
│   │   ├── use-cases/                   # Use Cases (Business Logic)
│   │   │   ├── index.ts
│   │   │   ├── auth/
│   │   │   │   ├── useLogin.ts
│   │   │   │   ├── useLogout.ts
│   │   │   │   └── useRefreshToken.ts
│   │   │   ├── conversations/
│   │   │   │   ├── useStartConversation.ts
│   │   │   │   ├── useSendMessage.ts
│   │   │   │   ├── useApproveToolCall.ts
│   │   │   │   └── useConversationHistory.ts
│   │   │   ├── agents/
│   │   │   │   ├── useAgents.ts
│   │   │   │   ├── useCreateAgent.ts
│   │   │   │   └── usePromoteAgent.ts
│   │   │   ├── domains/
│   │   │   │   ├── useDomains.ts
│   │   │   │   └── useCreateDomain.ts
│   │   │   └── users/
│   │   │       ├── useUsers.ts
│   │   │       └── useCreateUser.ts
│   │   │
│   │   ├── state/                       # State Management
│   │   │   ├── index.ts
│   │   │   ├── stores/
│   │   │   │   ├── authStore.ts         # Zustand auth store
│   │   │   │   ├── conversationStore.ts
│   │   │   │   ├── agentStore.ts
│   │   │   │   ├── domainStore.ts
│   │   │   │   └── uiStore.ts
│   │   │   │
│   │   │   └── queries/                 # React Query hooks
│   │   │       ├── agentQueries.ts
│   │   │       ├── domainQueries.ts
│   │   │       ├── userQueries.ts
│   │   │       └── metricsQueries.ts
│   │   │
│   │   └── interfaces/                  # Application Interfaces
│   │       ├── index.ts
│   │       ├── IApiClient.ts
│   │       ├── IWebSocketClient.ts
│   │       └── IAuthService.ts
│   │
│   ├── infrastructure/                  # INFRASTRUCTURE LAYER
│   │   ├── api/                         # API Clients
│   │   │   ├── index.ts
│   │   │   ├── apiClient.ts             # Axios/fetch wrapper
│   │   │   ├── endpoints/
│   │   │   │   ├── authApi.ts
│   │   │   │   ├── agentsApi.ts
│   │   │   │   ├── domainsApi.ts
│   │   │   │   ├── conversationsApi.ts
│   │   │   │   ├── usersApi.ts
│   │   │   │   └── metricsApi.ts
│   │   │   │
│   │   │   └── interceptors/
│   │   │       ├── authInterceptor.ts
│   │   │       └── errorInterceptor.ts
│   │   │
│   │   ├── websocket/                   # WebSocket Client
│   │   │   ├── index.ts
│   │   │   ├── WebSocketClient.ts
│   │   │   ├── WebSocketProvider.tsx
│   │   │   ├── useWebSocket.ts
│   │   │   └── protocol.ts              # Message types
│   │   │
│   │   ├── storage/                     # Local Storage
│   │   │   ├── index.ts
│   │   │   ├── tokenStorage.ts
│   │   │   └── preferencesStorage.ts
│   │   │
│   │   └── auth/                        # Auth Infrastructure
│   │       ├── index.ts
│   │       ├── AuthProvider.tsx
│   │       ├── useAuth.ts
│   │       └── ProtectedRoute.tsx
│   │
│   ├── presentation/                    # PRESENTATION LAYER
│   │   ├── components/                  # Reusable UI Components
│   │   │   ├── ui/                      # shadcn/ui components
│   │   │   │   ├── button.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── dialog.tsx
│   │   │   │   ├── dropdown-menu.tsx
│   │   │   │   ├── tabs.tsx
│   │   │   │   ├── toast.tsx
│   │   │   │   ├── avatar.tsx
│   │   │   │   ├── badge.tsx
│   │   │   │   ├── scroll-area.tsx
│   │   │   │   └── skeleton.tsx
│   │   │   │
│   │   │   ├── layout/                  # Layout Components
│   │   │   │   ├── AppLayout.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   └── NavigationMenu.tsx
│   │   │   │
│   │   │   ├── chat/                    # Chat Components
│   │   │   │   ├── ChatContainer.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   ├── MessageItem.tsx
│   │   │   │   ├── MessageInput.tsx
│   │   │   │   ├── StreamingMessage.tsx
│   │   │   │   ├── ToolApprovalCard.tsx
│   │   │   │   └── AgentAvatar.tsx
│   │   │   │
│   │   │   ├── agents/                  # Agent Components
│   │   │   │   ├── AgentCard.tsx
│   │   │   │   ├── AgentList.tsx
│   │   │   │   ├── AgentDetails.tsx
│   │   │   │   ├── AgentForm.tsx
│   │   │   │   ├── AgentStateIndicator.tsx
│   │   │   │   └── AgentMetricsChart.tsx
│   │   │   │
│   │   │   ├── domains/                 # Domain Components
│   │   │   │   ├── DomainCard.tsx
│   │   │   │   ├── DomainList.tsx
│   │   │   │   ├── DomainDetails.tsx
│   │   │   │   ├── DomainForm.tsx
│   │   │   │   └── WorkflowVisualizer.tsx
│   │   │   │
│   │   │   ├── admin/                   # Admin Components
│   │   │   │   ├── UserTable.tsx
│   │   │   │   ├── UserForm.tsx
│   │   │   │   ├── MetricsDashboard.tsx
│   │   │   │   ├── SystemHealth.tsx
│   │   │   │   └── ConfigEditor.tsx
│   │   │   │
│   │   │   └── common/                  # Common Components
│   │   │       ├── LoadingSpinner.tsx
│   │   │       ├── ErrorBoundary.tsx
│   │   │       ├── EmptyState.tsx
│   │   │       ├── ConfirmDialog.tsx
│   │   │       └── StatusBadge.tsx
│   │   │
│   │   ├── pages/                       # Page Components
│   │   │   ├── index.ts
│   │   │   ├── LoginPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── ChatPage.tsx
│   │   │   ├── DomainsPage.tsx
│   │   │   ├── DomainDetailPage.tsx
│   │   │   ├── AgentsPage.tsx
│   │   │   ├── AgentDetailPage.tsx
│   │   │   ├── ToolsPage.tsx
│   │   │   ├── UsersPage.tsx
│   │   │   ├── MetricsPage.tsx
│   │   │   ├── SettingsPage.tsx
│   │   │   └── NotFoundPage.tsx
│   │   │
│   │   ├── features/                    # Feature Modules
│   │   │   ├── chat/
│   │   │   │   ├── index.ts
│   │   │   │   ├── ChatFeature.tsx
│   │   │   │   ├── hooks/
│   │   │   │   │   ├── useChat.ts
│   │   │   │   │   └── useStreamingMessage.ts
│   │   │   │   └── utils/
│   │   │   │       └── messageFormatter.ts
│   │   │   │
│   │   │   ├── domain-browser/
│   │   │   │   ├── index.ts
│   │   │   │   ├── DomainBrowserFeature.tsx
│   │   │   │   └── hooks/
│   │   │   │       └── useDomainBrowser.ts
│   │   │   │
│   │   │   ├── agent-explorer/
│   │   │   │   ├── index.ts
│   │   │   │   ├── AgentExplorerFeature.tsx
│   │   │   │   └── hooks/
│   │   │   │       └── useAgentExplorer.ts
│   │   │   │
│   │   │   ├── admin-panel/
│   │   │   │   ├── index.ts
│   │   │   │   ├── AdminPanelFeature.tsx
│   │   │   │   └── hooks/
│   │   │   │       └── useAdmin.ts
│   │   │   │
│   │   │   ├── human-in-loop/
│   │   │   │   ├── index.ts
│   │   │   │   ├── HumanInLoopFeature.tsx
│   │   │   │   └── hooks/
│   │   │   │       └── useToolApproval.ts
│   │   │   │
│   │   │   └── version-management/
│   │   │       ├── index.ts
│   │   │       ├── VersionManagementFeature.tsx
│   │   │       └── hooks/
│   │   │           └── useVersionManagement.ts
│   │   │
│   │   └── hooks/                       # Shared Presentation Hooks
│   │       ├── index.ts
│   │       ├── useToast.ts
│   │       ├── useTheme.ts
│   │       └── useMediaQuery.ts
│   │
│   ├── config/                          # Configuration
│   │   ├── index.ts
│   │   ├── env.ts                       # Environment variables
│   │   ├── routes.ts                    # Route definitions
│   │   └── constants.ts                 # App constants
│   │
│   ├── lib/                             # Utilities
│   │   ├── utils.ts                     # shadcn/ui utils
│   │   ├── cn.ts                        # className helper
│   │   └── formatters.ts                # Date/string formatters
│   │
│   └── styles/                          # Global Styles
│       ├── globals.css                  # Tailwind imports
│       └── themes/
│           ├── light.css
│           └── dark.css
│
├── public/                              # Static Assets
│   ├── favicon.ico
│   └── assets/
│       └── images/
│
├── tests/                               # Test Suite
│   ├── setup.ts                         # Test setup
│   ├── unit/
│   │   ├── domain/
│   │   ├── application/
│   │   └── presentation/
│   ├── integration/
│   │   └── features/
│   └── e2e/
│       └── cypress/
│
├── index.html                           # HTML entry
├── vite.config.ts                       # Vite configuration
├── tailwind.config.ts                   # Tailwind configuration
├── tsconfig.json                        # TypeScript configuration
├── components.json                      # shadcn/ui configuration
├── package.json
└── .env.example
```

### 5.2 State Management Pattern

```typescript
// frontend/src/application/state/stores/conversationStore.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { Conversation, Message } from '@/domain/entities';

interface ConversationState {
  // State
  conversations: Map<string, Conversation>;
  activeConversationId: string | null;
  isStreaming: boolean;
  pendingApproval: ToolApprovalRequest | null;
  
  // Actions
  setActiveConversation: (id: string) => void;
  addMessage: (conversationId: string, message: Message) => void;
  appendToStreamingMessage: (conversationId: string, chunk: string) => void;
  setStreamingComplete: (conversationId: string, messageId: string) => void;
  setPendingApproval: (request: ToolApprovalRequest | null) => void;
  clearConversation: (id: string) => void;
}

interface ToolApprovalRequest {
  conversationId: string;
  toolName: string;
  toolArgs: Record<string, unknown>;
  requestId: string;
}

export const useConversationStore = create<ConversationState>()(
  devtools(
    persist(
      immer((set, get) => ({
        conversations: new Map(),
        activeConversationId: null,
        isStreaming: false,
        pendingApproval: null,
        
        setActiveConversation: (id) => {
          set((state) => {
            state.activeConversationId = id;
          });
        },
        
        addMessage: (conversationId, message) => {
          set((state) => {
            const conversation = state.conversations.get(conversationId);
            if (conversation) {
              conversation.messages.push(message);
            }
          });
        },
        
        appendToStreamingMessage: (conversationId, chunk) => {
          set((state) => {
            const conversation = state.conversations.get(conversationId);
            if (conversation) {
              const lastMessage = conversation.messages[conversation.messages.length - 1];
              if (lastMessage && lastMessage.isStreaming) {
                lastMessage.content += chunk;
              }
            }
            state.isStreaming = true;
          });
        },
        
        setStreamingComplete: (conversationId, messageId) => {
          set((state) => {
            const conversation = state.conversations.get(conversationId);
            if (conversation) {
              const message = conversation.messages.find(m => m.id === messageId);
              if (message) {
                message.isStreaming = false;
              }
            }
            state.isStreaming = false;
          });
        },
        
        setPendingApproval: (request) => {
          set((state) => {
            state.pendingApproval = request;
          });
        },
        
        clearConversation: (id) => {
          set((state) => {
            state.conversations.delete(id);
            if (state.activeConversationId === id) {
              state.activeConversationId = null;
            }
          });
        },
      })),
      {
        name: 'conversation-storage',
        partialize: (state) => ({
          conversations: state.conversations,
          activeConversationId: state.activeConversationId,
        }),
      }
    ),
    { name: 'ConversationStore' }
  )
);
```

### 5.3 WebSocket Integration

```typescript
// frontend/src/infrastructure/websocket/WebSocketClient.ts
import { EventEmitter } from 'events';

export enum WebSocketMessageType {
  // Client -> Server
  START_CONVERSATION = 'start_conversation',
  SEND_MESSAGE = 'send_message',
  APPROVE_TOOL = 'approve_tool',
  REJECT_TOOL = 'reject_tool',
  CANCEL_STREAM = 'cancel_stream',
  
  // Server -> Client
  CONVERSATION_STARTED = 'conversation_started',
  MESSAGE_CHUNK = 'message_chunk',
  MESSAGE_COMPLETE = 'message_complete',
  AGENT_TRANSITION = 'agent_transition',
  TOOL_APPROVAL_REQUIRED = 'tool_approval_required',
  TOOL_EXECUTED = 'tool_executed',
  ERROR = 'error',
  HEARTBEAT = 'heartbeat',
}

export interface WebSocketMessage<T = unknown> {
  type: WebSocketMessageType;
  payload: T;
  timestamp: string;
  conversationId?: string;
  requestId?: string;
}

export class WebSocketClient extends EventEmitter {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  
  constructor(private url: string, private token: string) {
    super();
  }
  
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(`${this.url}?token=${this.token}`);
      
      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.startHeartbeat();
        this.emit('connected');
        resolve();
      };
      
      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      this.ws.onclose = (event) => {
        this.stopHeartbeat();
        this.emit('disconnected', event);
        
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.attemptReconnect();
        }
      };
      
      this.ws.onerror = (error) => {
        this.emit('error', error);
        reject(error);
      };
    });
  }
  
  private handleMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case WebSocketMessageType.MESSAGE_CHUNK:
        this.emit('message_chunk', message.payload);
        break;
      case WebSocketMessageType.MESSAGE_COMPLETE:
        this.emit('message_complete', message.payload);
        break;
      case WebSocketMessageType.AGENT_TRANSITION:
        this.emit('agent_transition', message.payload);
        break;
      case WebSocketMessageType.TOOL_APPROVAL_REQUIRED:
        this.emit('tool_approval_required', message.payload);
        break;
      case WebSocketMessageType.TOOL_EXECUTED:
        this.emit('tool_executed', message.payload);
        break;
      case WebSocketMessageType.ERROR:
        this.emit('error', message.payload);
        break;
      case WebSocketMessageType.HEARTBEAT:
        // Respond to heartbeat
        this.send({ type: WebSocketMessageType.HEARTBEAT, payload: {} });
        break;
    }
  }
  
  send<T>(message: Omit<WebSocketMessage<T>, 'timestamp'>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      const fullMessage: WebSocketMessage<T> = {
        ...message,
        timestamp: new Date().toISOString(),
      };
      this.ws.send(JSON.stringify(fullMessage));
    } else {
      throw new Error('WebSocket is not connected');
    }
  }
  
  sendMessage(conversationId: string, content: string): void {
    this.send({
      type: WebSocketMessageType.SEND_MESSAGE,
      payload: { content },
      conversationId,
    });
  }
  
  approveToolCall(conversationId: string, requestId: string): void {
    this.send({
      type: WebSocketMessageType.APPROVE_TOOL,
      payload: { approved: true },
      conversationId,
      requestId,
    });
  }
  
  rejectToolCall(conversationId: string, requestId: string): void {
    this.send({
      type: WebSocketMessageType.REJECT_TOOL,
      payload: { approved: false },
      conversationId,
      requestId,
    });
  }
  
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: WebSocketMessageType.HEARTBEAT, payload: {} });
      }
    }, 30000);
  }
  
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
  
  private attemptReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    setTimeout(() => {
      this.connect().catch(() => {
        // Reconnection failed, will try again if under limit
      });
    }, delay);
  }
  
  disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, 'Client disconnected');
      this.ws = null;
    }
  }
}
```

---

## 6. WebSocket Streaming Protocol

### 6.1 Message Protocol Definition

```typescript
// Shared protocol definition (used by both frontend and backend)

// ============================================
// CLIENT -> SERVER MESSAGES
// ============================================

interface StartConversationMessage {
  type: "start_conversation";
  payload: {
    domainId: string;
    initialMessage?: string;
  };
}

interface SendMessageMessage {
  type: "send_message";
  payload: {
    content: string;
  };
  conversationId: string;
}

interface ApproveToolMessage {
  type: "approve_tool";
  payload: {
    approved: boolean;
    reason?: string;
  };
  conversationId: string;
  requestId: string;
}

interface CancelStreamMessage {
  type: "cancel_stream";
  payload: {};
  conversationId: string;
}

// ============================================
// SERVER -> CLIENT MESSAGES
// ============================================

interface ConversationStartedMessage {
  type: "conversation_started";
  payload: {
    conversationId: string;
    domainId: string;
    activeAgent: string;
  };
}

interface MessageChunkMessage {
  type: "message_chunk";
  payload: {
    messageId: string;
    chunk: string;
    agentName: string;
  };
  conversationId: string;
}

interface MessageCompleteMessage {
  type: "message_complete";
  payload: {
    messageId: string;
    content: string;
    agentName: string;
    metadata: {
      tokenCount: number;
      durationMs: number;
    };
  };
  conversationId: string;
}

interface AgentTransitionMessage {
  type: "agent_transition";
  payload: {
    fromAgent: string;
    toAgent: string;
    reason: string;
  };
  conversationId: string;
}

interface ToolApprovalRequiredMessage {
  type: "tool_approval_required";
  payload: {
    requestId: string;
    toolName: string;
    toolArgs: Record<string, unknown>;
    description: string;
    agentName: string;
  };
  conversationId: string;
}

interface ToolExecutedMessage {
  type: "tool_executed";
  payload: {
    requestId: string;
    toolName: string;
    result: unknown;
    success: boolean;
    errorMessage?: string;
  };
  conversationId: string;
}

interface ErrorMessage {
  type: "error";
  payload: {
    code: string;
    message: string;
    details?: unknown;
  };
  conversationId?: string;
}
```

### 6.2 Backend WebSocket Handler

```python
# backend/src/presentation/websocket/handlers.py
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, AsyncGenerator
import json
import asyncio

from ...application.use_cases.conversations import SendMessageUseCase
from ...application.dto.message_dto import StreamChunkDTO
from ...infrastructure.messaging.websocket_manager import WebSocketManager


class ConversationWebSocketHandler:
    """WebSocket handler for real-time conversation streaming."""
    
    def __init__(
        self,
        send_message_use_case: SendMessageUseCase,
        ws_manager: WebSocketManager,
    ):
        self._send_message = send_message_use_case
        self._ws_manager = ws_manager
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        user_id: str,
        conversation_id: str,
    ):
        """Handle WebSocket connection lifecycle."""
        await websocket.accept()
        connection_id = await self._ws_manager.connect(
            websocket, user_id, conversation_id
        )
        
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                await self._handle_message(
                    websocket, user_id, conversation_id, message
                )
        except WebSocketDisconnect:
            await self._ws_manager.disconnect(connection_id)
    
    async def _handle_message(
        self,
        websocket: WebSocket,
        user_id: str,
        conversation_id: str,
        message: Dict,
    ):
        """Route incoming WebSocket messages."""
        msg_type = message.get("type")
        payload = message.get("payload", {})
        
        handlers = {
            "send_message": self._handle_send_message,
            "approve_tool": self._handle_approve_tool,
            "reject_tool": self._handle_reject_tool,
            "cancel_stream": self._handle_cancel_stream,
        }
        
        handler = handlers.get(msg_type)
        if handler:
            await handler(websocket, user_id, conversation_id, payload, message)
        else:
            await self._send_error(websocket, "unknown_message_type", f"Unknown message type: {msg_type}")
    
    async def _handle_send_message(
        self,
        websocket: WebSocket,
        user_id: str,
        conversation_id: str,
        payload: Dict,
        original_message: Dict,
    ):
        """Handle send_message and stream response."""
        content = payload.get("content", "")
        
        try:
            # Execute use case and get streaming response
            result = await self._send_message.execute(
                SendMessageInput(
                    conversation_id=conversation_id,
                    content=content,
                    user_id=user_id,
                )
            )
            
            # Stream response chunks
            async for chunk in result.stream:
                await self._send_chunk(websocket, conversation_id, chunk)
            
            # Send completion message
            await self._send_complete(websocket, conversation_id, result)
            
        except Exception as e:
            await self._send_error(websocket, "execution_error", str(e))
    
    async def _send_chunk(
        self,
        websocket: WebSocket,
        conversation_id: str,
        chunk: StreamChunkDTO,
    ):
        """Send a streaming chunk to the client."""
        message = {
            "type": "message_chunk",
            "payload": {
                "messageId": chunk.message_id,
                "chunk": chunk.content,
                "agentName": chunk.agent_name,
            },
            "conversationId": conversation_id,
            "timestamp": chunk.timestamp.isoformat(),
        }
        await websocket.send_json(message)
    
    async def _send_complete(
        self,
        websocket: WebSocket,
        conversation_id: str,
        result: SendMessageOutput,
    ):
        """Send message completion notification."""
        message = {
            "type": "message_complete",
            "payload": {
                "messageId": result.message_id,
                "content": result.full_content,
                "agentName": result.agent_name,
                "metadata": {
                    "tokenCount": result.token_count,
                    "durationMs": result.duration_ms,
                },
            },
            "conversationId": conversation_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await websocket.send_json(message)
    
    async def _send_error(
        self,
        websocket: WebSocket,
        code: str,
        message: str,
    ):
        """Send error message to client."""
        error_msg = {
            "type": "error",
            "payload": {
                "code": code,
                "message": message,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        await websocket.send_json(error_msg)
```

---

## 7. API Endpoint Design

### 7.1 REST API Endpoints

```
# Authentication
POST   /api/v1/auth/login              # Login, get JWT token
POST   /api/v1/auth/logout             # Logout, revoke token
POST   /api/v1/auth/refresh            # Refresh JWT token
POST   /api/v1/auth/change-password    # Change password

# Users (Admin only)
GET    /api/v1/users                   # List users (paginated)
POST   /api/v1/users                   # Create user
GET    /api/v1/users/{id}              # Get user details
PUT    /api/v1/users/{id}              # Update user
DELETE /api/v1/users/{id}              # Delete user
GET    /api/v1/users/me                # Get current user profile

# Domains
GET    /api/v1/domains                 # List domains
POST   /api/v1/domains                 # Create domain (from YAML)
GET    /api/v1/domains/{id}            # Get domain details
PUT    /api/v1/domains/{id}            # Update domain
DELETE /api/v1/domains/{id}            # Delete domain
POST   /api/v1/domains/{id}/sync       # Sync domain config from YAML
GET    /api/v1/domains/{id}/agents     # List agents in domain

# Agents
GET    /api/v1/agents                  # List agents (with filters)
POST   /api/v1/agents                  # Create agent (from YAML)
GET    /api/v1/agents/{id}             # Get agent details
PUT    /api/v1/agents/{id}             # Update agent
DELETE /api/v1/agents/{id}             # Delete agent
POST   /api/v1/agents/{id}/promote     # Promote agent state
GET    /api/v1/agents/{id}/versions    # List agent versions
GET    /api/v1/agents/{id}/metrics     # Get agent metrics

# Tools
GET    /api/v1/tools                   # List tools
POST   /api/v1/tools                   # Register tool
GET    /api/v1/tools/{id}              # Get tool details
PUT    /api/v1/tools/{id}              # Update tool
DELETE /api/v1/tools/{id}              # Unregister tool

# Conversations (REST fallback)
GET    /api/v1/conversations           # List user's conversations
POST   /api/v1/conversations           # Start new conversation
GET    /api/v1/conversations/{id}      # Get conversation details
DELETE /api/v1/conversations/{id}      # Delete conversation
GET    /api/v1/conversations/{id}/messages  # Get conversation history

# Configuration
GET    /api/v1/config/domains          # List domain configs
GET    /api/v1/config/agents           # List agent configs
GET    /api/v1/config/tools            # List tool configs
POST   /api/v1/config/sync             # Sync all configs from YAML
POST   /api/v1/config/validate         # Validate config file

# Health & Metrics
GET    /api/v1/health                  # Health check
GET    /api/v1/health/agents           # Agent health status
GET    /api/v1/metrics                 # Prometheus metrics
GET    /api/v1/metrics/agents          # Agent performance metrics
GET    /api/v1/metrics/tokens          # Token usage metrics

# WebSocket
WS     /ws/conversations/{id}          # Real-time conversation streaming
```

### 7.2 API Response Standards

```python
# backend/src/presentation/api/responses.py
from pydantic import BaseModel
from typing import TypeVar, Generic, List, Optional
from datetime import datetime

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    items: List[T]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_prev: bool


class ErrorResponse(BaseModel):
    """Error response."""
    success: bool = False
    error: str
    code: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

---

## 8. Test Strategy

### 8.1 Backend Test Structure

```python
# tests/unit/domain/test_agent_entity.py
import pytest
from src.domain.entities.agent import Agent
from src.domain.value_objects.agent_state import AgentState
from src.domain.value_objects.version import SemanticVersion


class TestAgentEntity:
    """Unit tests for Agent entity."""
    
    def test_create_agent_with_valid_data(self):
        agent = Agent(
            id="agent_1",
            name="Coder",
            domain_id="software_dev",
            description="Python developer",
            version=SemanticVersion("1.0.0"),
            state=AgentState.DEVELOPMENT,
            system_prompt="You are a Python developer.",
            capabilities=["coding", "debugging"],
            tools=["save_file", "run_script"],
            model_name="gpt-oss:120b-cloud",
        )
        
        assert agent.name == "Coder"
        assert agent.state == AgentState.DEVELOPMENT
    
    def test_promote_from_dev_to_testing(self):
        agent = self._create_dev_agent()
        agent.promote(AgentState.TESTING)
        assert agent.state == AgentState.TESTING
    
    def test_promote_from_dev_to_production_raises_error(self):
        agent = self._create_dev_agent()
        with pytest.raises(ValueError, match="Invalid transition"):
            agent.promote(AgentState.PRODUCTION)
    
    def test_can_handle_matching_keywords(self):
        agent = self._create_dev_agent()
        agent.keywords = ["code", "implement", "develop"]
        
        score = agent.can_handle("write code", ["code", "write"])
        assert score > 0
    
    def _create_dev_agent(self) -> Agent:
        return Agent(
            id="test_agent",
            name="TestAgent",
            domain_id="test",
            description="Test",
            version=SemanticVersion("1.0.0"),
            state=AgentState.DEVELOPMENT,
            system_prompt="Test",
            capabilities=[],
            tools=[],
            model_name="test",
        )


# tests/integration/test_conversation_flow.py
import pytest
from httpx import AsyncClient
from src.presentation.api.main import create_app


@pytest.fixture
async def client():
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_conversation_flow_integration(client, auth_token):
    """Integration test for complete conversation flow."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # 1. Start conversation
    response = await client.post(
        "/api/v1/conversations",
        json={"domain_id": "software_development"},
        headers=headers,
    )
    assert response.status_code == 201
    conversation_id = response.json()["data"]["id"]
    
    # 2. Send message
    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "Write a hello world script"},
        headers=headers,
    )
    assert response.status_code == 201
    
    # 3. Get history
    response = await client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers,
    )
    assert response.status_code == 200
    messages = response.json()["data"]["items"]
    assert len(messages) >= 2  # User message + agent response
```

### 8.2 Frontend Test Structure

```typescript
// tests/unit/domain/Agent.test.ts
import { describe, it, expect } from 'vitest';
import { Agent, AgentState } from '@/domain/entities/Agent';

describe('Agent Entity', () => {
  it('should create an agent with valid data', () => {
    const agent = new Agent({
      id: 'agent_1',
      name: 'Coder',
      domainId: 'software_dev',
      state: AgentState.DEVELOPMENT,
    });
    
    expect(agent.name).toBe('Coder');
    expect(agent.state).toBe(AgentState.DEVELOPMENT);
  });
  
  it('should validate state transitions', () => {
    const agent = new Agent({
      id: 'agent_1',
      name: 'Coder',
      domainId: 'software_dev',
      state: AgentState.DEVELOPMENT,
    });
    
    expect(agent.canPromoteTo(AgentState.TESTING)).toBe(true);
    expect(agent.canPromoteTo(AgentState.PRODUCTION)).toBe(false);
  });
});

// tests/integration/features/chat.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatFeature } from '@/presentation/features/chat';
import { MockWebSocketProvider } from '@/tests/mocks/websocket';

describe('Chat Feature', () => {
  it('should send message and display streaming response', async () => {
    const user = userEvent.setup();
    
    render(
      <MockWebSocketProvider>
        <ChatFeature conversationId="test-conv" />
      </MockWebSocketProvider>
    );
    
    // Type message
    const input = screen.getByPlaceholderText(/type a message/i);
    await user.type(input, 'Hello, write a Python script');
    
    // Send message
    const sendButton = screen.getByRole('button', { name: /send/i });
    await user.click(sendButton);
    
    // Verify message appears
    await waitFor(() => {
      expect(screen.getByText(/Hello, write a Python script/i)).toBeInTheDocument();
    });
    
    // Verify streaming response
    await waitFor(() => {
      expect(screen.getByTestId('streaming-indicator')).toBeInTheDocument();
    });
  });
});
```

---

## 9. Migration Plan

### 9.1 Phase 1: Foundation (Week 1-2)

#### Backend Foundation
1. Set up new project structure with clean architecture
2. Implement domain entities and value objects
3. Create repository interfaces (ports)
4. Implement SQLite repositories (adapters)
5. Set up configuration loader with YAML parsing
6. Migrate existing auth system to new structure

#### Frontend Foundation
1. Initialize Vite + React + TypeScript project
2. Configure Tailwind CSS and shadcn/ui
3. Set up folder structure
4. Implement API client and WebSocket client
5. Create auth infrastructure

### 9.2 Phase 2: Core Features (Week 3-4)

#### Backend Core
1. Implement LangGraph adapter with streaming
2. Create configuration sync mechanism
3. Implement WebSocket handlers
4. Build conversation use cases
5. Migrate agent definitions to YAML configs

#### Frontend Core
1. Build chat interface with streaming
2. Implement domain browser
3. Create agent explorer
4. Add human-in-the-loop approval UI

### 9.3 Phase 3: Admin Features (Week 5-6)

#### Backend Admin
1. Implement admin API endpoints
2. Add metrics collection
3. Build version management
4. Create hot-reload for configs

#### Frontend Admin
1. Build admin dashboard
2. Create user management UI
3. Implement metrics visualization
4. Add configuration editor

### 9.4 Phase 4: Testing & Polish (Week 7-8)

1. Write comprehensive tests (unit, integration, e2e)
2. Performance optimization
3. Security audit
4. Documentation
5. Deployment setup

---

## 10. Critical Files for Implementation

### Backend Critical Files:
1. **`backend/src/domain/entities/agent.py`** - Core agent entity with state machine logic
2. **`backend/src/infrastructure/langgraph/graph_builder.py`** - Dynamic LangGraph construction from config
3. **`backend/src/infrastructure/config/yaml_loader.py`** - YAML config loading and validation
4. **`backend/src/presentation/websocket/handlers.py`** - WebSocket streaming implementation
5. **`backend/src/application/use_cases/conversations/send_message.py`** - Core conversation logic

### Frontend Critical Files:
1. **`frontend/src/infrastructure/websocket/WebSocketClient.ts`** - Real-time communication
2. **`frontend/src/application/state/stores/conversationStore.ts`** - Conversation state management
3. **`frontend/src/presentation/features/chat/ChatFeature.tsx`** - Main chat interface
4. **`frontend/src/presentation/components/chat/ToolApprovalCard.tsx`** - Human-in-the-loop UI
5. **`frontend/src/infrastructure/auth/AuthProvider.tsx`** - Authentication wrapper

### Configuration Critical Files:
1. **`configs/domains/software_development.yaml`** - Example domain configuration
2. **`configs/agents/core/coder.yaml`** - Example agent configuration
3. **`configs/tools/file_operations.yaml`** - Example tool configuration

---

## 11. Summary

This architecture transforms the existing Multi-Agent Intelligence system into a **configuration-driven, zero-code domain extension platform** while maintaining:

1. **Clean Architecture** - Clear separation of concerns across domain, application, infrastructure, and presentation layers
2. **TDD Support** - Comprehensive test structure for unit, integration, and e2e testing
3. **Hybrid Config** - YAML files for version control with SQLite sync for runtime
4. **Real-time Streaming** - WebSocket-based bidirectional communication
5. **Modern Frontend** - React + Vite + shadcn/ui with Zustand state management
6. **Extensibility** - New domains/agents/tools added via YAML without code changes
7. **Existing Patterns** - Preserves supervisor pattern, RBAC, MCP protocol, and human-in-the-loop

The migration follows a Big Bang approach replacing Streamlit completely with a modern React SPA, while carefully preserving all existing functionality and business logic.
