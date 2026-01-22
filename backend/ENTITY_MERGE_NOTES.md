# Entity Merge and Alignment Notes

## Overview
This document explains how domain entities are organized and how they work together without conflicts.

---

## Entity Types

### 1. Agent Configuration Entities

#### **Agent** (Configuration-Defined)
- **Purpose**: Represents agents defined via YAML config files
- **Lifecycle**: Development → Testing → Production → Deprecated → Archived
- **Fields**:
  - `id`, `name`, `domain_id`, `description`
  - `system_prompt` - The LLM system prompt
  - `capabilities` - List of capabilities (e.g., ["python", "code_review"])
  - `tools` - List of tool IDs this agent can use
  - `model_name`, `temperature`, `max_tokens`
  - `keywords` - Routing keywords (e.g., ["code", "implement", "write"])
  - `version`, `state`, `created_at`, `updated_at`
  - `test_results`, `performance_metrics`

**Usage**: Configuration defined in YAML → loaded into DB → used for agent orchestration

#### **RegisteredAgent** (Runtime-Discovered)
- **Purpose**: Represents agents discovered at runtime (local or remote)
- **Lifecycle**: Same as Agent (dev → test → prod → deprecated → archived)
- **Fields**:
  - `id`, `name`, `description`
  - `endpoint` - URL/address where agent is accessible
  - `capabilities` - Capabilities list
  - `version`, `state`, `created_at`, `updated_at`
  - `last_heartbeat_at` - For health checking
  - `metadata` - Flexible extra data

**Usage**: Dynamic agent discovery, health monitoring, remote agents

#### **Difference**:
| Aspect | Agent | RegisteredAgent |
|--------|-------|-----------------|
| Definition | YAML config files | Runtime discovery |
| Deployment | Centralized | Distributed/Remote |
| Configuration | System prompt, routing keywords | Just metadata |
| Usage | Core orchestration | Integration/Fallback |

---

### 2. Tool Entities

#### **Tool** (Tool Definition)
- **Purpose**: Represents executable tools that agents can use
- **Fields**:
  - `id`, `name`, `description`
  - `parameters_schema` - JSON Schema for input validation
  - `returns_schema` - JSON Schema for output validation
  - `handler_path` - Python function to execute (e.g., "src.infrastructure.tools.file_operations.save_file")
  - `timeout_seconds`, `max_retries`
  - `requires_approval` - Whether human approval is needed
  - `allowed_roles` - Who can use this tool
  - `tags` - Categorization (e.g., ["file", "io"])
  - `domain` - Optional domain this tool belongs to
  - `is_async` - Whether tool runs asynchronously
  - `metadata` - Extra config

#### **ToolRun** (Tool Execution Record)
- **Purpose**: Represents a specific execution of a tool (human-in-the-loop workflow)
- **Fields**:
  - `id`, `tool_id`, `conversation_id`
  - `parameters` - Actual parameters passed
  - `status` - PENDING_APPROVAL, APPROVED, REJECTED, EXECUTED, FAILED
  - `requested_by_role`, `approved_by_role`, `rejected_by_role`, `executed_by_role`
  - `approved_at`, `rejected_at`, `executed_at`
  - `result` - Tool execution result
  - `error` - Error message if failed

**Relationship**: Agent → uses Tool → creates ToolRun (execution record)

---

### 3. Domain Management

#### **DomainConfig** (Domain Definition)
- **Purpose**: Groups agents and defines routing rules
- **Fields**:
  - `id`, `name`, `description`
  - `agents` - List of Agent IDs in this domain
  - `default_agent`, `fallback_agent`
  - `workflow_type` - "supervisor", "sequential", "parallel"
  - `routing_rules` - List of RoutingRule objects
  - `allowed_roles` - Who can access this domain
  - `max_iterations`, `version`
  - `is_active`, `metadata`

#### **RoutingRule** (Routing Logic)
- **Purpose**: Defines how to route requests to agents
- **Fields**:
  - `keywords` - Trigger keywords (e.g., ["code", "implement"])
  - `agent` - Target agent ID
  - `priority` - Lower = higher priority

**Workflow**:
1. User sends message in domain
2. DomainConfig routing rules evaluate keywords
3. Best matching Agent (or default) is selected
4. Agent processes request with assigned Tools

---

### 4. Conversation & Messages

