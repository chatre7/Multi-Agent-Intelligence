# Remaining Test Issues

**Status:** 257/311 tests passing (82.6%)
**Remaining:** 48 tests (34 failures + 14 errors)
**Date:** 2026-01-21

---

## Summary

After fixing 25 tests in this session, 48 tests remain that require attention. These fall into 5 main categories with different root causes and recommended approaches.

---

## 1. Advanced Agents Tests (19 failures)

### Issue: Test-Code API Mismatch

**Location:** `testing/test_agents_comprehensive.py`

**Problem:**
Tests expect methods that don't exist in the actual implementation:
- `CodeReviewAgent.analyze_code(code: str) -> dict`
- `ResearchAgent.research(query: str) -> dict`
- `DataAnalysisAgent.analyze_data(data: list) -> dict`
- `DocumentationAgent.generate_docs(code: str) -> str`
- `DevOpsAgent.setup_pipeline(config: dict) -> dict`

**Current Implementation:**
These agents inherit from `SpecializedAgent` which has:
- `get_system_prompt()` - Returns prompt template
- `_calculate_confidence(response: str)` - Calculates confidence score
- No specific methods for task execution (LLM interaction is implicit)

**Failing Tests:**
```
✗ TestCodeReviewAgent::test_clean_code_review
✗ TestCodeReviewAgent::test_problematic_code_review
✗ TestCodeReviewAgent::test_unsupported_language
✗ TestCodeReviewAgent::test_research_integration
✗ TestResearchAgent::test_successful_research
✗ TestResearchAgent::test_research_with_budget_limit
✗ TestResearchAgent::test_research_timeout_handling
✗ TestDataAnalysisAgent::test_standard_data_analysis
✗ TestDataAnalysisAgent::test_data_with_anomalies
✗ TestDataAnalysisAgent::test_invalid_data_handling
✗ TestDataAnalysisAgent::test_empty_data
✗ TestDocumentationAgent::test_code_documentation
✗ TestDocumentationAgent::test_api_documentation
✗ TestDocumentationAgent::test_documentation_update
✗ TestDevOpsAgent::test_deployment_pipeline_setup
✗ TestDevOpsAgent::test_infrastructure_provisioning
✗ TestDevOpsAgent::test_monitoring_setup
✗ TestAgentOrchestration::test_agent_selection_logic
✗ TestAgentOrchestration::test_agent_performance_tracking
```

**Recommended Solutions:**

### Option A: Skip Non-Implemented Tests (Quick Fix)
```python
@pytest.mark.skip(reason="API not implemented - tests written before implementation")
def test_analyze_code(self, agent):
    """Test code analysis functionality."""
    ...
```

**Pros:**
- Quick (5 minutes)
- Keeps tests as documentation of intended API
- Can be un-skipped when API is implemented

**Cons:**
- Doesn't actually improve code coverage
- Tests still exist but provide no value

### Option B: Implement Missing Methods (Complete Fix)
```python
class CodeReviewAgent(SpecializedAgent):
    def analyze_code(self, code: str, language: str = "python") -> dict:
        """Analyze code for issues and improvements."""
        prompt = f"""Analyze this {language} code:

{code}

Provide:
1. Security vulnerabilities
2. Code quality issues
3. Performance problems
4. Improvement suggestions

Format as JSON with structure:
{{
    "issues": [...],
    "severity": "low|medium|high",
    "suggestions": [...]
}}
"""
        response = self.llm.invoke(prompt)
        # Parse LLM response into structured dict
        return self._parse_review_response(response.content)
```

**Pros:**
- Tests become valuable
- API becomes usable
- Better code quality

**Cons:**
- Time-consuming (2-4 hours per agent)
- Requires LLM response parsing logic
- May need mocking for reliable tests

### Option C: Mock LLM for Tests (Test-Only Fix)
```python
@patch('advanced_agents.ChatOllama')
def test_code_review(self, mock_llm, agent):
    """Test code review with mocked LLM."""
    mock_response = MagicMock()
    mock_response.content = '{"issues": [], "severity": "low"}'
    mock_llm.return_value.invoke.return_value = mock_response

    result = agent.analyze_code("def foo(): pass")
    assert result["severity"] == "low"
```

**Pros:**
- Tests pass consistently
- Fast test execution
- No real LLM needed

**Cons:**
- Still need to implement methods
- Mocking logic can be complex
- Tests don't verify actual LLM quality

**Recommendation:** Start with Option A (skip), then do Option B when time permits.

---

## 2. Database Manager Tests (8 failures)

### Issue: API Signature Mismatch

**Location:** `testing/test_database_comprehensive.py`

**Problem:**
Tests call methods with different signatures than implementation:

