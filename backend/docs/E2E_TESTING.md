# E2E Testing Guide

## Prerequisites
1. Start backend server
2. Configure domains with workflow_type

## Test Orchestrator Workflow

### 1. Start Backend
```bash
cd backend
uv run uvicorn src.presentation.main:app --reload
```

### 2. Test via API/WebSocket

**Using curl:**
```bash
# Send message to software_development domain (orchestrator)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "software_development",
    "message": "Build a REST API for user authentication"
  }'
```

**Expected Flow:**
```
User: "Build a REST API for user authentication"
  ↓
Planner: [Plans the architecture]
  ↓
Coder: [Writes the code]
  ↓
Tester: [Creates tests]
  ↓
Reviewer: [Reviews the implementation]
  ↓
Final Response: Complete implementation with review feedback
```

## Test Few-Shot Workflow

**Using curl:**
```bash
# Send message to social_chat domain (few-shot)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "social_chat",
    "message": "I feel sad today, can you cheer me up?"
  }'
```

**Expected Flow:**
```
User: "I feel sad today, can you cheer me up?"
  ↓
Empath: "I understand you're feeling sad. Let me get the Comedian..."
  ↓ (LLM decides to handoff)
Comedian: [Tells a joke to cheer you up]
  ↓
Final Response: Joke from comedian
```

## Verify Workflow Type

Check backend logs for:
```
[INFO] Using orchestrator workflow strategy for domain 'software_development'
```

or

```
[INFO] Using few_shot workflow strategy for domain 'social_chat'
```

## Debug

Enable verbose logging in `graph_builder.py`:
```python
print(f"[DEBUG] Workflow type: {workflow_type}")
print(f"[DEBUG] Strategy: {type(strategy).__name__}")
print(f"[DEBUG] Result: {result}")
```
