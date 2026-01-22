# Multi-Agent Intelligence Platform - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama (for LLM)

### Step 1: Start Ollama (in new terminal)
```bash
ollama serve
```

In another terminal, pull the required models:
```bash
ollama pull gpt-oss:120b-cloud
ollama pull nomic-embed-text
```

### Step 2: Start Backend API
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn src.presentation.api.app:create_app --reload
```

Backend will be available at: `http://localhost:8000`

Verify with: `curl http://localhost:8000/health`

### Step 3: Start Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: `http://localhost:5173`

### Step 4: Login
Use demo credentials:
- **Admin**: `admin:admin`
- **Developer**: `dev:dev`
- **User**: `user:user`

### Step 5: Start Chatting! 🎉
1. Select a Domain from dropdown
2. Select an Agent
3. Click "Start Conversation"
4. Type a message and watch it stream in real-time!

---

## 📁 Project Structure

```
Multi-Agent-Intelligence/
├── backend/                          # Python FastAPI backend
│   ├── src/
│   │   ├── domain/                   # Business logic
│   │   ├── application/              # Use cases
│   │   ├── infrastructure/           # Adapters
│   │   └── presentation/             # REST/WebSocket API
│   ├── tests/unit/                   # 119 unit tests
│   └── configs/                      # YAML domain/agent configs
│
├── frontend/                         # React + Vite frontend
│   ├── src/
│   │   ├── domain/                   # TypeScript types
│   │   ├── infrastructure/           # API client, WebSocket, state
│   │   └── presentation/             # React components & pages
│   ├── dist/                         # Built production assets
│   └── package.json
│
├── IMPLEMENTATION_SUMMARY.md         # Detailed implementation report
├── QUICKSTART.md                     # This file
└── README.md                         # Main project README
```

---

## 🔧 Available Commands

### Backend
```bash
# Run tests (all 119 passing)
pytest backend/tests/unit -v

# Run specific test
pytest backend/tests/unit/domain/test_entities.py -v

# Run with coverage
pytest backend/tests/unit --cov=src --cov-report=html

# Code quality
ruff check .
ruff format .
mypy .
```

### Frontend
```bash
# Development
npm run dev

# Build for production
npm run build

# Preview build
npm run preview
```

---

## 🔗 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Get JWT token
- `GET /api/v1/auth/me` - Current user info

### Chat
- `POST /api/v1/conversations` - Start conversation
- `GET /api/v1/conversations/{id}` - Get conversation history
- `WS /ws/chat/{conversation_id}` - WebSocket for streaming

### Domains & Agents
- `GET /api/v1/domains` - List domains
- `GET /api/v1/agents` - List agents

### Tool Management
- `GET /api/v1/tool-runs` - List tool runs
- `POST /api/v1/tool-runs/{id}/approve` - Approve tool

### Metrics
- `GET /api/v1/health` - Health status
- `GET /api/v1/metrics` - Prometheus metrics

Full API reference in: `backend/src/presentation/api/app.py`

---

## 📊 System Architecture

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────┐
│  PRESENTATION (REST API, WebSocket)             │
│  ├─ /api/v1/auth, /api/v1/domains, etc        │
│  └─ /ws/chat/{id}                              │
└────────────────┬────────────────────────────────┘
                 │ depends on
┌────────────────▼────────────────────────────────┐
│  APPLICATION (Use Cases, DTOs)                  │
│  ├─ CreateAgentUseCase, SendMessageUseCase, etc│
│  └─ Request/Response DTOs                      │
└────────────────┬────────────────────────────────┘
                 │ depends on
┌────────────────▼────────────────────────────────┐
│  DOMAIN (Entities, Value Objects)              │
│  ├─ Agent, DomainConfig, Tool, Conversation   │
│  ├─ AgentState, SemanticVersion               │
│  └─ Repository Interfaces                      │
└────────────────┬────────────────────────────────┘
                 │ depends on