**Test Expectations:**
```python
# Tests expect keyword arguments
db.create_user(username="foo", email="bar", ...)
db.get_user_by_id(user_id="123")
db.create_conversation(thread_id="abc", ...)
```

**Actual Implementation:**
```python
# Check actual method signatures in database_manager.py
# May use positional args or different parameter names
```

**Failing Tests:**
```
✗ TestDatabaseManager::test_user_crud_operations
✗ TestDatabaseManager::test_user_duplicate_creation
✗ TestDatabaseManager::test_conversation_operations
✗ TestDatabaseManager::test_agent_metrics
✗ TestDatabaseManager::test_concurrent_operations
✗ TestDatabaseManager::test_database_stats
✗ TestDatabaseManager::test_error_handling
✗ TestDatabaseManager::test_search_cache_operations
```

**Recommended Solution:**

1. **Audit DatabaseManager API:**
```bash
grep -n "def create_user\|def get_user\|def create_conversation" database_manager.py
```

2. **Update Tests to Match:**
```python
# Find actual signature
def create_user(self, user_data: dict) -> str:
    ...

# Update test
def test_user_crud_operations(self, temp_db):
    user_data = {
        "username": "test",
        "email": "test@example.com",
        ...
    }
    user_id = temp_db.create_user(user_data)
    assert user_id is not None
```

3. **Add Database Documentation:**
```python
# In database_manager.py docstrings
def create_user(self, user_data: dict) -> str:
    """Create a new user.

    Parameters
    ----------
    user_data : dict
        User data with keys: username, email, password_hash, role

    Returns
    -------
    str
        User ID

    Example
    -------
    >>> db.create_user({
    ...     "username": "alice",
    ...     "email": "alice@example.com",
    ...     "password_hash": "...",
    ...     "role": "user"
    ... })
    'user_123'
    """
```

**Estimated Time:** 1-2 hours

---

## 3. Web Search Tests (13 errors)

### Issue: Missing Test Fixtures

**Location:** `testing/test_search_comprehensive.py`

**Problem:**
```
ERROR at setup of TestSearchFunctions.test_successful_search
fixture 'provider' not found
```

Tests expect a `provider` fixture that provides a mocked search provider, but it's not defined.

**Failing Tests:**
```
✗ TestSearchFunctions::test_successful_search
✗ TestSearchFunctions::test_search_with_domain_filter
✗ TestSearchFunctions::test_search_error_handling
✗ TestSearchFunctions::test_search_timeout
✗ TestSearchCache::test_cache_miss_and_store
✗ TestSearchCache::test_cache_expiration
✗ TestSearchCache::test_cache_invalidation
✗ TestSearchCache::test_cache_stats
✗ TestSearchCostManager::test_budget_check
✗ TestSearchCostManager::test_cost_recording
✗ TestSearchCostManager::test_budget_reset
✗ TestSearchCostManager::test_user_isolation
✗ TestSearchCostManager::test_cost_limits_enforcement
```

**Recommended Solution:**

Add fixtures to `testing/test_search_comprehensive.py`:

```python
@pytest.fixture
def provider():
    """Mock search provider for testing."""
    from unittest.mock import MagicMock

    provider = MagicMock()
    provider.search.return_value = {
        "results": [
            {
                "title": "Test Result",
                "url": "https://example.com",
                "snippet": "Test snippet"
            }
        ],
        "total": 1
    }
    return provider

@pytest.fixture
def search_cache():
    """Mock search cache for testing."""
    from search_provider import SearchCache  # Adjust import
    cache = SearchCache()
    yield cache
    cache.clear()

@pytest.fixture
def cost_manager():
    """Mock cost manager for testing."""
    from search_provider import SearchCostManager  # Adjust import
    manager = SearchCostManager()
    yield manager
    manager.reset()
```

**Alternative:** Mock HTTP requests:
```python
@pytest.fixture
def mock_search_api(monkeypatch):
    """Mock external search API."""
    def mock_get(*args, **kwargs):
        response = MagicMock()
        response.json.return_value = {
            "items": [{"title": "Test", "link": "https://test.com"}]
        }
        response.status_code = 200
        return response

    monkeypatch.setattr("requests.get", mock_get)
```

**Estimated Time:** 2-3 hours

---

## 4. Orchestration Tests (5 failures)

### Issue: Agent Coordination Logic

**Location:** `testing/test_orchestration_comprehensive.py`

**Problem:**
Tests for multi-agent orchestration strategies need mocked agent responses and coordination logic.

**Failing Tests:**
```
✗ TestOrchestrationStrategies::test_agent_selection_integration
✗ TestOrchestrationStrategies::test_parallel_orchestration
✗ TestOrchestrationStrategies::test_consensus_orchestration
✗ TestOrchestrationStrategies::test_orchestration_with_agent_failure
✗ TestOrchestrationStrategies::test_performance_tracking
```

