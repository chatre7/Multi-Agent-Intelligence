#!/bin/bash
# Multi-Agent Intelligence System - Quick Start Script

echo "🚀 Starting Multi-Agent Intelligence System..."
echo "================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt
pip install prometheus-client

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p agent_brain
mkdir -p logs

# Set environment variables (optional)
export OLLAMA_BASE_URL="http://localhost:11434"
export JWT_SECRET_KEY="your-secret-key-change-in-production"
export AGENTS_STORAGE="./agent_versions.json"
export USERS_STORAGE="./users.json"

echo "✅ Setup complete!"
echo ""
echo "🎯 To start using the system:"
echo ""
echo "1. Start Ollama (if using local models):"
echo "   ollama serve"
echo ""
echo "2. Create admin user:"
echo "   python -c \"from auth_system import get_auth_manager, UserRole; auth = get_auth_manager(); auth.create_user('admin', 'admin@example.com', 'Administrator', 'admin123', UserRole.ADMIN); print('Admin user created!')\""
echo ""
echo "3. Run the Streamlit app:"
echo "   streamlit run app.py"
echo ""
echo "4. Run health monitor (optional, in another terminal):"
echo "   python health_monitor.py"
echo ""
echo "5. Run tests to verify everything works:"
echo "   python -m pytest test_intent_classifier.py test_health_monitor.py -v"
echo ""
echo "🌐 Access points:"
echo "   - Streamlit UI: http://localhost:8501"
echo "   - Health API: http://localhost:8001"
echo "   - Metrics: http://localhost:8000/metrics"
echo ""
echo "🔐 Default login: admin / admin123"
echo ""
echo "📚 For detailed usage, see README.md and USAGE_GUIDE.md"