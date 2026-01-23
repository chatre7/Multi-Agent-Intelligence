# Domain Workflow Strategy Configuration

## Summary

Updated domain configuration files to specify workflow strategies:

### 1. Software Development Domain
- **Workflow Type:** `orchestrator`
- **Strategy:** Deterministic pipeline
- **Pipeline:** `planner` → `coder` → `tester` → `reviewer`
- **Use Case:** Predictable code development with fixed agent sequence
- **Config:** [software_development.yaml](file:///d:/cmtn-project/Multi-Agent-Intelligence/backend/configs/domains/software_development.yaml)

### 2. Social Chat Domain
- **Workflow Type:** `few_shot`
- **Strategy:** LLM-based handoffs with examples
- **Max Handoffs:** 5
- **Default Agent:** `empath`
- **Use Case:** Flexible conversation flow with context-aware agent selection
- **Config:** [social_chat.yaml](file:///d:/cmtn-project/Multi-Agent-Intelligence/backend/configs/domains/social_chat.yaml)

## Configuration Schema

### Orchestrator Workflow
```yaml
metadata:
  workflow_type: orchestrator
  orchestration:
    strategy: deterministic
    pipeline: [agent1, agent2, agent3]
    continue_on_error: false
```

### Few-Shot Workflow
```yaml
metadata:
  workflow_type: few_shot
  few_shot:
    examples_enabled: true
    max_handoffs: 5
    handoff_confidence_threshold: 0.7
```

### Hybrid Workflow (Example)
```yaml
metadata:
  workflow_type: hybrid
  hybrid:
    orchestrator_decides: [planning, validation]
    llm_decides: [agent_selection, handoff_timing]
```

## Next Steps

1. ✅ Update domain configs with workflow_type metadata
2. 🔄 Update graph_builder.py to detect and use workflow strategies
3. ⏳ Test with real requests to each domain
