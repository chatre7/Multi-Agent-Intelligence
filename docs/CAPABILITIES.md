# Multi-Agent Intelligence Platform - Capabilities

> รายละเอียดความสามารถทั้งหมดของ Platform วิเคราะห์จาก Source Code

---

## 📋 สารบัญ

- [ภาพรวมสถาปัตยกรรม](#-ภาพรวมสถาปัตยกรรม)
- [Backend Capabilities](#-backend-capabilities)
- [Frontend Capabilities](#-frontend-capabilities)
- [WebSocket & Real-time Features](#-websocket--real-time-features)
- [Authentication & Authorization](#-authentication--authorization)
- [Agent System](#-agent-system)
- [Tool System](#-tool-system)
- [API Endpoints](#-api-endpoints)

---

## 🏗️ ภาพรวมสถาปัตยกรรม

### Clean Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │   REST API (FastAPI)    │    WebSocket Handlers         ││
│  │   /v1/auth, /v1/domains │    /ws (real-time streaming)  ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│                      Application Layer                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Use Cases: SendMessage, RequestToolRun, ApproveToolRun ││
│  │  ListAgents, ListDomains, CreateConversation, etc.      ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│                       Domain Layer                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Entities: Agent, Tool, DomainConfig, ToolRun          ││
│  │  Value Objects: AgentState, SemanticVersion            ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                      │
│  ┌────────────┬─────────────┬─────────────┬───────────────┐│
│  │  SQLite    │  LangGraph  │  LLM        │  Auth (JWT)   ││
│  │  Repos     │  Builder    │  Streaming  │  Permissions  ││
│  └────────────┴─────────────┴─────────────┴───────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, TypeScript, Vite 7, Zustand |
| **Backend** | Python 3.11+, FastAPI, LangGraph |
| **Database** | SQLite (checkpoints.db) |
| **LLM** | Ollama (local), OpenAI API compatible |
| **Container** | Docker, Docker Compose |
| **Proxy** | Nginx (reverse proxy, static serving) |

---

## 🔧 Backend Capabilities

### Domain Entities

#### 1. Agent Entity (`domain/entities/agent.py`)

AI Agent ที่สามารถจัดการงานต่างๆ:

| Property | Description |
|----------|-------------|
| `id` | Unique identifier |
| `name` | Human-readable name |
| `description` | Agent description |
| `model_id` | LLM model to use (e.g., `llama3.2`) |
| `system_prompt` | Persona/instructions |
| `tools` | List of tool IDs agent can use |
| `routing_keywords` | Keywords for automatic routing |
| `capabilities` | List of capabilities (e.g., `code_generation`) |
| `state` | Lifecycle state (DEVELOPMENT → PRODUCTION) |
| `version` | Semantic version |
| `domain` | Domain this agent belongs to |

**Methods:**
- `can_handle(intent, keywords)` - คำนวณ confidence score สำหรับ request
- `promote(target_state)` - เลื่อน state ตาม lifecycle
- `has_capability(capability)` - ตรวจสอบ capability
- `add_tool(tool_id)` / `remove_tool(tool_id)` - จัดการ tools

**Agent Lifecycle States:**
```
DEVELOPMENT → TESTING → PRODUCTION → DEPRECATED → ARCHIVED
```

#### 2. Tool Entity (`domain/entities/tool.py`)

เครื่องมือที่ Agent สามารถเรียกใช้:

| Property | Description |
|----------|-------------|
| `id` | Unique tool ID |
| `name` | Tool name |
| `description` | What the tool does |
| `parameters_schema` | JSON Schema for parameters |
| `returns_schema` | JSON Schema for return value |
| `handler_path` | Python module path to handler |
| `requires_approval` | ต้องขออนุมัติจากมนุษย์ก่อนรัน |
| `allowed_roles` | Roles ที่ใช้ tool นี้ได้ |
| `timeout_seconds` | Execution timeout |
| `max_retries` | Maximum retry attempts |

**Methods:**
- `validate_parameters(params)` - Validate input ด้วย JSON Schema
- `to_langchain_tool_schema()` - แปลงเป็น LangChain format
- `to_openai_function_schema()` - แปลงเป็น OpenAI function calling format
- `is_role_allowed(role)` - ตรวจสอบ permission

#### 3. DomainConfig Entity (`domain/entities/domain_config.py`)

การกำหนดค่า Business Domain:

| Property | Description |
|----------|-------------|
| `id` | Domain ID (e.g., `software_development`) |
| `name` | Display name |
| `description` | Domain description |
| `agents` | List of agent IDs in this domain |
| `default_agent` | Default agent for routing |
| `fallback_agent` | Fallback when no match |
| `routing_rules` | Rules for routing to agents |
| `allowed_roles` | Access control |

**Routing Rules:**
```python
RoutingRule(
    keywords=["bug", "fix", "error"],
    agent="debugger_agent",
    priority=10
)
```

#### 4. ToolRun Entity (`domain/entities/tool_run.py`)

การเรียกใช้ Tool พร้อม approval workflow:

| Property | Description |
|----------|-------------|
| `id` | Unique run ID |
| `tool_id` | Tool being executed |
| `conversation_id` | Related conversation |
| `status` | `pending` → `approved`/`rejected` → `executed`/`failed` |
| `parameters` | Input parameters |
| `result` | Execution result |
| `approved_by` | Who approved |
| `rejection_reason` | Why rejected |

---

### Application Use Cases

#### Conversation Use Cases
- `SendMessageUseCase` - ส่งข้อความและรับ streaming response
- `CreateConversationUseCase` - สร้าง conversation ใหม่
- `ListConversationsUseCase` - ดึงรายการ conversations
- `GetConversationMessagesUseCase` - ดึง messages ใน conversation

#### Tool Use Cases
- `RequestToolRunUseCase` - ขอเรียกใช้ tool
- `ApproveToolRunUseCase` - อนุมัติ tool run
- `RejectToolRunUseCase` - ปฏิเสธ tool run
- `ExecuteToolRunUseCase` - รัน tool หลังอนุมัติ
- `ListToolRunsUseCase` - ดึงรายการ tool runs

#### Agent Use Cases
- `ListAgentsUseCase` - ดึงรายการ agents
- `GetAgentUseCase` - ดึง agent detail
- `PromoteAgentUseCase` - เลื่อน state
- `BumpVersionUseCase` - เพิ่ม version
- `RegisterAgentUseCase` - ลงทะเบียน agent ใหม่

#### Domain Use Cases
- `ListDomainsUseCase` - ดึงรายการ domains
- `GetDomainUseCase` - ดึง domain detail

---

### LangGraph Integration

#### ConversationGraphBuilder (`infrastructure/langgraph/graph_builder.py`)

สร้าง Supervisor-style conversation graph แบบ dynamic:

```
┌─────────┐     ┌────────────┐     ┌─────────────┐
│  START  │────▶│ Supervisor │────▶│ Agent Node  │────▶ END
└─────────┘     └────────────┘     └─────────────┘
                      │                   ▲
                      │   Routing         │
                      └───────────────────┘
```

**Features:**
- Dynamic node creation จาก config
- Keyword-based routing
- Confidence scoring
- Default/Fallback agent handling

---

## ⚛️ Frontend Capabilities

### Pages

#### 1. LoginPage
- JWT authentication
- Username/password form
- Error handling
- Redirect หลัง login สำเร็จ

#### 2. ChatPage
- Real-time WebSocket streaming
- Domain/Agent selector
- Message history
- Send message form
- Loading indicators

#### 3. AdminPage (5 Tabs)

**Overview Tab:**
- 4 KPI StatCards (Domains, Agents, Conversations, Pending Tools)
- MetricsChart - tool run status distribution
- Health panel (auth mode, db type, version)
- ActivityFeed - recent tool runs & conversations

**Domains Tab:**
- DomainList component
- Search/filter
- DomainDetail panel (agents, routing rules)

**Agents Tab:**
- AgentList component
- Filter by domain/state
- AgentDetail panel
- State promotion buttons
- Color-coded StateBadge

**Tools Tab:**
- ToolRunList component
- Filter by status
- ToolApprovalModal
- Approve/Reject with reason

**Settings Tab:**
- Placeholder for future configuration

### Components

| Component | Description |
|-----------|-------------|
| `StatCard` | KPI card with icon & value |
| `MetricsChart` | Horizontal bar chart |
| `ActivityFeed` | Recent activity list |
| `DomainList` | Domain listing with search |
| `DomainDetail` | Domain details panel |
| `AgentList` | Agent listing with filters |
| `AgentDetail` | Agent details with promote |
| `StateBadge` | Color-coded state indicator |
| `ToolRunList` | Tool runs with filters |
| `ToolApprovalModal` | Approve/Reject modal |
| `ChatContainer` | WebSocket chat interface |
| `DomainSelector` | Domain dropdown |
| `AgentSelector` | Agent dropdown |

### State Management (Zustand)

- `useAuthStore` - Authentication state
- `useMetricsStore` - Admin metrics with auto-refresh (5s)
- `useChatStore` - Chat messages & conversations
- `useDomainStore` - Domains cache
- `useAgentStore` - Agents cache

---

## 🔌 WebSocket & Real-time Features

### Connection (`/ws`)

```javascript
const ws = new WebSocket(`ws://host/ws?token=${jwt_token}`);
```

### Message Types

| Type | Direction | Description |
|------|-----------|-------------|
| `PING` | Client → Server | Keep-alive |
| `PONG` | Server → Client | Keep-alive response |
| `start_conversation` | Client → Server | Start new conversation |
| `send_message` | Client → Server | Send chat message |
| `message_chunk` | Server → Client | Streaming token |
| `message_complete` | Server → Client | Message finished |
| `tool_approval_required` | Server → Client | Tool needs approval |
| `tool_approved` | Server → Client | Tool was approved |
| `tool_rejected` | Server → Client | Tool was rejected |
| `tool_executed` | Server → Client | Tool execution result |
| `error` | Server → Client | Error message |

### Streaming Response

```
Client: send_message("Hello")
     ↓
Server: message_chunk("Hello")
Server: message_chunk(" there")
Server: message_chunk("!")
Server: message_complete("Hello there!")
```

### Human-in-the-Loop Tool Approval

```
Agent calls tool (requires_approval=true)
     ↓
Server: tool_approval_required(tool_id, params)
     ↓
Admin reviews in UI
     ↓
Admin: approve_tool_run / reject_tool_run
     ↓
Server: tool_approved/rejected → tool_executed
```

---

## 🔐 Authentication & Authorization

### Auth Modes

| Mode | Description |
|------|-------------|
| `none` | No authentication required |
| `jwt` | JWT token authentication |

### JWT Configuration

```yaml
AUTH_MODE=jwt
AUTH_SECRET=your-secret-key
AUTH_USERS=admin:admin:admin;dev:dev:developer;user:user:user
```

### Roles & Permissions

| Role | Permissions |
|------|-------------|
| `admin` | All permissions |
| `developer` | Most permissions (no admin-only) |
| `user` | Basic chat & tool request |

### Permission List

```python
class Permission(Enum):
    CHAT_SEND = "chat:send"
    CHAT_READ = "chat:read"
    CONFIG_RELOAD = "config:reload"
    DOMAIN_READ = "domain:read"
    HEALTH_READ = "health:read"
    METRICS_READ = "metrics:read"
    AGENT_READ = "agent:read"
    AGENT_WRITE = "agent:write"
    TOOL_READ = "tool:read"
    TOOL_REQUEST = "tool:request"
    TOOL_APPROVE = "tool:approve"
    TOOL_REJECT = "tool:reject"
    TOOL_EXECUTE = "tool:execute"
```

---

## 🤖 Agent System

### Multi-Agent Orchestration

**Supervisor Pattern:**
1. User sends message
2. Supervisor analyzes keywords
3. Routing rules evaluated by priority
4. Best matching agent selected
5. Agent processes request
6. Response streamed back

### Agent Capabilities

Agents can have capabilities like:
- `code_generation`
- `debugging`
- `documentation`
- `testing`
- `code_review`
- `refactoring`

### Agent State Machine

```
┌─────────────┐     ┌─────────────┐     ┌────────────┐
│ DEVELOPMENT │────▶│   TESTING   │────▶│ PRODUCTION │
└─────────────┘     └─────────────┘     └────────────┘
                                               │
                                               ▼
                                        ┌────────────┐
                                        │ DEPRECATED │
                                        └────────────┘
                                               │
                                               ▼
                                        ┌────────────┐
                                        │  ARCHIVED  │
                                        └────────────┘
```

---

## 🔧 Tool System

### Built-in Tools

| Tool | Description |
|------|-------------|
| `file_read` | Read file contents |
| `file_write` | Write file contents |
| `noop` | No-op placeholder |

### Tool Features

- **Parameter Validation** - JSON Schema validation
- **Role-based Access** - Only allowed roles can use
- **Human Approval** - Optional approval workflow
- **Timeout & Retry** - Configurable execution limits
- **Async Support** - Can run asynchronously

### Tool Execution Flow

```
Request Tool Run
     ↓
Validate Parameters
     ↓
Check Permissions
     ↓
requires_approval? ─── No ──▶ Execute Immediately
     │
    Yes
     │
     ▼
Wait for Approval ─── Rejected ──▶ Return Rejection
     │
  Approved
     │
     ▼
Execute Tool
     │
     ▼
Return Result
```

---

## 📡 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/auth/login` | Login, get JWT token |
| GET | `/v1/auth/me` | Get current user info |

### Domains

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/domains` | List all domains |
| GET | `/v1/domains/{id}` | Get domain details |

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/agents` | List all agents |
| GET | `/v1/agents/{id}` | Get agent details |
| POST | `/v1/agents` | Register new agent |
| POST | `/v1/agents/{id}/promote` | Promote agent state |
| POST | `/v1/agents/{id}/bump-version` | Bump version |
| POST | `/v1/agents/{id}/heartbeat` | Agent heartbeat |

### Conversations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/conversations` | List conversations |
| POST | `/v1/conversations` | Create conversation |
| GET | `/v1/conversations/{id}` | Get conversation |
| GET | `/v1/conversations/{id}/messages` | Get messages |
| POST | `/v1/chat` | Send message (REST) |

### Tools

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/tools` | List all tools |
| GET | `/v1/tools/{id}` | Get tool details |
| GET | `/v1/tool-runs` | List tool runs |
| POST | `/v1/tool-runs` | Request tool run |
| POST | `/v1/tool-runs/{id}/approve` | Approve run |
| POST | `/v1/tool-runs/{id}/reject` | Reject run |

### Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/config/reload` | Reload YAML configs |
| GET | `/v1/config/status` | Config status |
| GET | `/v1/config/sync` | Sync configs (hash-based) |

### Health & Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/details` | Detailed health info |
| GET | `/metrics` | Prometheus metrics |

---

## 📊 Metrics & Monitoring

### Available Metrics

- Total domains count
- Total agents count
- Total conversations count
- Tool runs by status (pending/approved/rejected/executed)
- System info (auth mode, database type, version)

### Health Check Response

```json
{
  "status": "healthy",
  "auth_mode": "jwt",
  "database": "sqlite",
  "version": "1.0.0",
  "domains_count": 3,
  "agents_count": 5,
  "conversations_count": 10
}
```

---

## 🚀 Deployment

### Docker Compose (Production)

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

**Services:**
- `mai-backend` - FastAPI + Python
- `mai-nginx` - Nginx + Static Frontend

### Environment Variables

```yaml
# Backend
OLLAMA_BASE_URL=http://host.docker.internal:11434
DATABASE_PATH=/app/data/checkpoints.db
LOG_LEVEL=INFO
AUTH_MODE=jwt
AUTH_SECRET=change-in-production
AUTH_USERS=admin:admin:admin

# Frontend (build-time)
VITE_API_BASE_URL=/api
VITE_WS_URL=/ws
```

---

## 🧪 Testing

### Backend Tests (130 tests)

```bash
cd backend
pytest tests/ -v
```

**Coverage:**
- Unit tests for all entities
- Repository tests
- Use case tests
- API endpoint tests
- WebSocket connection tests

---

**Last Updated:** January 23, 2026  
**Version:** 1.1.0
