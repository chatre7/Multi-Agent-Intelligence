# Phase 7: Enhanced Features & Performance Roadmap

**Status:** Planning Phase
**Target Duration:** 3-4 weeks
**Priority:** Medium-High

---

## Overview

Phase 7 builds on the complete Phase 6 implementation with focus on:
1. **Settings Tab Implementation** - User preferences & configuration
2. **Dark Mode Support** - Theme switching system-wide
3. **Performance Optimization** - Bundle size, rendering, caching
4. **Real-time Updates** - WebSocket for metrics & events
5. **Advanced Analytics** - Audit logs, trends, reporting

---

## Sprint 1: Settings Tab & Dark Mode (Week 1)

### Sprint 1.1: Settings Tab Implementation

**Deliverables:**
- [ ] `SettingsPage.tsx` - Settings interface
- [ ] User preference store
- [ ] API for preference persistence
- [ ] Settings categories:
  - System (Auto-refresh interval, notifications)
  - UI (Theme, language, timezone)
  - Export (Metrics format, schedule)

**Files to Create:**
```
frontend/src/
├── presentation/components/admin/
│   └── SettingsPanel.tsx              (Component groups)
│
├── infrastructure/stores/
│   └── userPreferencesStore.ts        (Zustand store)
│
└── presentation/pages/
    └── SettingsPage.tsx               (Full settings page)

backend/src/
└── application/services/
    └── user_preferences_service.py    (Preference management)
```

**Settings Categories:**

```typescript
interface UserPreferences {
  // System Settings
  autoRefreshInterval: number          // milliseconds (default: 5000)
  enableNotifications: boolean          // default: true
  notificationTypes: {
    toolApproval: boolean
    agentStateChange: boolean
    systemAlert: boolean
  }
  
  // UI Settings
  theme: 'light' | 'dark' | 'auto'     // default: 'auto'
  language: string                      // default: 'en'
  timezone: string                      // default: 'UTC'
  
  // Export Settings
  defaultExportFormat: 'csv' | 'json'   // default: 'csv'
  autoExport: boolean                   // default: false
  exportSchedule: 'daily' | 'weekly'    // if autoExport enabled
  
  // Advanced
  enableBetaFeatures: boolean           // default: false
  analyticsConsent: boolean             // default: false
}
```

### Sprint 1.2: Dark Mode Implementation

**Deliverables:**
- [ ] TailwindCSS dark mode configuration
- [ ] Theme context/store
- [ ] System theme detection
- [ ] Theme toggle component
- [ ] Persist theme preference

**Files to Create:**
```
frontend/
├── tailwind.config.js                 (Updated with darkMode)
├── src/infrastructure/stores/
│   └── themeStore.ts                 (Zustand theme store)
└── src/presentation/components/
    └── ThemeToggle.tsx               (Toggle button)
```

**Theme Implementation:**

```typescript
// tailwind.config.js
export default {
  darkMode: 'class',  // or 'media' for system preference
  theme: {
    extend: {
      colors: {
        dark: {
          50: '#f9fafb',
          900: '#111827',
          // ... full palette
        }
      }
    }
  }
}

// Usage in components
<div className="bg-white dark:bg-gray-900">
  Light mode: white, Dark mode: dark gray
</div>
```

**TailwindCSS Dark Mode Classes:**

All existing classes can use `dark:` prefix:
```
bg-white → dark:bg-gray-900
text-gray-900 → dark:text-white
border-gray-200 → dark:border-gray-800
```

---

## Sprint 2: Performance Optimization (Week 2)

### Sprint 2.1: Code Splitting with Dynamic Imports

**Current Bundle:** 671.95 kB (gzip: 203.28 kB)
**Target:** <500 kB (gzip: <150 kB)

**Strategy:**

1. **Route-based Code Splitting**
   ```typescript
   // Before
   import AdminPage from './pages/AdminPage'
   
   // After
   const AdminPage = lazy(() => import('./pages/AdminPage'))
   ```

2. **Component-based Code Splitting**
   ```typescript
   // For heavy components
   const ToolApprovalModal = lazy(() => import('./ToolApprovalModal'))
   const MetricsChart = lazy(() => import('./MetricsChart'))
   ```

3. **Library Optimization**
   ```typescript
   // Only import what you need from libraries
   // Before
   import * as recharts from 'recharts'
   
   // After
   import { BarChart, Bar, XAxis } from 'recharts'
   ```

**Files to Update:**
- `frontend/src/App.tsx` - Add route-based splitting
- `frontend/src/presentation/pages/AdminPage.tsx` - Component splitting
- `vite.config.ts` - Optimize chunking