#### **Conversation** (Chat Session)
- **Purpose**: Groups messages in a chat session
- **Fields**:
  - `id`, `domain_id`, `title`
  - `created_by_role`, `created_by_sub` - User identity
  - `created_at`, `updated_at`, `metadata`

#### **Message** (Single Message)
- **Purpose**: Individual message in conversation
- **Fields**:
  - `id`, `conversation_id`, `role`
  - `content` - Message text
  - `created_at`, `metadata`

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────┐
│                 USER INTERACTION                     │
└─────────────────────────────────────────────────────┘
                        ↓
            ┌─────────────────────────┐
            │   Conversation          │
            │  (chat session)         │
            └─────────────────────────┘
                        ↓
            ┌─────────────────────────┐
            │   Message               │
            │  (individual message)   │
            └─────────────────────────┘
                        ↓
        ┌─────────────────────────────────┐
        │  DomainConfig                   │
        │  (routing rules)                │
        └─────────────────────────────────┘
                        ↓
            ┌─────────────────────────┐
            │   Agent                 │
            │  (config-defined)       │
            └─────────────────────────┘
                        ↓
        ┌─────────────────────────────────┐
        │   Tool                          │
        │  (executable tool)              │
        └─────────────────────────────────┘
                        ↓
            ┌─────────────────────────┐
            │   ToolRun               │
            │  (execution record)     │
            └─────────────────────────┘
```

---

## Data Flow Example

### 1. Configuration Loading
```yaml
# domains/software_development.yaml
domain:
  id: software_development
  agents: [planner, coder, tester]
  routing_rules:
    - keywords: [code, implement]
      agent: coder
```

↓ (YAML Loader) ↓

```python
DomainConfig(
  id="software_development",
  agents=["planner", "coder", "tester"],
  routing_rules=[RoutingRule(keywords=["code", "implement"], agent="coder")]
)
```

### 2. Request Handling
```
User Message: "Write a Python function to calculate factorial"
                            ↓
                DomainConfig.get_agent_for_keywords(
                  keywords=["write", "python", "function"]
                )
                            ↓
                Returns: "coder" (matches routing rule)
                            ↓
                Agent(id="coder").can_handle(...)
                            ↓
                Agent executes with available tools:
                  - save_file (requires approval)
                  - search_memory
                            ↓
                ToolRun(tool_id="save_file", status=PENDING_APPROVAL)
                            ↓
                [Human approves]
                            ↓
                ToolRun(status=EXECUTED, result={...})
```

---

## No Conflicts - Summary

✅ **Agent** and **RegisteredAgent** don't conflict:
- Agent = static config-based
- RegisteredAgent = dynamic runtime-based
- Both use same state machine (AgentState)

✅ **Tool** and **ToolRun** don't conflict:
- Tool = tool definition (what can be done)
- ToolRun = execution record (what was done)

✅ **DomainConfig** uniquely manages:
- Agent grouping
- Routing logic
- Access control

✅ **Conversation** and **Message** uniquely manage:
- Chat sessions
- Message history
- User context

---

## Implementation Notes

### Loading Configuration
```python
from src.infrastructure.config import YamlConfigLoader

loader = YamlConfigLoader("configs/")
domain = loader.load_domain("software_development")
agent = loader.load_agent("coder")
tools = loader.load_tools()
```

### Storing in Database
```python
# Repositories use these entities
domain_repo.save(domain)          # Stores DomainConfig
agent_repo.save(agent)            # Stores Agent
tool_repo.save(tool)              # Stores Tool
tool_run_repo.save(tool_run)      # Stores ToolRun
```

### Using in Orchestration
```python
# Route based on domain + keywords
agent_id = domain.get_agent_for_keywords(user_keywords)
agent = agent_repo.find_by_id(agent_id)

# Execute tools
tools = tool_repo.find_by_agent(agent_id)
tool_run = ToolRun(tool_id=tool.id, ...)
tool_run_repo.save(tool_run)
```

---

## Testing Strategy

Tests are organized by entity:

1. **Value Objects** (test_entities.py)
   - AgentState transitions
   - SemanticVersion comparisons
   - ToolRunStatus transitions

2. **Entities** (test_entities.py)
   - Agent creation, promotion, capability checking
   - DomainConfig routing logic
   - Tool parameter validation
   - ToolRun approval/rejection

3. **Repositories** (test_repositories.py)
   - CRUD operations for each entity
   - Query operations (find_by_*, list_by_*)

4. **Use Cases** (test_use_cases.py)
   - Request/Response flows
   - Integration between entities

---
