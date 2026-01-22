# Phase 6 Admin Panel - Quick Start Guide

## 🚀 Quick Start (5 minutes)

### 1. Start Frontend Dev Server
```bash
cd frontend
npm run dev
```
This starts the Vite dev server on **http://localhost:5173**

### 2. Open in Browser
Navigate to: **http://localhost:5173**

### 3. Access Admin Panel
- Look for "Admin Panel" button in the top navigation
- Or navigate directly to the admin section (login required)

---

## 📋 What You'll See

### Admin Panel with 5 Tabs:

#### **1. Overview Tab** (Default)
```
┌─────────────────────────────────────────────┐
│  Admin Panel                    [Refresh]   │
├─────────────────────────────────────────────┤
│ [Overview] [Domains] [Agents] [Tools] [Settings]
├─────────────────────────────────────────────┤
│
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  │ Domains  │ │ Agents   │ │ Convs.   │ │ Pending  │
│  │    5     │ │   12     │ │    3     │ │    2     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘
│
│  ┌──────────────────────┐  ┌──────────────────────┐
│  │ Tool Run Distribution│  │ System Health        │
│  │ [Bar Chart]          │  │ ✅ Status: Healthy  │
│  │ Requested: 150       │  │ Auth: JWT            │
│  │ Approved: 140        │  │ DB: SQLite           │
│  │ Rejected: 10         │  │ Config: 5D/12A/20T   │
│  └──────────────────────┘  └──────────────────────┘
│
│  ┌──────────────────────────────────────────────┐
│  │ Recent Activity                              │
│  │ 🟢 Tool run approved: save_file (2 mins)    │
│  │ 🔵 New conversation: AI Chat (5 mins)       │
│  │ 🔴 Tool run rejected: delete_file (10 mins) │
│  └──────────────────────────────────────────────┘
│
│  ┌──────────────────────────────────────────────┐
│  │ Metrics Summary                              │
│  │ Chat Messages: 150  | Requested: 45          │
│  │ Approved: 40       | Rejected: 5            │
│  │ Executed: 40       │                        │
│  └──────────────────────────────────────────────┘
│
└─────────────────────────────────────────────┘
```

#### **2. Domains Tab**
```
┌────────────────────────┬─────────────────────┐
│ Domain Search...       │ [Domain Detail]     │
├────────────────────────┤                     │
│ ◉ Software Dev         │ Name: Software Dev  │
│ • Data Analysis        │ ID: dom_123         │
│ • ML Pipeline          │ Agents: 5           │
│ • DevOps               │ ├─ Planner          │
│ • Security             │ ├─ Coder            │
│                        │ ├─ Reviewer         │
│                        │ ├─ Tester           │
│                        │ └─ Critic           │
└────────────────────────┴─────────────────────┘
```

#### **3. Agents Tab**
```
┌─────────────────────────────┬──────────────────┐
│ Search...                   │ [Agent Detail]   │
│ Domain: [All▼]              │                  │
│ State: [All▼]               │ Name: Planner    │
├─────────────────────────────┤ State: [PROD]    │
│ ◉ Planner (SoftDev, v1.2)  │ Version: 1.2.0   │
│ • Coder (SoftDev, v1.1)    │                  │
│ • Reviewer (SoftDev, v1.0) │ Capabilities:    │
│ • Tester (DataAnal, v2.1)  │ • Planning       │
│ • Analyst (DataAnal, v1.9) │ • Breakdown      │
│                             │ • Estimation    │
│                             │ • Risk Analysis │
│                             │                 │
│                             │ [Promote...]    │
└─────────────────────────────┴──────────────────┘
```

#### **4. Tool Approval Tab**
```
┌─────────────────────────────────────────────┐
│ Status: [Pending▼]                          │
├─────────────────────────────────────────────┤
│ Tool: save_file              [⏳ Pending]   │
│ ID: run_456                                 │
│ Parameters: { path: "out.txt", ... }        │
│ [✓ Approve] [✕ Reject]                     │
│                                             │
│ Tool: delete_file            [⏳ Pending]   │
│ ID: run_457                                 │
│ Parameters: { path: "/tmp/*", ... }         │
│ [✓ Approve] [✕ Reject]                     │
│                                             │
│ Tool: execute_script         [✅ Approved] │
│ ID: run_455                                 │
└─────────────────────────────────────────────┘
```