**Recommended Solution:**

Mock agent execution:
```python
@pytest.fixture
def mock_agents():
    """Create mock agents for orchestration testing."""
    from unittest.mock import AsyncMock

    agent1 = AsyncMock()
    agent1.execute.return_value = {"result": "Agent 1 response"}
    agent1.name = "Agent1"

    agent2 = AsyncMock()
    agent2.execute.return_value = {"result": "Agent 2 response"}
    agent2.name = "Agent2"

    return [agent1, agent2]

@pytest.mark.asyncio
async def test_parallel_orchestration(mock_agents):
    """Test parallel agent execution."""
    orchestrator = ParallelOrchestrator()
    results = await orchestrator.execute(mock_agents, task="test")

    assert len(results) == 2
    assert all(r["result"] for r in results)
```

**Estimated Time:** 3-4 hours

---

## 5. Integration/Edge Cases (3 tests)

### Issue: System Integration & Minor Edge Cases

**Failing Tests:**
```
✗ TestAgentOrchestration::test_agent_persistence (1 error)
✗ TestSearchIntegration::test_full_search_workflow (1 failure)
✗ TestSearchIntegration::test_search_with_caching (1 failure)
```

**Recommended Solution:**
- Review individual test failures
- Fix based on specific error messages
- May be quick fixes (15-30 min each)

**Estimated Time:** 1-2 hours

---

## Priority Recommendations

### High Priority (Do First)
1. **Database Manager API** (8 tests) - Clear API mismatch, straightforward fix
2. **Web Search Fixtures** (13 tests) - Just need fixtures added
3. **Integration Tests** (3 tests) - Quick individual fixes

**Estimated Time:** 4-7 hours total

### Medium Priority (Do Later)
4. **Orchestration Tests** (5 tests) - Need async mocking
5. **Advanced Agents** (19 tests) - Option A: Skip them for now

**Estimated Time:** 3-4 hours

### Low Priority (Future Enhancement)
- Implement full Advanced Agent APIs (Option B)
- Would be valuable but time-intensive (8-12 hours)

---

## Testing Best Practices for Future

1. **Write Tests After Implementation**
   - Tests currently assume APIs that don't exist
   - Better: Implement feature → Write tests → Iterate

2. **Use Test-Driven Development (TDD) Properly**
   - Write test → RED (fails)
   - Write minimal code → GREEN (passes)
   - Refactor → Still GREEN
   - Current tests skip the "implement to pass" step

3. **Document Expected APIs**
   - If tests define future API, mark with `@pytest.mark.skip("Not implemented")`
   - Add GitHub issue linking test to planned feature
   - Remove skip when implemented

4. **Mock External Dependencies**
   - Always mock: LLM calls, HTTP requests, databases
   - Use fixtures for consistent mock setup
   - Consider `pytest-mock` plugin

5. **Separate Unit vs Integration Tests**
   - Unit tests: Fast, isolated, mocked
   - Integration tests: Slower, use real services (optional)
   - Mark integration tests: `@pytest.mark.integration`

---

## Next Steps

### Option A: Quick Wins (4-7 hours)
```bash
# Fix Database Manager tests
vim testing/test_database_comprehensive.py

# Add Web Search fixtures
vim testing/test_search_comprehensive.py

# Fix integration tests
pytest testing/test_search_comprehensive.py::TestSearchIntegration -v
```

### Option B: Skip Advanced Tests (5 minutes)
```python
# In testing/test_agents_comprehensive.py
pytestmark = pytest.mark.skip("Advanced agent APIs not implemented yet")
```

### Option C: Document and Defer
```bash
# Create GitHub issues for each category
gh issue create --title "Implement Advanced Agent APIs" --body "See REMAINING_TEST_ISSUES.md"
gh issue create --title "Fix Database Manager test API mismatches"
gh issue create --title "Add Web Search test fixtures"
```

---

## Success Metrics

Current: **257/311 passing (82.6%)**

After quick wins:
- Database: +8 tests → **265/311 (85.2%)**
- Web Search: +13 tests → **278/311 (89.4%)**
- Integration: +3 tests → **281/311 (90.4%)**

After all fixes:
- **305/311 passing (98.1%)**
- Remaining 6 skipped (advanced features not implemented)

---

## Files to Reference

- Implementation: `advanced_agents.py`, `database_manager.py`, `search_provider.py`
- Tests: `testing/test_agents_comprehensive.py`, `testing/test_database_comprehensive.py`, `testing/test_search_comprehensive.py`
- Fixtures: `conftest.py` (pytest configuration)
- Documentation: `CODE_REVIEW_REPORT.md`, `README.md`

---

*Generated: 2026-01-21 by Claude Sonnet 4.5*
*Session improvement: +25 tests (74.6% → 82.6%)*
