# Multi-Workflow Strategy System - Quick Start

## Overview

This system allows domains to use different workflow strategies:
- **Orchestrator**: Fixed agent pipeline (e.g., Plan → Code → Test → Review)
- **Few-Shot**: LLM-based handoffs (e.g., Empath → Comedian)
- **Hybrid**: Mix of both (e.g., Planning → LLM Selection → Validation)

## Usage

### 1. Configure Domain

Edit your domain YAML file:

```yaml
# Example: software_development.yaml
metadata:
  workflow_type: orchestrator
  orchestration:
    pipeline: [planner, coder, tester, reviewer]
```

or

```yaml
# Example: social_chat.yaml
metadata:
  workflow_type: few_shot
  few_shot:
    max_handoffs: 5
```

### 2. Automatic Detection

The system automatically detects `workflow_type` and uses the appropriate strategy:

```python
# In your code (no changes needed!)
builder = ConversationGraphBuilder()
graph = builder.build(domain, agents)

# Graph automatically uses:
# - OrchestratorStrategy if workflow_type="orchestrator"
# - FewShotStrategy if workflow_type="few_shot"
# - HybridStrategy if workflow_type="hybrid"
# - Supervisor (legacy) otherwise
```

## Configuration Examples

### Orchestrator
```yaml
metadata:
  workflow_type: orchestrator
  orchestration:
    strategy: deterministic
    pipeline: [agent1, agent2, agent3]
    continue_on_error: false
```

### Few-Shot
```yaml
metadata:
  workflow_type: few_shot
  few_shot:
    examples_enabled: true
    max_handoffs: 5
    handoff_confidence_threshold: 0.7
```

### Hybrid
```yaml
metadata:
  workflow_type: hybrid
  hybrid:
    orchestrator_decides: [planning, validation]
    llm_decides: [agent_selection, handoff_timing]
```

## Testing

```bash
cd backend

# Run unit tests (fast, ~8s)
uv run pytest tests/unit/infrastructure/workflows/ -v

# Run integration tests (~33s)
uv run pytest tests/integration/workflows/ -v

# Run all tests
uv run pytest tests/unit/infrastructure/workflows/ tests/integration/workflows/ -v
```

## Files

- **Implementation**: `backend/src/infrastructure/langgraph/workflow_strategies.py`
- **Integration**: `backend/src/infrastructure/langgraph/graph_builder.py`
- **Tests**: `backend/tests/unit/infrastructure/workflows/`
- **Configs**: `backend/configs/domains/*.yaml`
- **Full Docs**: `backend/docs/MULTI_WORKFLOW_IMPLEMENTATION.md`

## Support

See [MULTI_WORKFLOW_IMPLEMENTATION.md](./MULTI_WORKFLOW_IMPLEMENTATION.md) for complete documentation.