#### **5. Settings Tab**
- Coming in future phase

---

## 🎮 Interactive Features

### Metrics Dashboard
- **Auto-Refresh:** Updates every 5 seconds automatically
- **Manual Refresh:** Click the [Refresh] button in header
- **Last Updated:** Shows timestamp at top

### Domain Management
- **Search:** Type to filter domains
- **Click to View:** Select a domain to see details
- **Agents List:** See which agents are in the domain

### Agent Management
- **Search:** Find agents by name
- **Filter by Domain:** Select from dropdown
- **Filter by State:** DEVELOPMENT, TESTING, PRODUCTION, etc.
- **Promote Agent:** Click "Promote to X" button to advance state

### Tool Approval
- **Real-time List:** Updates every 5 seconds
- **Filter by Status:** See Pending/Approved/Rejected/Executed
- **Quick Approve/Reject:** Click buttons directly in list
- **Detailed View:** Click row for approval modal with options
- **Add Reason:** Provide rejection reason in modal

---

## 🔧 Keyboard Shortcuts

- **Tab:** Navigate between tabs
- **Enter:** Activate buttons/approve actions
- **Escape:** Close modals/panels

---

## 🐛 Troubleshooting

### Admin Panel Not Showing?
- Make sure you're logged in
- Look for "Admin Panel" link in navigation
- Check browser console for errors (F12)

### Data Not Loading?
- Backend may not be running - that's OK, UI shows placeholders
- Check console for API errors
- Verify backend is on http://localhost:8000

### Buttons Not Responding?
- Wait for previous request to complete
- Check for error messages (red boxes)
- Try manual refresh button

### Auto-Refresh Not Working?
- Check browser console
- Verify network tab for API calls
- Auto-refresh happens every 5 seconds

---

## 📊 Testing Without Backend

The UI is fully functional without backend! You can test:
- ✅ Tab navigation
- ✅ UI responsiveness
- ✅ Component rendering
- ✅ Loading states
- ✅ Error messages
- ✅ Search/filter interactions

You'll just see empty lists and loading skeletons, which is expected.

---

## 🔌 Testing With Backend

Once backend is running on **http://localhost:8000**:
- 🟢 Metrics will populate with real data
- 🟢 Domains/Agents will load from database
- 🟢 Tool approvals will show real pending runs
- 🟢 Actions (approve/reject/promote) will work

### Start Backend:
```bash
cd backend
python -m uvicorn src.presentation.api.app:create_app --reload
```

---

## 📚 Component Reference

### Overview Tab Components
- `StatCard` - 4x KPI cards
- `MetricsChart` - Bar chart
- `ActivityFeed` - Event list
- System Health Panel

### Domains Tab Components
- `DomainList` - Search & list
- `DomainDetail` - Side panel

### Agents Tab Components
- `AgentList` - Search & filter
- `AgentDetail` - Side panel with promote

### Tools Tab Components
- `ToolRunList` - List with inline actions
- `ToolApprovalModal` - Approval dialog

---

## 🎨 UI Features

### Responsive Design
- **Mobile:** Single column, scrollable
- **Tablet:** 2 columns with panels
- **Desktop:** Full layout with side panels

### Color Coding
- **States:** 
  - Green = PRODUCTION
  - Yellow = TESTING
  - Gray = DEVELOPMENT
  - Orange = DEPRECATED
  - Red = ARCHIVED
  
- **Status:**
  - Green = Approved ✓
  - Red = Rejected ✕
  - Yellow = Pending ⏳
  - Blue = Executed ✔

### Loading States
- Skeleton screens while loading
- Spinners on buttons
- Disabled states during actions

### Error Handling
- Red error banners
- Console error logs
- Fallback empty states

---

## 📞 Support

For issues or questions:
1. Check browser console (F12 → Console tab)
2. Verify backend is running
3. Check API responses in Network tab
4. Review PHASE_6_COMPLETE.md for details

---

**Ready to explore? Open http://localhost:5173 and click Admin Panel! 🚀**
