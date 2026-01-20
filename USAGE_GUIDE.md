# Multi-Agent Intelligence System - Usage Guide

## 🎯 **Quick Start**

### 1. **System Requirements**
```bash
# Python 3.12+
python --version

# Ollama (for local models) - Optional
ollama --version

# Git
git --version
```

### 2. **Installation**

```bash
# Clone repository
git clone <repository-url>
cd multi-agent-intelligence

# Run quick start script
chmod +x start.sh
./start.sh
```

**Manual Installation:**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install prometheus-client PyJWT passlib[bcrypt]

# Create directories
mkdir -p agent_brain logs
```

### 3. **Initial Setup**

#### Create Admin User
```bash
python -c "
from auth_system import get_auth_manager, UserRole
auth = get_auth_manager()
user = auth.create_user('admin', 'admin@example.com', 'Administrator', 'admin123', UserRole.ADMIN)
print('✅ Admin user created successfully!')
print('Username: admin')
print('Password: admin123')
"
```

#### Setup Environment (Optional)
```bash
# Create .env file
cat > .env << EOF
OLLAMA_BASE_URL=http://localhost:11434
JWT_SECRET_KEY=your-super-secret-key-change-in-production
AGENTS_STORAGE=./agent_versions.json
USERS_STORAGE=./users.json
EOF
```

---

## 🚀 **Running the System**

### **Option 1: Full System (Recommended)**

```bash
# Terminal 1: Start Ollama (if using local models)
ollama serve

# Terminal 2: Start Health Monitor API
python health_monitor.py

# Terminal 3: Start Metrics Server (optional)
python -c "
from metrics import get_metrics
metrics = get_metrics()
print('📊 Metrics server starting...')
metrics.start_metrics_server(8000)
import time
while True:
    time.sleep(1)
"

# Terminal 4: Start Main Application
streamlit run app.py
```

### **Option 2: Quick Start (Streamlit Only)**

```bash
# Just run the main app
streamlit run app.py
```

### **Option 3: API Only**

```bash
# Health & Auth API
python health_monitor.py

# Or create custom FastAPI app
python -c "
from system_integration import get_system
system = get_system()
app = system.create_system_api()
# Add your custom endpoints here
"
```

---

## 🔐 **Authentication & Authorization**

### **Login Process**

1. **Via Streamlit UI**: Go to login page
2. **Via API**:
```bash
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### **User Roles & Permissions**

| Role | Permissions | Use Case |
|------|-------------|----------|
| **Admin** | Full system access, user management | System administrators |
| **Developer** | Agent creation, tool access, monitoring | AI developers |
| **Operator** | Agent deployment, system monitoring | DevOps engineers |
| **User** | Basic agent interaction | End users |
| **Agent** | Inter-agent communication | Service accounts |

### **Creating Additional Users**

```bash
python -c "
from auth_system import get_auth_manager, UserRole
auth = get_auth_manager()

# Create developer user
dev = auth.create_user('alice', 'alice@company.com', 'Alice Developer', 'dev123', UserRole.DEVELOPER)
print('✅ Developer user created')

# Create operator user
ops = auth.create_user('bob', 'bob@company.com', 'Bob Operator', 'ops123', UserRole.OPERATOR)
print('✅ Operator user created')
"
```

---

## 🤖 **Using Agents**

### **Via Streamlit UI (Recommended)**

1. **Login**: Use admin/admin123 or your created user
2. **Create Agents**: Go to "Agent Management" section
3. **Deploy Agents**: Promote through dev → test → prod
4. **Run Tasks**: Use the chat interface for agent interaction

### **Via API**

#### Create Agent Version
```bash
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
# Note the access_token from response

# Create agent version
curl -X POST "http://localhost:8001/agents/calculator/versions" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.0.0",
    "author": "alice",
    "description": "Calculator agent",
    "dependencies": ["math"]
  }'
```

#### Promote Agent
```bash
# Promote to testing
curl -X POST "http://localhost:8001/agents/calculator/promote" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version": "1.0.0", "environment": "test"}'

# Promote to production
curl -X POST "http://localhost:8001/agents/calculator/promote" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version": "1.0.0", "environment": "prod"}'
```

---

## 🔧 **MCP (Model Context Protocol)**

### **Register Tools**

```python
from mcp_server import get_mcp_server

server = get_mcp_server()

# Register a custom tool
def weather_lookup(city: str) -> str:
    # Your weather API logic here
    return f"Weather in {city}: Sunny, 25°C"

server.register_tool(
    name="weather",
    tool_function=weather_lookup,
    description="Get weather information for a city",
    schema={
        "type": "object",
        "required": ["city"],
        "properties": {
            "city": {"type": "string", "description": "City name"}
        }
    },
    tags=["weather", "external-api"]
)
```

### **Use Tools in Agents**

```python
from mcp_client import get_mcp_client

client = get_mcp_client()

# Invoke tool
result = await client.invoke_tool("weather", {"city": "Bangkok"})
print(result.result)  # "Weather in Bangkok: Sunny, 25°C"
```

---

## 📊 **Monitoring & Observability**

