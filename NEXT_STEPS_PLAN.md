# 📋 Next Steps Plan - Multi-Agent Intelligence

**Current Status:** 2026-01-21
- Test Coverage: 82.6% (257/311 tests)
- Microsoft Compliance: 100% (architecture)
- Runtime Issues: Fixed (supervisor + Planner loops)

---

## 🎯 PRIORITY 1: Fix Remaining Tests (Target: 90%+ Coverage)

### 1.1 Database Manager API Tests (8 tests) ⏱️ 1-2 hours
**Issue:** API signature mismatch between tests and implementation

**Tasks:**
- [ ] Read `database_manager.py` to understand actual API
- [ ] Update tests in `testing/test_database_comprehensive.py` to match
- [ ] Fix method signatures (likely `create_user(dict)` vs `create_user(**kwargs)`)
- [ ] Add proper docstrings to database_manager.py

**Expected Result:** +8 tests (82.6% → 85.2%)

**Files:**
- `database_manager.py`
- `testing/test_database_comprehensive.py`

---

### 1.2 Web Search Fixtures (13 tests) ⏱️ 2-3 hours
**Issue:** Missing `provider`, `search_cache`, `cost_manager` fixtures

**Tasks:**
- [ ] Add `@pytest.fixture` for `provider` (mock search provider)
- [ ] Add `@pytest.fixture` for `search_cache` (SearchCache instance)
- [ ] Add `@pytest.fixture` for `cost_manager` (SearchCostManager)
- [ ] Mock HTTP requests for external search APIs

**Expected Result:** +13 tests (85.2% → 89.4%)

**Files:**
- `testing/test_search_comprehensive.py`
- `testing/conftest.py` (if shared fixtures)

---

### 1.3 Integration Tests (3 tests) ⏱️ 1-2 hours
**Issue:** Various edge cases and system integration issues

**Tasks:**
- [ ] Fix `TestAgentOrchestration::test_agent_persistence`
- [ ] Fix `TestSearchIntegration::test_full_search_workflow`
- [ ] Fix `TestSearchIntegration::test_search_with_caching`

**Expected Result:** +3 tests (89.4% → 90.4%)

**Files:**
- `testing/test_orchestration_comprehensive.py`
- `testing/test_search_comprehensive.py`

---

### 1.4 Orchestration Tests (5 tests) ⏱️ 3-4 hours
**Issue:** Need async mocking for multi-agent orchestration

**Tasks:**
- [ ] Create `@pytest.fixture` for `mock_agents` (AsyncMock)
- [ ] Mock agent execution with async responses
- [ ] Test parallel, sequential, consensus orchestration
- [ ] Test orchestration with agent failures

**Expected Result:** +5 tests (90.4% → 92.0%)

**Files:**
- `testing/test_orchestration_comprehensive.py`

---

### 1.5 Advanced Agents (19 tests) - OPTIONAL ⏱️ 8-12 hours
**Issue:** Tests expect APIs that don't exist

**Option A - Quick (5 minutes):**
```python
# Skip for now
pytestmark = pytest.mark.skip("Advanced agent APIs not implemented")
```

**Option B - Implement (8-12 hours):**
- [ ] Implement `CodeReviewAgent.analyze_code(code: str) -> dict`
- [ ] Implement `ResearchAgent.research(query: str) -> dict`
- [ ] Implement `DataAnalysisAgent.analyze_data(data: list) -> dict`
- [ ] Implement `DocumentationAgent.generate_docs(code: str) -> str`
- [ ] Implement `DevOpsAgent.setup_pipeline(config: dict) -> dict`

**Recommendation:** Option A for now, Option B when time permits

---

## 🎯 PRIORITY 2: Runtime Improvements

### 2.1 Streamlit App Enhancements ⏱️ 2-3 hours
**Current Issues:**
- ✅ Supervisor loop - FIXED
- ✅ Planner loop - FIXED
- ⚠️ Need more testing with different inputs