**Expected Impact:**
- Main bundle: 200-250 kB (from 671 kB)
- Admin chunk: 150-200 kB
- Shared vendors: 100-150 kB
- Page load time: <2s (from ~3s)

### Sprint 2.2: Component Memoization & Optimization

**Changes:**

```typescript
// Use React.memo for expensive components
export const MetricsChart = React.memo(({ data, title }) => {
  // Component won't re-render unless props change
}, (prev, next) => {
  // Custom comparison for complex props
  return JSON.stringify(prev) === JSON.stringify(next)
})

// Use useCallback for event handlers
const handleApprove = useCallback((runId: string) => {
  apiClient.approveToolRun(runId)
}, []) // Deps array

// Use useMemo for expensive calculations
const filteredAgents = useMemo(() => {
  return agents.filter(a => a.state === filterState)
}, [agents, filterState])
```

**Files to Update:**
- `frontend/src/presentation/components/admin/*.tsx`
- `frontend/src/presentation/pages/AdminPage.tsx`

### Sprint 2.3: API Call Optimization

**Deliverables:**
- [ ] Request deduplication
- [ ] Smarter caching strategy
- [ ] Batch API calls where possible

```typescript
// Deduplicate concurrent requests
class CachedApiClient {
  private pendingRequests = new Map()
  
  async listAgents() {
    const key = 'listAgents'
    
    // Return pending request if exists
    if (this.pendingRequests.has(key)) {
      return this.pendingRequests.get(key)
    }
    
    // Otherwise, make request
    const promise = apiClient.listAgents()
    this.pendingRequests.set(key, promise)
    
    try {
      return await promise
    } finally {
      this.pendingRequests.delete(key)
    }
  }
}
```

---

## Sprint 3: Real-time Updates via WebSocket (Week 2-3)

### Current Implementation: Polling
- Metrics refresh every 5 seconds
- Activity feed polls for updates
- Tool runs checked periodically
- **Issue:** Inefficient, delays in updates

### Target Implementation: WebSocket

**New Architecture:**

```
Admin Panel Components
        ↓
    Store (Zustand)
        ↓
    WebSocket Handler
        ↓
Backend WebSocket Server (/ws/admin)
        ↓
Metrics Service → Event Stream
Tool Run Service → Approvals
Activity Stream → Events
```

**Files to Create:**
```
frontend/src/infrastructure/
├── websocket/
│   ├── AdminWebSocketClient.ts        (NEW)
│   └── useAdminWebSocket.ts           (NEW hook)

backend/src/presentation/websocket/
└── admin_handler.py                   (NEW - admin WebSocket handler)
```

**Implementation:**

```typescript
// frontend/src/infrastructure/websocket/AdminWebSocketClient.ts
export class AdminWebSocketClient {
  private ws: WebSocket | null = null
  private messageHandlers: Map<string, Function[]> = new Map()
  
  connect(url: string) {
    this.ws = new WebSocket(url)
    
    this.ws.onmessage = (event) => {
      const { type, data } = JSON.parse(event.data)
      
      // Route to appropriate handler
      const handlers = this.messageHandlers.get(type) || []
      handlers.forEach(handler => handler(data))
    }
  }
  
  subscribe(type: string, callback: Function) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, [])
    }
    this.messageHandlers.get(type)?.push(callback)
  }
  
  disconnect() {
    this.ws?.close()
  }
}

// Usage in store
export const useMetricsStore = create((set) => {
  const client = new AdminWebSocketClient()
  
  client.subscribe('metrics_update', (metrics) => {
    set({ metrics })
  })
  
  client.subscribe('tool_run_status', (toolRun) => {
    set(state => ({
      toolRuns: state.toolRuns.map(t => 
        t.id === toolRun.id ? toolRun : t
      )
    }))
  })
  
  return { /* store */ }
})
```

**Backend WebSocket Handler:**