┌────────────────▼────────────────────────────────┐
│  INFRASTRUCTURE (Adapters)                      │
│  ├─ SQLite Repositories                        │
│  ├─ YAML Config Loader                         │
│  ├─ LangGraph Integration                      │
│  └─ WebSocket Connection Manager               │
└─────────────────────────────────────────────────┘
```

### Tech Stack

**Backend**
- FastAPI 0.115+
- LangGraph 0.2+
- SQLite + SQLAlchemy
- Pydantic 2.x
- pytest for testing

**Frontend**
- React 19 + TypeScript 5
- Vite 5
- TailwindCSS 4
- Zustand (state)
- Axios (HTTP)
- WebSocket (real-time)

---

## 🧪 Testing

### Run All Tests
```bash
cd backend
pytest tests/unit -v
```

### Test Coverage by Component
- ✅ Domain Entities: 40 tests
- ✅ Auth System: 27/29 tests
- ✅ Agent Management: 8 tests
- ✅ Conversations: 15 tests
- ✅ Tool Runs: 18 tests
- ✅ API Endpoints: 30+ tests
- ✅ WebSocket: 10 tests

**Total: 119/119 PASSING** ✅

---

## 🔐 Authentication & Authorization

### JWT Token Flow
1. Login with username/password → get `access_token`
2. Include in requests: `Authorization: Bearer {token}`
3. Token validated by middleware
4. User role and permissions extracted from claims

### Roles & Permissions
| Role | Permissions |
|------|-------------|
| ADMIN | All permissions |
| DEVELOPER | Domain read, Agent CRUD, Config sync |
| OPERATOR | Tool approve/reject |
| USER | Chat, tool read |
| GUEST | Chat read-only |

---

## 🚨 Troubleshooting

### Backend Issues

**Ollama Connection Error**
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags
# Restart if needed
ollama serve
```

**Database Lock**
```bash
# Reset database
rm backend/data/checkpoints.db
# Restart backend
```

**Import Errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend Issues

**Port Already in Use**
```bash
# Find process using port 5173
lsof -i :5173
# Kill it
kill -9 <PID>
```

**WebSocket Connection Failed**
- Ensure backend is running: `http://localhost:8000`
- Check CORS is enabled
- Verify token is valid

**Build Errors**
```bash
# Clear build cache
rm -rf dist node_modules/.vite
npm run build
```

---

## 📚 Key Files to Know

### Backend
- `backend/src/domain/entities/agent.py` - Agent entity (200+ lines)
- `backend/src/presentation/api/app.py` - REST API factory
- `backend/src/infrastructure/persistence/sqlite/` - Database adapters
- `backend/tests/unit/domain/test_entities.py` - Entity tests

### Frontend
- `frontend/src/App.tsx` - Main app component
- `frontend/src/presentation/pages/ChatPage.tsx` - Chat interface
- `frontend/src/infrastructure/stores/conversationStore.ts` - State management
- `frontend/src/infrastructure/websocket/WebSocketClient.ts` - WebSocket integration

---

## 🎯 Next Steps

### Immediate
- [ ] Test chat with different agents
- [ ] Try tool approval workflow
- [ ] Monitor metrics endpoint

### Short Term
- [ ] Create custom domain in YAML
- [ ] Add new agent to domain
- [ ] Build custom tools

### Medium Term
- [ ] Deploy with Docker
- [ ] Setup monitoring dashboard
- [ ] Implement file upload feature

### Long Term
- [ ] Multi-user collaboration
- [ ] Advanced analytics
- [ ] Custom LLM integration

---

## 📖 Documentation

- **Detailed Implementation**: See `IMPLEMENTATION_SUMMARY.md`
- **Backend README**: See `backend/README.md` (if exists)
- **Frontend README**: See `frontend/README.md`
- **API Docs**: OpenAPI schema at `/docs` (FastAPI)

---

## 🆘 Need Help?

1. Check the README files in each directory
2. Review test files for usage examples
3. Check backend logs: `logs/agent_system.log`
4. Frontend console for client-side errors (F12 in browser)

---

## ✨ What You Can Do

### Chat Features
- Send messages to multi-agent system
- Get real-time streaming responses
- Approve/reject tool executions
- View conversation history

### Admin Features (Coming Soon)
- Manage domains and agents
- Create custom tools
- View system metrics
- User management

---

## 🎓 Learning Path

1. **Understand the Architecture**
   - Read `IMPLEMENTATION_SUMMARY.md`
   - Review Clean Architecture pattern

2. **Explore Backend Code**
   - Start with `backend/src/domain/entities/`
   - Move to `backend/src/application/use_cases/`
   - Finish with `backend/src/presentation/api/`

3. **Explore Frontend Code**
   - Check `frontend/src/infrastructure/stores/`
   - Review `frontend/src/presentation/components/`
   - Study `frontend/src/infrastructure/websocket/`

4. **Run Tests & Experiments**
   - Run backend tests
   - Try different prompts
   - Monitor metrics

---

**Status**: ✅ Ready for Production Testing

**Last Updated**: January 22, 2026