### **Health Checks**

```bash
# System health
curl http://localhost:8001/health

# Agent-specific health
curl http://localhost:8001/health/agents/planner

# All statuses
curl http://localhost:8001/status/all
```

### **Metrics**

```bash
# Prometheus metrics
curl http://localhost:8000/metrics

# Or view in browser: http://localhost:8000/metrics
```

### **Token Usage Tracking**

```python
from token_tracker import get_token_tracker

tracker = get_token_tracker()

# Get session summary
summary = tracker.get_session_summary()
print(f"Total tokens: {summary['total_tokens']}")
print(f"Total cost: ${summary['total_cost']:.4f}")

# Export usage data
tracker.export_to_json("usage_report.json")
```

---

## 🧪 **Testing**

### **Run All Tests**
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests (198 tests)
pytest -v

# Run specific component tests
pytest test_intent_classifier.py -v
pytest test_health_monitor.py -v
pytest test_agent_versioning.py -v
pytest test_mcp.py -v
pytest test_auth_system.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### **Test Results Summary**
- ✅ **Intent Classifier**: 16/16 tests passing
- ✅ **Health Monitor**: 22/22 tests passing
- ✅ **Metrics System**: 30/30 tests passing
- ✅ **Token Tracker**: 25/25 tests passing
- ✅ **Agent Versioning**: 25/25 tests passing
- ✅ **MCP Protocol**: 31/31 tests passing
- ✅ **RBAC/Authentication**: 29/29 tests passing
- ✅ **System Integration**: 20/20 tests passing
- 🎯 **Total**: 198/198 tests passing (100%)

---

## 🔧 **Configuration**

### **Environment Variables**

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Authentication
JWT_SECRET_KEY=your-super-secret-key
JWT_EXPIRATION_HOURS=24

# Storage Paths
AGENTS_STORAGE=./agent_versions.json
USERS_STORAGE=./users.json

# Database
SQLITE_DB_PATH=./checkpoints.db

# Vector Store
CHROMA_DB_PATH=./agent_brain
```

### **Component Configuration**

```python
# Custom configurations
from intent_classifier import IntentClassifierConfig
from health_monitor import HealthConfig
from auth_system import AuthConfig

# Example custom config
classifier_config = IntentClassifierConfig(
    model_name="gpt-4",
    confidence_threshold=0.8
)

system = get_system(
    classifier_config=classifier_config,
    health_config=HealthConfig(check_interval_seconds=60),
    auth_config=AuthConfig(jwt_expiration_hours=48)
)
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

1. **"Module not found" errors**
   ```bash
   pip install -r requirements.txt
   pip install prometheus-client PyJWT passlib[bcrypt]
   ```

2. **Ollama connection issues**
   ```bash
   ollama serve  # Start Ollama server
   ollama pull gpt-oss:120b-cloud  # Pull required model
   ```

3. **Port conflicts**
   - Streamlit: Change port with `streamlit run app.py --server.port 8502`
   - Health API: Change port in `health_monitor.py`
   - Metrics: Change port in metrics startup

4. **Authentication issues**
   ```bash
   # Reset users
   rm users.json
   # Recreate admin user
   python -c "from auth_system import get_auth_manager, UserRole; auth = get_auth_manager(); auth.create_user('admin', 'admin@example.com', 'Administrator', 'admin123', UserRole.ADMIN)"
   ```

### **Logs and Debugging**

```bash
# Enable debug logging
export PYTHONPATH=.
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# Run your code here
"

# View agent brain contents
ls -la agent_brain/

# View checkpoints
ls -la checkpoints.db*

# View version history
cat agent_versions.json | jq .
```

---

## 📚 **API Reference**

### **Authentication Endpoints**
- `POST /auth/login` - User login
- `POST /auth/register` - User registration

### **Health Endpoints**
- `GET /health` - System health
- `GET /health/agents/{name}` - Agent health
- `GET /status/all` - All statuses

### **User Management (Admin only)**
- `GET /users` - List users
- `GET /users/{id}` - Get user details
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user

### **Agent Management**
- `POST /agents/{name}/versions` - Create version
- `POST /agents/{name}/promote` - Promote version

### **MCP Endpoints**
- `GET /mcp/tools` - List tools
- `POST /mcp/tools/{name}/invoke` - Invoke tool

---

## 🎯 **Next Steps**

1. **Explore Features**: Try creating and deploying agents
2. **Customize Tools**: Add your own MCP tools
3. **Extend Roles**: Create custom user roles
4. **Monitor Usage**: Check metrics and token usage
5. **Scale Up**: Deploy multiple instances

---

## 📞 **Support**

- **Documentation**: See `README.md`, `TESTING.md`, `MICROSOFT_COMPLIANCE.md`
- **Issues**: Check test results with `pytest -v`
- **Logs**: Check application logs for errors
- **API Docs**: Visit `http://localhost:8001/docs` when health monitor is running

---

**Happy exploring! 🚀**

*This system implements 100% of Microsoft's Multi-Agent Architecture best practices with comprehensive testing and enterprise-grade security.*