```python
# backend/src/presentation/websocket/admin_handler.py
from fastapi import WebSocket
import json
import asyncio

class AdminWebSocketManager:
    def __init__(self):
        self.connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
    
    async def broadcast_metrics(self, metrics_data):
        """Broadcast metrics to all connected clients"""
        message = {
            "type": "metrics_update",
            "data": metrics_data
        }
        for connection in self.connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                # Handle disconnection
                self.connections.remove(connection)
    
    async def broadcast_tool_run_status(self, tool_run):
        """Notify all clients of tool run status change"""
        message = {
            "type": "tool_run_status",
            "data": tool_run.to_dict()
        }
        # ... broadcast logic

# In FastAPI app
@app.websocket("/ws/admin")
async def websocket_admin_endpoint(websocket: WebSocket):
    manager = AdminWebSocketManager()
    await manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

**Real-time Events:**
- ✅ Metrics updates (every 1s instead of 5s)
- ✅ Tool run status changes (immediate)
- ✅ New activities (instant)
- ✅ Agent state changes (immediate)

---

## Sprint 4: Advanced Analytics & Audit Logs (Week 3-4)

### Sprint 4.1: Activity Audit Log

**New Component: `AuditLogPage.tsx`**

```typescript
interface AuditLogEntry {
  id: string
  timestamp: Date
  user_id: string
  action: string              // 'approve_tool', 'promote_agent', etc.
  resource_type: string       // 'tool_run', 'agent', 'domain'
  resource_id: string
  before_state?: any          // Previous state
  after_state?: any           // New state
  metadata?: Record<string, any>
}

// Query API
GET /v1/audit-logs?
  user_id=...&
  resource_type=...&
  action=...&
  date_from=...&
  date_to=...&
  limit=100&
  offset=0
```

**UI Features:**
- [ ] Filter by date range
- [ ] Filter by user
- [ ] Filter by action type
- [ ] Search by resource
- [ ] Export to CSV
- [ ] Pagination

### Sprint 4.2: Usage Analytics Dashboard

**New Component: `AnalyticsPage.tsx`**

```typescript
interface UsageAnalytics {
  period: 'day' | 'week' | 'month'
  
  // Agent metrics
  agent_calls: number
  agent_errors: number
  average_response_time: number
  
  // Tool metrics
  tool_runs_total: number
  tool_runs_approved: number
  tool_runs_rejected: number
  approval_rate: number         // % approved
  
  // Conversation metrics
  conversations_total: number
  messages_total: number
  average_messages_per_conversation: number
  
  // Cost metrics
  tokens_used: number
  estimated_cost: number
  tokens_per_conversation: number
  
  // System metrics
  uptime_percentage: number
  error_rate: number
  peak_usage_time: string
}
```

**Dashboard Sections:**
1. **Time Series Charts**
   - Messages over time
   - Tool approvals over time
   - Agent usage by type
   - Error rates over time

2. **Metrics Cards**
   - Total tokens used
   - Estimated cost
   - Success rate
   - Average response time

3. **Top Agents**
   - Most used agents
   - Error rates by agent
   - Performance ranking

4. **Export Options**
   - Daily report
   - Weekly report
   - Monthly report
   - Custom date range

---

## Sprint 5: Additional Enhancements (Week 4)

### Sprint 5.1: Keyboard Shortcuts

```typescript
// Keyboard shortcuts help
const SHORTCUTS = {
  '?': 'Show this help',
  'a': 'Go to Admin Panel',
  'c': 'Go to Chat',
  'g+d': 'Go to Domains tab',
  'g+a': 'Go to Agents tab',
  'g+t': 'Go to Tools tab',
  's': 'Focus search',
  'enter': 'Approve selected tool run',
  'esc': 'Close modal/panel',
}
```

**Implementation:**
- [ ] `useKeyboardShortcuts.ts` hook
- [ ] Shortcuts help modal
- [ ] Settings to customize shortcuts
- [ ] Global keyboard event handler

### Sprint 5.2: Filter & Search Persistence

```typescript
// Save filter state to localStorage
useEffect(() => {
  localStorage.setItem('agentFilters', JSON.stringify({
    domain: filterDomain,
    state: filterState,
    search: searchQuery
  }))
}, [filterDomain, filterState, searchQuery])

// Restore on mount
useEffect(() => {
  const saved = localStorage.getItem('agentFilters')
  if (saved) {
    const { domain, state, search } = JSON.parse(saved)
    setFilterDomain(domain)
    setFilterState(state)
    setSearchQuery(search)
  }
}, [])
```

### Sprint 5.3: Bulk Operations

**Tool Approval Bulk Actions:**
- [ ] Multi-select tool runs
- [ ] "Select All" checkbox
- [ ] Bulk approve/reject buttons
- [ ] Confirmation dialog
- [ ] Progress indicator

**Implementation:**
```typescript
interface BulkToolRunState {
  selectedIds: Set<string>
  isSelecting: boolean
}

// Actions
const toggleSelect = (id: string) => {
  setSelected(prev => {
    const next = new Set(prev)
    next.has(id) ? next.delete(id) : next.add(id)
    return next
  })
}

