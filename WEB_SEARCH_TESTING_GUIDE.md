# Web Search Tool Testing Guide

## 🎯 Quick Test Commands

### 1. Full Integration Test
```bash
python test_web_search_integration.py
```
**What it tests:** Complete system integration, MCP registration, cache, budget, permissions

### 2. MCP Tools Check
```bash
python -c "from mcp_server import get_mcp_server; s=get_mcp_server(); print('Tools:', [t['name'] for t in s.list_tools() if 'web' in t['name']])"
```
**Expected output:** `['web_search', 'web_search_with_domain']`

### 3. Direct Search Test
```bash
python -c "from search_provider import perform_web_search; print(perform_web_search('test query', 2, None, 'developer', 'user'))"
```
**What it shows:** Search functionality with caching and cost tracking

### 4. Cache System Test
```bash
python test_budget_demo.py
```
**What it shows:** Budget status and permission checking

### 5. Agent Integration Test
```bash
python -c "
# Test that agents can use web search
from planner_agent_team_v3 import get_next_speaker_router
router = get_next_speaker_router()
context = router.analyze_message_context('Check latest FastAPI docs')
print(f'Context analysis: {context}')
"
```

## 🧪 Manual Testing Scenarios

### Scenario 1: Basic Web Search
```bash
# Test general web search
python -c "
from search_provider import perform_web_search
result = perform_web_search('Python async best practices', 3, None, 'developer', 'test_user')
print('Search completed successfully!')
print(f'Result length: {len(result)} characters')
"
```

### Scenario 2: Domain-Specific Search
```bash
# Test domain filtering
python -c "
from search_provider import perform_domain_search
result = perform_domain_search('FastAPI middleware', 'docs.python.org', 2, 'developer', 'test_user')
print('Domain search completed!')
print(f'Result preview: {result[:200]}...')
"
```

### Scenario 3: Budget Monitoring
```bash
# Test budget notifications
python -c "
from search_cost_manager import get_search_cost_manager
manager = get_search_cost_manager()
print('Budget before:', manager.get_budget_status()['usage_today'])

# Simulate some usage
for i in range(3):
    manager.track_cost(f'test_query_{i}', 'duckduckgo', 5)

print('Budget after:', manager.get_budget_status()['usage_today'])
"
```

### Scenario 4: Permission Testing
```bash
python -c "
from search_cost_manager import get_search_cost_manager
manager = get_search_cost_manager()

# Test different roles
roles = ['admin', 'developer', 'user', 'guest']
for role in roles:
    can_search, reason = manager.can_perform_search(role, 'test_user')
    print(f'{role}: {can_search} - {reason}')
"
```

## 🔍 Advanced Testing

### Test with Real Agent Workflow
```bash
# Test planner agent with web search context
python -c "
from planner_agent_team_v3 import supervisor_node
from langchain_core.messages import HumanMessage

# Simulate a user request that should trigger web search
state = {
    'messages': [HumanMessage(content='Implement JWT authentication using the latest FastAPI best practices')],
    'sender': 'user',
    'next_agent': 'supervisor'
}

result = supervisor_node(state)
print('Supervisor routing decision:', result['next_agent'])
"
```

### Performance Testing
```bash
# Test cache performance
python -c "
import time
from search_provider import perform_web_search

# First search (cache miss)
start = time.time()
result1 = perform_web_search('Python performance tips', 3, None, 'developer', 'user')
time1 = time.time() - start

# Second search (cache hit)
start = time.time()
result2 = perform_web_search('Python performance tips', 3, None, 'developer', 'user')
time2 = time.time() - start

print(f'First search (cache miss): {time1:.2f}s')
print(f'Second search (cache hit): {time2:.2f}s')
print(f'Cache speedup: {time1/time2:.1f}x faster')
"
```

## 📊 Monitoring & Debugging

### Check System Status
```bash
# View cache statistics
python -c "from search_cache import get_search_cache; print(get_search_cache().get_stats())"

# View budget status
python test_budget_demo.py

# View MCP tools
python -c "from mcp_server import get_mcp_server; [print(f'{t[\"name\"]}: {t[\"description\"][:50]}...') for t in get_mcp_server().list_tools()]"
```

### Debug Issues
```bash
# Check for errors in search functionality
python -c "
try:
    from search_provider import perform_web_search
    result = perform_web_search('test', 1, None, 'developer', 'user')
    print('✅ Search working')
except Exception as e:
    print(f'❌ Search error: {e}')
"

# Validate configuration
python -c "
from search_config import SEARCH_CONFIG
print('Search config loaded successfully')
print(f'Provider: {SEARCH_CONFIG[\"provider\"]}')
print(f'Budget: ${SEARCH_CONFIG[\"daily_budget\"]}')
print(f'Permissions: {len(SEARCH_CONFIG[\"permissions\"])} roles')
"
```

## 🎯 Success Indicators

### ✅ System is Working If:
- Integration test passes: `python test_web_search_integration.py`
- MCP tools show: `web_search`, `web_search_with_domain`
- Search returns results with `[LIVE]` or `[CACHED]` indicators
- Budget stays within $5/day limit
- Cache hit ratio improves over time
- No permission errors for valid roles

### 🚨 Check These If Issues Occur:
- Cache file permissions: `data/search_cache.json`
- Budget file: `data/search_budget.json`
- MCP server initialization
- Network connectivity (for real search APIs)
- Python dependencies

## 🚀 Production Testing

Once confident with local testing, test in production environment:

1. **Deploy to staging environment**
2. **Monitor budget usage** over several days
3. **Test agent workflows** with real search queries
4. **Validate cache persistence** across restarts
5. **Monitor error rates** and user feedback

---

## 📞 Need Help?

If you encounter issues during testing:

1. **Run the integration test first**: `python test_web_search_integration.py`
2. **Check the logs** for error messages
3. **Verify file permissions** in the `data/` directory
4. **Test individual components** using the commands above

**Happy testing! 🎯🔍**