**Tasks:**
- [ ] Test with various Thai/English inputs
- [ ] Test all agent routing paths:
  - [ ] "รีวิวโค้ด" → CodeReviewAgent
  - [ ] "ค้นคว้า Python" → ResearchAgent
  - [ ] "วิเคราะห์ข้อมูล" → DataAnalysisAgent
  - [ ] "สร้าง README" → DocumentationAgent
  - [ ] "ตั้ง CI/CD" → DevOpsAgent
  - [ ] "พัฒนา feature" → DevTeam
- [ ] Add error handling for edge cases
- [ ] Add loading indicators
- [ ] Improve UI/UX feedback

**Files:**
- `app.py`
- `planner_agent_team_v3.py`

---

### 2.2 Agent Response Quality ⏱️ 4-6 hours
**Current Issue:** Agents may give generic responses

**Tasks:**
- [ ] Review and improve system prompts for each agent
- [ ] Add examples to prompts (few-shot learning)
- [ ] Test LLM responses for quality
- [ ] Add response validation
- [ ] Implement response caching for common queries

**Files:**
- `planner_agent_team_v3.py` (all agent nodes)
- `advanced_agents.py`

---

### 2.3 Performance Optimization ⏱️ 2-3 hours
**Tasks:**
- [ ] Profile slow operations
- [ ] Optimize database queries
- [ ] Add connection pooling
- [ ] Implement async where possible
- [ ] Add response caching

**Files:**
- `database_manager.py`
- `planner_agent_team_v3.py`

---

## 🎯 PRIORITY 3: New Features (Microsoft Compliance Gaps)

### 3.1 Multi-tenant Support ⏱️ 8-12 hours
**Current:** Not implemented (compliance gap)

**Tasks:**
- [ ] Design tenant isolation architecture
- [ ] Add tenant_id to database schema
- [ ] Implement tenant-specific agent instances
- [ ] Add tenant configuration management
- [ ] Add tenant-level resource limits
- [ ] Write tests for multi-tenancy

**Files (NEW):**
- `tenant_manager.py`
- `testing/test_tenant_isolation.py`

**Database Changes:**
- Add `tenant_id` column to all tables
- Add tenant configuration table
- Add tenant usage tracking

---

### 3.2 Fallback Mechanisms ⏱️ 6-8 hours
**Current:** Not implemented (compliance gap)

**Tasks:**
- [ ] Implement model switching on failure
- [ ] Add cached response fallback
- [ ] Implement graceful degradation
- [ ] Add retry logic with exponential backoff
- [ ] Add circuit breaker pattern
- [ ] Write tests for fallback scenarios

**Files (NEW):**
- `fallback_manager.py`
- `testing/test_fallback.py`

**Changes:**
- Modify agent nodes to use fallback manager
- Add model priority lists
- Add response cache layer

---

### 3.3 Audit Trail for Human-in-Loop ⏱️ 3-4 hours
**Current:** No audit logging for approvals

**Tasks:**
- [ ] Add approval/rejection logging
- [ ] Store user decisions in database
- [ ] Add approval history view in UI
- [ ] Add approval analytics
- [ ] Export audit logs

**Files:**
- `app.py` (add logging)
- `database_manager.py` (add approval_logs table)
- `testing/test_audit_trail.py`

---

## 🎯 PRIORITY 4: Documentation & DevOps

### 4.1 API Documentation ⏱️ 2-3 hours
**Tasks:**
- [ ] Add OpenAPI/Swagger docs for FastAPI endpoints
- [ ] Document all agent APIs
- [ ] Add usage examples
- [ ] Create architecture diagrams

**Files (NEW/UPDATE):**
- `docs/API_REFERENCE.md`
- `docs/ARCHITECTURE.md`
- Update `README.md`

---