const bulkApprove = async () => {
  await Promise.all(
    Array.from(selected).map(id => 
      apiClient.approveToolRun(id)
    )
  )
}
```

---

## Success Criteria

### Sprint 1: Settings & Dark Mode
- [ ] Settings tab fully functional
- [ ] All preferences persist
- [ ] Dark mode works across all pages
- [ ] Theme toggle works instantly
- [ ] No TypeScript errors
- [ ] Mobile responsive

### Sprint 2: Performance
- [ ] Bundle size <500 kB (main)
- [ ] Page load time <2s
- [ ] Component render time <50ms
- [ ] No performance regressions
- [ ] Lighthouse score >90

### Sprint 3: Real-time WebSocket
- [ ] Metrics update in <1s
- [ ] Tool run updates instant
- [ ] No unnecessary reconnects
- [ ] Graceful disconnect handling
- [ ] Backward compatible with polling

### Sprint 4: Analytics
- [ ] Audit logs comprehensive
- [ ] Analytics dashboard working
- [ ] Export to CSV functional
- [ ] Reports accurate
- [ ] Performance acceptable

### Sprint 5: Additional Features
- [ ] Keyboard shortcuts working
- [ ] Filter persistence working
- [ ] Bulk operations functional
- [ ] All features integrated
- [ ] No regression bugs

---

## Rollout Plan

### Staging Verification
1. Deploy to staging environment
2. Run full regression tests
3. Performance testing
4. Load testing
5. Security audit
6. User acceptance testing

### Production Rollout
1. Blue-green deployment
2. Monitor error rates
3. Check performance metrics
4. Collect user feedback
5. Hotfix issues as needed

### Rollback Plan
- Keep Phase 6 version running
- Switch traffic back if needed
- Restore database from snapshot
- Communication plan

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| WebSocket connection issues | Medium | High | Fallback to polling, retry logic |
| Performance regression | Low | High | Load testing, monitoring |
| User preference data loss | Low | Medium | Database backup, validation |
| Bulk operation timeout | Medium | Medium | Progress tracking, partial success |
| Dark mode readability issues | Low | Medium | User testing, accessibility audit |

---

## Timeline

```
Week 1:
  Mon-Tue: Settings tab implementation
  Wed-Thu: Dark mode implementation
  Fri: Testing and polish

Week 2:
  Mon-Tue: Code splitting & optimization
  Wed-Thu: Component memoization
  Fri: Performance testing

Week 2-3:
  Mon-Tue: WebSocket implementation (frontend)
  Wed-Thu: WebSocket implementation (backend)
  Fri: Integration testing

Week 3-4:
  Mon-Tue: Audit logs implementation
  Wed-Thu: Analytics dashboard
  Fri: Additional features

Week 4:
  Mon-Tue: Final testing & bug fixes
  Wed: Staging deployment
  Thu: Load testing
  Fri: Production rollout
```

---

## Estimated Effort

| Feature | Days | Priority |
|---------|------|----------|
| Settings Tab | 2 | High |
| Dark Mode | 2 | High |
| Code Splitting | 2 | High |
| Component Optimization | 2 | Medium |
| WebSocket | 3 | Medium |
| Audit Logs | 2 | Medium |
| Analytics | 2 | Medium |
| Keyboard Shortcuts | 1 | Low |
| Filter Persistence | 1 | Low |
| Bulk Operations | 2 | Low |
| Testing & Polish | 3 | High |
| **Total** | **22 days** | |

**Recommended:** 3-4 person team, 1 month timeline

---

## Dependencies

### External
- Ollama service (existing)
- SQLite database (existing)
- Prometheus metrics (existing)

### Internal
- Phase 1-6 completion ✅
- Backend API enhancements (WebSocket)
- Frontend store updates (Zustand)

---

## Documentation

Create for Phase 7:
- [ ] Settings configuration guide
- [ ] Dark mode customization guide
- [ ] Performance optimization tips
- [ ] WebSocket architecture docs
- [ ] Audit log query examples
- [ ] Analytics dashboard guide
- [ ] Keyboard shortcuts reference

---

## Conclusion

Phase 7 focuses on **user experience** and **system reliability** enhancements. By implementing these features, the platform will be more:

✅ **User-friendly** - Settings, dark mode, shortcuts  
✅ **Efficient** - Optimized bundle, real-time updates  
✅ **Observable** - Complete audit trail, analytics  
✅ **Scalable** - Optimized for growth, monitoring  

**Expected Outcome:** Enterprise-grade admin platform ready for widespread adoption.

---

**Prepared by:** Claude AI Code Assistant  
**Date:** January 22, 2026  
**Status:** Planning Phase - Ready for Approval