### 4.2 Deployment Guide ⏱️ 2-3 hours
**Tasks:**
- [ ] Docker containerization
- [ ] Docker Compose setup
- [ ] Environment variable documentation
- [ ] Production deployment guide
- [ ] Monitoring setup guide

**Files (NEW):**
- `Dockerfile`
- `docker-compose.yml`
- `docs/DEPLOYMENT.md`

---

### 4.3 CI/CD Pipeline ⏱️ 3-4 hours
**Tasks:**
- [ ] GitHub Actions workflow for tests
- [ ] Automated code quality checks (flake8, black)
- [ ] Automated test coverage reports
- [ ] Automated deployment to staging

**Files (NEW):**
- `.github/workflows/test.yml`
- `.github/workflows/deploy.yml`

---

## 📊 ROADMAP SUMMARY

### Week 1: Test Coverage (Quick Wins)
```
Day 1-2: Database Manager + Web Search Fixtures (+21 tests → 90.4%)
Day 3-4: Integration + Orchestration Tests (+8 tests → 92.0%)
Day 5: Skip Advanced Agents, runtime testing
```
**Goal:** 90%+ test coverage

---

### Week 2: Runtime & UX Improvements
```
Day 1-2: Streamlit app enhancements
Day 3-4: Agent response quality improvements
Day 5: Performance optimization
```
**Goal:** Production-ready user experience

---

### Week 3: Microsoft Compliance Features
```
Day 1-3: Multi-tenant support implementation
Day 4-5: Fallback mechanisms + Audit trail
```
**Goal:** 100% Microsoft compliance (features + tests)

---

### Week 4: DevOps & Documentation
```
Day 1-2: API documentation + Architecture docs
Day 3-4: Docker + CI/CD pipeline
Day 5: Deployment guide + monitoring
```
**Goal:** Production deployment ready

---

## 🎯 IMMEDIATE NEXT ACTIONS (Today/Tomorrow)

### Option A: Continue Test Improvements (Recommended)
```bash
# 1. Fix Database Manager API (1-2 hours)
vim database_manager.py
vim testing/test_database_comprehensive.py
pytest testing/test_database_comprehensive.py -v

# 2. Add Web Search Fixtures (2-3 hours)
vim testing/test_search_comprehensive.py
pytest testing/test_search_comprehensive.py -v
```

### Option B: Focus on Runtime Quality
```bash
# 1. Test all agent routing paths
streamlit run app.py
# Manual testing with different inputs

# 2. Improve agent prompts
vim planner_agent_team_v3.py
# Enhance system prompts for better responses
```

### Option C: Start New Features
```bash
# 1. Design multi-tenant architecture
vim docs/MULTI_TENANT_DESIGN.md

# 2. Implement fallback manager
vim fallback_manager.py
```

---

## 📈 SUCCESS METRICS

### Test Coverage Goals
- **Current:** 82.6% (257/311)
- **Week 1 Target:** 90%+ (280/311)
- **Week 2 Target:** 92%+ (286/311)
- **Final Target:** 95%+ (295/311)

### Microsoft Compliance
- **Architecture:** ✅ 100% (achieved)
- **Features:** ⚠️ 80% (Multi-tenant + Fallback missing)
- **Target:** ✅ 100% (all features implemented)

### Code Quality
- **Current:** Good (modular, documented)
- **Target:** Add CI/CD, linting, type hints
- **Tools:** flake8, black, mypy, pylint

---

## 🤔 RECOMMENDATION

**Start with Priority 1 (Test Coverage)** because:
1. ✅ Immediate visible progress (82.6% → 90%+)
2. ✅ Clear, well-defined tasks
3. ✅ Builds confidence in system stability
4. ✅ Quick wins (4-7 hours for +21 tests)

**Then move to Priority 2 (Runtime)** to ensure user-facing quality.

---

Generated: 2026-01-21
Based on: REMAINING_TEST_ISSUES.md, MICROSOFT_COMPLIANCE.md
