import operator
import subprocess
import os
import sqlite3
from typing import Annotated, Sequence, TypedDict, Dict, Optional

# Memory Dependencies
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    AIMessage,
)
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver

# MCP Integration
from mcp_server import get_mcp_server
from mcp_client import get_mcp_client

# Agent Versioning
from agent_versioning import get_version_manager, TransitionAction

# Hierarchical Chat / Subgraphs Support
from langgraph.graph import StateGraph as SubgraphStateGraph
from typing import Literal

# Dynamic Group Chat Support
from enum import Enum


# ==========================================
# 1. MEMORY SYSTEM
# ==========================================
class MemoryManager:
    def __init__(self):
        try:
            self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        except Exception:
            print("⚠️ Warning: 'nomic-embed-text' not found. Using default.")
            self.embeddings = OllamaEmbeddings(model="gpt-oss:120b-cloud")

        self.vector_store = Chroma(
            collection_name="shared_knowledge",
            embedding_function=self.embeddings,
            persist_directory="./agent_brain",
        )

    def save(self, text: str, source: str = "User"):
        doc = Document(page_content=text, metadata={"source": source})
        self.vector_store.add_documents([doc])
        return "✅ Saved to memory."

    def search(self, query: str, k: int = 2):
        results = self.vector_store.similarity_search(query, k=k)
        if not results:
            return "No relevant memory found."
        return "\n".join([f"- {doc.page_content}" for doc in results])


brain = MemoryManager()


# ==========================================
# ADVANCED AGENTS INTEGRATION
# ==========================================

# Import advanced specialized agents
from advanced_agents import (
    get_agent_registry as get_advanced_agent_registry,
    get_multi_agent_orchestrator,
)

# Get advanced agent registry and orchestrator
advanced_registry = get_advanced_agent_registry()
multi_agent_orchestrator = get_multi_agent_orchestrator()


# ==========================================
# 2. AGENT REGISTRY WITH VERSIONING
# ==========================================
class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, str] = {}
        self.version_manager = get_version_manager()

    def register(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
        author: str = "system",
    ):
        """Register an agent with versioning."""
        self._agents[name] = description

        # Create version if it doesn't exist
        try:
            self.version_manager.create_version(
                agent_name=name, version=version, author=author, description=description
            )
        except ValueError:
            # Version already exists, skip
            pass

    def get_agent_version(self, name: str, environment: str = "prod"):
        """Get current version of an agent for specific environment."""
        return self.version_manager.get_current_version(name, environment)

    def promote_agent(
        self, name: str, version: str, target_env: str, user: str = "system"
    ):
        """Promote agent version to target environment."""
        if target_env == "test":
            action = TransitionAction.PROMOTE
            # First promote to testing
            self.version_manager.transition_version(name, version, action, user)
        elif target_env == "prod":
            # Promote to testing first if not already
            current = self.get_agent_version(name, "test")
            if not current or current.version != version:
                # Promote to testing
                self.version_manager.transition_version(
                    name, version, TransitionAction.PROMOTE, user
                )
            # Then promote to production
            self.version_manager.transition_version(
                name, version, TransitionAction.PROMOTE, user
            )

    def get_prompt_context(self) -> str:
        context = "AVAILABLE WORKERS:\n"
        for name, desc in self._agents.items():
            version = self.get_agent_version(name)
            version_str = f" v{version.version}" if version else ""
            state_str = f" ({version.state.value})" if version else ""
            context += f"- {name}{version_str}{state_str}: {desc}\n"
        return context

    def get_members(self) -> list:
        return list(self._agents.keys())

    def get_agent_versions(self, name: str):
        """List all versions of an agent."""
        return self.version_manager.list_versions(name)


registry = AgentRegistry()
registry.register("Planner", "Expert strategist. Breaks down complex tasks.")
registry.register("Coder", "Writes code and SAVES files.")
registry.register(
    "Critic", "Reviews code logic and quality BEFORE testing."
)  # 🔥 เพิ่มคนนี้
registry.register("Tester", "Runs scripts and validates output.")
registry.register("Reviewer", "General reviewer (Final check).")

# Register advanced specialized agents
registry.register(
    "CodeReviewAgent", "Advanced code review and security analysis specialist."
)
registry.register(
    "ResearchAgent", "Academic research and evidence-based analysis expert."
)
registry.register(
    "DataAnalysisAgent", "Statistical analysis and data visualization specialist."
)
registry.register(
    "DocumentationAgent", "Technical documentation and API writing expert."
)
registry.register(
    "DevOpsAgent", "CI/CD pipeline and infrastructure deployment specialist."
)

# ==========================================
# 3. CONFIG & TOOLS
# ==========================================
MODEL_NAME = "gpt-oss:120b-cloud"
llm = ChatOllama(model=MODEL_NAME, temperature=0, request_timeout=120.0)
supervisor_llm_text = ChatOllama(model=MODEL_NAME, temperature=0, request_timeout=120.0)


@tool
def save_file(filename: str, code: str):
    """Saves valid Python code to a specific file.

    Security: Validates file path to prevent directory traversal and
    restricts writes to allowed directories only.

    Args:
        filename: Relative path to save file (e.g., 'script.py' or 'output/data.py')
        code: Content to write to file

    Returns:
        Success or error message
    """
    from pathlib import Path
    import os

    # Define allowed base directories for file operations
    ALLOWED_DIRECTORIES = [
        Path("./workspace").resolve(),
        Path("./output").resolve(),
        Path("./temp").resolve(),
        Path("./scripts").resolve(),
        Path(".").resolve(),  # Current directory
    ]

    # Create allowed directories if they don't exist
    for allowed_dir in ALLOWED_DIRECTORIES[:3]:  # Skip current dir
        allowed_dir.mkdir(exist_ok=True)

    try:
        # Convert to absolute path and resolve any symlinks
        file_path = Path(filename).resolve()

        # Security check 1: Prevent directory traversal
        if ".." in str(filename):
            return f"❌ Security Error: Directory traversal (..) not allowed in path"

        # Security check 2: Prevent absolute paths
        if Path(filename).is_absolute():
            return f"❌ Security Error: Absolute paths not allowed. Use relative paths."

        # Security check 3: Validate file is within allowed directories
        is_allowed = any(
            str(file_path).startswith(str(allowed_dir))
            for allowed_dir in ALLOWED_DIRECTORIES
        )

        if not is_allowed:
            allowed_paths = ", ".join(str(d.relative_to(Path.cwd())) for d in ALLOWED_DIRECTORIES[:3])
            return f"❌ Security Error: File must be in allowed directories: {allowed_paths}"

        # Security check 4: Validate file extension
        ALLOWED_EXTENSIONS = [".py", ".txt", ".md", ".json", ".yaml", ".yml", ".csv"]
        if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            return f"❌ Security Error: File extension '{file_path.suffix}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        rel_path = file_path.relative_to(Path.cwd())
        return f"✅ File '{rel_path}' saved successfully."

    except ValueError as e:
        return f"❌ Path Error: {e}"
    except PermissionError:
        return f"❌ Permission Error: Cannot write to '{filename}'"
    except OSError as e:
        return f"❌ OS Error: {e}"
    except Exception as e:
        return f"❌ Unexpected Error: {type(e).__name__}: {e}"


@tool
def run_script(filename: str):
    """Executes a Python script."""
    if not os.path.exists(filename):
        return f"⛔ FATAL ERROR: File '{filename}' does NOT exist. Tell Coder to create it."

    try:
        result = subprocess.run(
            ["python", filename], capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            return f"✅ Output:\n{result.stdout}"
        else:
            return f"⚠️ Runtime Error:\n{result.stderr}"
    except Exception as e:
        return f"❌ System Error: {e}"


@tool
def save_memory(knowledge: str):
    """Saves important information, rules, or lessons learned to long-term memory."""
    return brain.save(knowledge, source="Agent")


@tool
def search_memory(query: str):
    """Searches for relevant information in long-term memory."""
    return brain.search(query)


# ==========================================
# MCP INTEGRATION
# ==========================================

# Initialize MCP components
mcp_server = get_mcp_server()
mcp_client = get_mcp_client()

# Register tools with MCP server
mcp_server.register_tool(
    name="save_file",
    tool_function=save_file,
    description="Save Python code to a file",
    schema={
        "type": "object",
        "required": ["filename", "code"],
        "properties": {
            "filename": {"type": "string", "description": "File path to save to"},
            "code": {"type": "string", "description": "Python code content"},
        },
    },
    tags=["file", "coding", "io"],
)

mcp_server.register_tool(
    name="run_script",
    tool_function=run_script,
    description="Execute a Python script",
    schema={
        "type": "object",
        "required": ["filename"],
        "properties": {
            "filename": {
                "type": "string",
                "description": "Python script file to execute",
            }
        },
    },
    tags=["execution", "testing", "script"],
)

mcp_server.register_tool(
    name="save_memory",
    tool_function=save_memory,
    description="Save information to long-term memory",
    schema={
        "type": "object",
        "required": ["knowledge"],
        "properties": {
            "knowledge": {"type": "string", "description": "Information to save"}
        },
    },
    tags=["memory", "knowledge", "storage"],
)

mcp_server.register_tool(
    name="search_memory",
    tool_function=search_memory,
    description="Search for information in long-term memory",
    schema={
        "type": "object",
        "required": ["query"],
        "properties": {"query": {"type": "string", "description": "Search query"}},
    },
    tags=["memory", "knowledge", "search"],
)


# Create MCP wrapper tools for LangChain compatibility
async def mcp_save_file(filename: str, code: str):
    """MCP wrapper for save_file tool."""
    result = await mcp_client.invoke_tool(
        "save_file", {"filename": filename, "code": code}
    )
    return result.result if result.status.name == "SUCCESS" else result.error_message


async def mcp_run_script(filename: str):
    """MCP wrapper for run_script tool."""
    result = await mcp_client.invoke_tool("run_script", {"filename": filename})
    return result.result if result.status.name == "SUCCESS" else result.error_message


async def mcp_save_memory(knowledge: str):
    """MCP wrapper for save_memory tool."""
    result = await mcp_client.invoke_tool("save_memory", {"knowledge": knowledge})
    return result.result if result.status.name == "SUCCESS" else result.error_message


async def mcp_search_memory(query: str):
    """MCP wrapper for search_memory tool."""
    result = await mcp_client.invoke_tool("search_memory", {"query": query})
    return result.result if result.status.name == "SUCCESS" else result.error_message


# Create sync MCP wrappers for ToolNode compatibility
def sync_mcp_save_file(filename: str, code: str):
    """Sync MCP wrapper for save_file tool."""
    import asyncio

    result = asyncio.run(
        mcp_client.invoke_tool("save_file", {"filename": filename, "code": code})
    )
    return result.result if result.status.name == "SUCCESS" else result.error_message


def sync_mcp_run_script(filename: str):
    """Sync MCP wrapper for run_script tool."""
    import asyncio

    result = asyncio.run(mcp_client.invoke_tool("run_script", {"filename": filename}))
    return result.result if result.status.name == "SUCCESS" else result.error_message


def sync_mcp_save_memory(knowledge: str):
    """Sync MCP wrapper for save_memory tool."""
    import asyncio

    result = asyncio.run(
        mcp_client.invoke_tool("save_memory", {"knowledge": knowledge})
    )
    return result.result if result.status.name == "SUCCESS" else result.error_message


def sync_mcp_search_memory(query: str):
    """Sync MCP wrapper for search_memory tool."""
    import asyncio

    result = asyncio.run(mcp_client.invoke_tool("search_memory", {"query": query}))
    return result.result if result.status.name == "SUCCESS" else result.error_message


# Convert to LangChain tools
from langchain_core.tools import tool as langchain_tool

mcp_save_file_tool = langchain_tool(sync_mcp_save_file)
mcp_run_script_tool = langchain_tool(sync_mcp_run_script)
mcp_save_memory_tool = langchain_tool(sync_mcp_save_memory)
mcp_search_memory_tool = langchain_tool(sync_mcp_search_memory)


# ==========================================
# 4. NODES & LOGIC
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str
    next_agent: str


coder_llm = llm.bind_tools(
    [mcp_save_file_tool, mcp_save_memory_tool, mcp_search_memory_tool]
)
tester_llm = llm.bind_tools([mcp_run_script_tool])
critic_llm = llm  # Critic ไม่ต้องใช้ Tool แค่บ่น
planner_llm = llm


def supervisor_node(state: AgentState):
    """
    Advanced Dynamic Supervisor: Uses intelligent routing with specialized agents
    Supports hierarchical delegation, dynamic conversation flow, and specialized agent selection
    """
    messages = state["messages"]
    last_message = messages[-1]
    sender = state.get("sender", "User")

    # Handle tool calls and responses
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return {"next_agent": "tools"}
    if isinstance(last_message, ToolMessage):
        return {"next_agent": sender}

    # For User messages, always route to Planner for intelligent routing
    if sender == "User":
        print("  🎯 [Supervisor] : User message detected, routing to Planner")
        return {"next_agent": "Planner"}

    # For other senders, use dynamic router
    router = get_next_speaker_router()

    # Get conversation state for routing decisions
    conversation_state = {
        "hierarchical_mode": True,  # Enable hierarchical routing
        "iteration_count": len(messages),
        "participants": list(router.participant_roles.keys()),
    }

    # Determine next speaker based on current context
    message_content = str(last_message.content)
    next_speaker = router.get_next_speaker(sender, message_content, conversation_state)

    # Check for termination conditions
    if router.should_terminate(message_content, conversation_state["iteration_count"]):
        print("  🎯 [Supervisor] : Conversation complete!")
        return {"next_agent": "FINISH"}

    print(f"  🎭 [Supervisor] : Dynamic routing -> {next_speaker}")

    # Handle special routing logic for specialized agents and DevTeam
    if sender == "DevTeam":
        dev_team_response = message_content.lower()
        if any(
            word in dev_team_response
            for word in ["completed", "เสร็จ", "success", "done"]
        ):
            print("  🏢 [Supervisor] : DevTeam task completed successfully!")
            return {"next_agent": "FINISH"}
        elif any(word in dev_team_response for word in ["failed", "error", "ปัญหา"]):
            print("  🏢 [Supervisor] : DevTeam needs assistance -> routing to Planner")
            return {"next_agent": "Planner"}  # Get help from Planner

    # Handle specialized agent responses - they should route back appropriately
    specialized_agents = [
        "CodeReviewAgent",
        "ResearchAgent",
        "DataAnalysisAgent",
        "DocumentationAgent",
        "DevOpsAgent",
    ]

    if sender in specialized_agents:
        # Check response structure to distinguish actual errors from technical content
        # Specialized agents use structured format: "🔬 **AgentName Analysis Complete**" for success
        # and "❌ **AgentName Error**" for actual failures

        if f"🔬 **{sender} Analysis Complete**" in message_content:
            # Successful completion with analysis
            print(f"  🔬 [Supervisor] : {sender} analysis complete, task finished")
            return {"next_agent": "FINISH"}  # Complete the conversation

        elif f"❌ **{sender} Error**" in message_content:
            # Actual error from agent - route to Planner for help
            print(f"  🔬 [Supervisor] : {sender} encountered actual error, routing to Planner")
            return {"next_agent": "Planner"}

        else:
            # Fallback: treat as completion
            print(f"  🔬 [Supervisor] : {sender} response received, completing task")
            return {"next_agent": "FINISH"}

    # Handle multi-agent orchestration responses
    if sender.startswith("MultiAgent_"):
        orchestration_response = message_content.lower()
        if any(word in orchestration_response for word in ["error", "failed"]):
            print(
                "  🎭 [Supervisor] : Multi-agent orchestration failed, routing to Planner"
            )
            return {"next_agent": "Planner"}
        else:
            print(
                "  🎭 [Supervisor] : Multi-agent orchestration complete, ready for next steps"
            )

    return {"next_agent": next_speaker}


def planner_node(state: AgentState):
    messages = state["messages"]
    print("  🗺️ [Planner] : กำลังวางแผนด้วย SpecKit...")

    # Extract only the LAST user request (HumanMessage) from messages
    user_request = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) and hasattr(msg, "content") and msg.content:
            user_request = msg.content
            break

    # Check if this is a simple greeting or casual message
    import re
    # Thai patterns use simple substring matching (no word boundaries)
    thai_greetings = ["สวัสดี", "ทดสอบ"]
    # English patterns use word boundary matching
    english_patterns = [r"\bhello\b", r"\bhi\b", r"\bhey\b", r"\btest\b", r"\?"]

    is_simple_message = (
        any(thai in user_request for thai in thai_greetings) or
        any(re.search(pattern, user_request.lower()) for pattern in english_patterns)
    )

    # For simple greetings, respond briefly and finish
    if is_simple_message and len(user_request.strip()) < 50:
        simple_response = SystemMessage(
            content=f"""สวัสดีครับ! ผม Planner Agent พร้อมช่วยคุณในงานต่างๆ

**งานพัฒนาซอฟต์แวร์:**
- วางแผนและพัฒนา feature ใหม่ (DevTeam)
- รีวิวโค้ด และหาจุดปรับปรุง (CodeReviewAgent)

**งานวิเคราะห์และวิจัย:**
- ค้นคว้าข้อมูลและเทคโนโลยี (ResearchAgent)
- วิเคราะห์ข้อมูลและสถิติ (DataAnalysisAgent)

**งานเอกสารและ DevOps:**
- สร้างเอกสารและ API docs (DocumentationAgent)
- จัดการ deployment และ infrastructure (DevOpsAgent)

มีอะไรให้ช่วยไหมครับ?"""
        )
        return {"messages": [simple_response], "sender": "Planner", "next_agent": "FINISH"}

    # Use SpecKit commands for structured planning
    try:
        # Step 1: Generate detailed specifications
        print("    📋 กำลังสร้าง specifications...")
        spec_command = f"/speckit.specify {user_request.strip()}"
        # In a real implementation, this would invoke the SpecKit agent command
        # For now, we'll simulate the spec generation

        # Step 2: Create technical implementation plan
        print("    📐 กำลังสร้าง implementation plan...")
        plan_command = f"/speckit.plan Create technical implementation plan for: {user_request.strip()}"
        # This would also invoke SpecKit

        # Step 3: Generate actionable tasks
        print("    ✅ กำลังสร้าง task breakdown...")
        tasks_command = "/speckit.tasks"
        # This would generate the detailed task list

        # Create dynamic response with web search capabilities
        dynamic_response = f"""
🎯 **Strategic Analysis Complete - Web Search Enabled**

**Current Assessment:**
- **Request**: {user_request.strip()}
- **Complexity**: High - requires structured development approach
- **Next Phase**: Implementation with DevTeam collaboration

**Available Web Search Tools:**
- web_search(): Real-time information access (free, 24h cache, $5/day budget)
- web_search_with_domain(): Domain-specific research (docs, APIs, tutorials)

**Recommended Approach:**
1. **Research Phase**: Use web_search() to gather current information and best practices
2. **DevTeam Implementation**: Coder → Critic → Tester iterative cycle
3. **Quality Assurance**: Automated testing and code review
4. **Completion Criteria**: All tests pass, code approved

**DevTeam Brief:**
"Research current technologies using web_search(), then implement following specifications:
1. Use web_search() to research current technologies and best practices
2. Review detailed requirements in `.specify/specs/` directory
3. Execute implementation according to technical plan
4. Complete all acceptance criteria with 100% test coverage
5. Report back only when fully complete and tested

The DevTeam has access to web search tools for real-time information."

**Status**: Ready for development phase with web search capabilities enabled.
**Next Speaker**: DevTeam should begin implementation.
"""

        response = SystemMessage(content=dynamic_response)

    except Exception as e:
        print(f"    ⚠️ SpecKit integration error: {e}")
        # Fallback to original planning approach
        sys_msg = SystemMessage(
            content="""
        Role: Technical Planner.
        Task: Break down the request using SpecKit principles.
        Output Format:
        1. [Coder]: Review specs in .specify/specs/ and implement according to plan.md
        2. [Critic]: Review code against specifications and constitution
        3. [Tester]: Test implementation against acceptance criteria
        """
        )
        response = planner_llm.invoke([sys_msg] + messages)

    # Analyze request and determine appropriate next agent
    request_lower = user_request.lower()

    # Determine next agent based on request type (check data analysis first to avoid conflicts)
    if any(word in request_lower for word in ["analyze data", "วิเคราะห์ข้อมูล", "analytics", "statistics", "สถิติ"]) or \
       ("analyze" in request_lower and "data" in request_lower):
        next_agent = "DataAnalysisAgent"
        print("  🎯 [Planner] : Routing to DataAnalysisAgent for data analysis")
    elif any(word in request_lower for word in ["review", "รีวิว", "code review", "ตรวจสอบโค้ด", "quality"]):
        next_agent = "CodeReviewAgent"
        print("  🎯 [Planner] : Routing to CodeReviewAgent for code review")
    elif any(word in request_lower for word in ["research", "ค้นคว้า", "หาข้อมูล", "search", "investigate"]):
        next_agent = "ResearchAgent"
        print("  🎯 [Planner] : Routing to ResearchAgent for research")
    elif any(word in request_lower for word in ["document", "เอกสาร", "docs", "api doc", "readme"]):
        next_agent = "DocumentationAgent"
        print("  🎯 [Planner] : Routing to DocumentationAgent for documentation")
    elif any(word in request_lower for word in ["deploy", "devops", "infrastructure", "pipeline", "ci/cd"]):
        next_agent = "DevOpsAgent"
        print("  🎯 [Planner] : Routing to DevOpsAgent for DevOps tasks")
    elif any(word in request_lower for word in ["implement", "develop", "code", "build", "create", "พัฒนา", "สร้าง"]):
        next_agent = "DevTeam"
        print("  🎯 [Planner] : Routing to DevTeam for implementation")
    else:
        # For ambiguous requests, route back to supervisor for intelligent routing
        next_agent = "supervisor"
        print("  🎯 [Planner] : Routing to supervisor for intelligent agent selection")

    return {"messages": [response], "sender": "Planner", "next_agent": next_agent}


def coder_node(state: AgentState):
    messages = state["messages"]
    print("  📝 [Coder] : กำลัง implement ตาม SpecKit specs...")

    # Check for SpecKit-generated specifications
    spec_content = ""
    try:
        from pathlib import Path

        # Look for the most recent spec directory
        spec_base = Path(".specify/specs")
        if spec_base.exists():
            spec_dirs = [d for d in spec_base.iterdir() if d.is_dir()]
            if spec_dirs:
                # Get the most recent spec directory
                latest_spec = max(spec_dirs, key=lambda x: x.stat().st_mtime)
                spec_dir = latest_spec

                # Read specification files
                spec_file = spec_dir / "spec.md"
                plan_file = spec_dir / "plan.md"
                tasks_file = spec_dir / "tasks.md"

                if spec_file.exists():
                    with open(spec_file, "r", encoding="utf-8") as f:
                        spec_content += f"\n--- SPECIFICATIONS ---\n{f.read()}"

                if plan_file.exists():
                    with open(plan_file, "r", encoding="utf-8") as f:
                        spec_content += f"\n--- IMPLEMENTATION PLAN ---\n{f.read()}"

                if tasks_file.exists():
                    with open(tasks_file, "r", encoding="utf-8") as f:
                        spec_content += f"\n--- TASK BREAKDOWN ---\n{f.read()}"

        if spec_content:
            print("    📖 พบ SpecKit specifications แล้ว กำลัง implement ตาม specs...")
        else:
            print("    ⚠️ ไม่พบ SpecKit specs ใช้โหมดปกติ...")

    except Exception as e:
        print(f"    ⚠️ Error reading specs: {e}")
        spec_content = ""

    # Enhanced system message with SpecKit integration
    spec_driven_prompt = f"""
Role: Python Developer with Spec-Driven Development.
Task: Implement code according to SpecKit-generated specifications.

{spec_content}

CRITICAL REQUIREMENTS:
1. Follow the specifications exactly as defined in the spec documents
2. Implement according to the technical plan and architecture
3. Complete tasks in the order specified in tasks.md
4. Ensure compliance with constitution guidelines (.specify/memory/constitution.md)
5. Write production-ready, well-tested code
6. Include comprehensive error handling and logging

IMPLEMENTATION STEPS:
1. Review all specification documents carefully
2. Plan your implementation approach
3. Write the code following best practices
4. SAVE the code to appropriate files
5. After saving, ask the 'Critic' to review against specifications

Say: "I have implemented according to SpecKit specifications. Critic, please review against the specs."
"""

    # Use enhanced prompt if specs are available
    if spec_content:
        sys_msg = SystemMessage(content=spec_driven_prompt)
    else:
        # Fallback to original approach
        sys_msg = SystemMessage(
            content="""
        Role: Python Dev.
        Task: Write code and SAVE it.
        CRITICAL RULE: After saving, ask the 'Critic' to review your code.
        Say: "I have saved the code. Critic, please review."
        """
        )

    response = coder_llm.invoke([sys_msg] + messages)
    return {"messages": [response], "sender": "Coder"}


# --- 🔥 NEW: Critic Node ---
def critic_node(state: AgentState):
    messages = state["messages"]
    print("  🤔 [Critic] : กำลังตรวจตาม SpecKit specs...")

    # Load SpecKit specifications for review criteria
    spec_criteria = ""
    try:
        from pathlib import Path

        # Look for the most recent spec directory
        spec_base = Path(".specify/specs")
        if spec_base.exists():
            spec_dirs = [d for d in spec_base.iterdir() if d.is_dir()]
            if spec_dirs:
                latest_spec = max(spec_dirs, key=lambda x: x.stat().st_mtime)

                # Read constitution for review guidelines
                constitution_file = Path(".specify/memory/constitution.md")
                if constitution_file.exists():
                    with open(constitution_file, "r", encoding="utf-8") as f:
                        spec_criteria += (
                            f"\n--- CONSTITUTION GUIDELINES ---\n{f.read()}"
                        )

                # Read spec file for requirements
                spec_file = latest_spec / "spec.md"
                if spec_file.exists():
                    with open(spec_file, "r", encoding="utf-8") as f:
                        spec_criteria += f"\n--- SPECIFICATIONS ---\n{f.read()}"

                # Read tasks for acceptance criteria
                tasks_file = latest_spec / "tasks.md"
                if tasks_file.exists():
                    with open(tasks_file, "r", encoding="utf-8") as f:
                        spec_criteria += f"\n--- ACCEPTANCE CRITERIA ---\n{f.read()}"

        if spec_criteria:
            print("    📋 กำลังตรวจสอบตาม SpecKit specifications...")
        else:
            print("    ⚠️ ไม่พบ SpecKit specs ใช้โหมดปกติ...")

    except Exception as e:
        print(f"    ⚠️ Error loading specs: {e}")
        spec_criteria = ""

    # Enhanced review prompt with SpecKit integration
    spec_driven_review = f"""
Role: Senior Code Reviewer (SpecKit-Enhanced).
Task: Review code implementation against SpecKit-generated specifications.

{spec_criteria}

REVIEW CRITERIA:
1. **Specification Compliance**: Does code match the defined specs exactly?
2. **Constitution Adherence**: Follows all constitutional guidelines?
3. **Task Completion**: All tasks from breakdown completed?
4. **Security Requirements**: Meets all security specifications?
5. **Code Quality**: Clean, maintainable, well-documented code?
6. **Acceptance Criteria**: Passes all defined acceptance criteria?

Technical Checks:
- Syntax errors and imports
- Logic correctness and edge cases
- Security vulnerabilities
- Performance considerations
- Error handling completeness
- Test coverage adequacy

Output Rules:
- If code fully complies with specifications: "APPROVE. Tester, please run comprehensive tests."
- If minor issues found: "APPROVE with notes: [list minor issues]. Tester, please run tests."
- If major issues found: "REJECT. Coder, please fix: [explain issues with spec references]."
- Always reference specific specification sections when rejecting code.
"""

    # Use enhanced review if specs are available
    if spec_criteria:
        sys_msg = SystemMessage(content=spec_driven_review)
    else:
        # Fallback to original review approach
        sys_msg = SystemMessage(
            content="""
        Role: Senior Code Reviewer (Critic).
        Task: Analyze the code written by the Coder.
        Check for:
        1. Syntax errors
        2. Missing imports
        3. Infinite loops
        4. Security risks

        Output Rules:
        - If code looks good, reply exactly: "APPROVE. Tester, please run."
        - If code has issues, reply exactly: "REJECT. Coder, please fix [explain error]."
        """
        )

    response = critic_llm.invoke([sys_msg] + messages)
    print(f"      🗣️  [Msg]: {response.content}")
    return {"messages": [response], "sender": "Critic"}


def tester_node(state: AgentState):
    messages = state["messages"]
    print("  🧪 [Tester] : กำลัง test ตาม SpecKit specs...")

    # Load testing criteria from specifications
    test_criteria = ""
    try:
        from pathlib import Path

        # Look for the most recent spec directory
        spec_base = Path(".specify/specs")
        if spec_base.exists():
            spec_dirs = [d for d in spec_base.iterdir() if d.is_dir()]
            if spec_dirs:
                latest_spec = max(spec_dirs, key=lambda x: x.stat().st_mtime)

                # Read tasks for acceptance criteria
                tasks_file = latest_spec / "tasks.md"
                if tasks_file.exists():
                    with open(tasks_file, "r", encoding="utf-8") as f:
                        test_criteria += f"\n--- ACCEPTANCE CRITERIA ---\n{f.read()}"

                # Read plan for testing requirements
                plan_file = latest_spec / "plan.md"
                if plan_file.exists():
                    with open(plan_file, "r", encoding="utf-8") as f:
                        test_criteria += f"\n--- TESTING REQUIREMENTS ---\n{f.read()}"

        if test_criteria:
            print("    🧪 กำลัง test ตาม SpecKit acceptance criteria...")
        else:
            print("    ⚠️ ไม่พบ SpecKit specs ใช้โหมดปกติ...")

    except Exception as e:
        print(f"    ⚠️ Error loading test criteria: {e}")
        test_criteria = ""

    # Enhanced testing prompt with SpecKit integration
    spec_driven_testing = f"""
Role: QA Engineer (SpecKit-Enhanced).
Task: Test implementation against SpecKit specifications and acceptance criteria.

{test_criteria}

TESTING REQUIREMENTS:
1. **Acceptance Criteria Validation**: Verify all criteria from tasks.md are met
2. **Specification Compliance**: Ensure implementation matches spec.md exactly
3. **Security Testing**: Validate all security requirements are implemented
4. **Integration Testing**: Test with existing system components
5. **Performance Testing**: Verify performance requirements are met

Testing Commands Available:
- run_script: Execute Python scripts and commands
- File operations for test setup/cleanup

Test Execution Steps:
1. Review acceptance criteria from specifications
2. Set up test environment if needed
3. Run comprehensive tests covering all requirements
4. Validate security implementations
5. Check integration with existing systems
6. Report results with specific pass/fail criteria

Output Format:
- For each acceptance criterion: PASS/FAIL with evidence
- Overall assessment: IMPLEMENTATION READY or NEEDS FIXES
- Specific issues found with spec references
"""

    # Use enhanced testing if criteria are available
    if test_criteria:
        sys_msg = SystemMessage(content=spec_driven_testing)
    else:
        # Fallback to original testing approach
        sys_msg = SystemMessage(content="Role: QA. Run scripts using 'run_script'.")

    response = tester_llm.invoke([sys_msg] + messages)
    return {"messages": [response], "sender": "Tester"}


tool_node = ToolNode(
    [
        sync_mcp_save_file,
        sync_mcp_run_script,
        sync_mcp_save_memory,
        sync_mcp_search_memory,
    ]
)

# ==========================================
# 4. HIERARCHICAL CHAT / DEVTEAM SUBGRAPH
# ==========================================


# DevTeam Subgraph State
class DevTeamState(TypedDict):
    """State for the DevTeam subgraph with internal communication"""

    messages: Annotated[Sequence, operator.add]
    sender: str
    task_summary: str  # Summary of the task from Supervisor
    iteration_count: int  # Track internal iterations
    dev_status: Literal[
        "planning", "coding", "reviewing", "testing", "completed", "failed"
    ]
    final_result: Optional[str]  # Final deliverable to send back to Supervisor


def dev_team_coordinator(state: DevTeamState) -> DevTeamState:
    """
    Internal coordinator for the DevTeam subgraph.
    Manages the flow between Coder, Critic, and Tester.
    """
    messages = state["messages"]
    iteration_count = state.get("iteration_count", 0)

    print(f"  👥 [DevTeam] Iteration {iteration_count + 1} - กำลังประสานงานภายในทีม...")

    # Analyze the latest message to determine next action
    if not messages:
        return {
            "messages": [
                SystemMessage(
                    content="DevTeam initialized and ready for task assignment."
                )
            ],
            "sender": "DevTeam_Coordinator",
            "dev_status": "planning",
            "iteration_count": iteration_count + 1,
        }

    latest_message = messages[-1]

    # Decision logic based on message content and current status
    current_status = state.get("dev_status", "planning")

    # If this is the first task assignment from Supervisor
    if current_status == "planning" and "supervisor" in str(latest_message).lower():
        return {
            "messages": [
                SystemMessage(content="Task received. Starting development process.")
            ],
            "sender": "DevTeam_Coordinator",
            "dev_status": "coding",
        }

    # Analyze message content for routing decisions
    message_text = (
        str(latest_message.content).lower()
        if hasattr(latest_message, "content")
        else str(latest_message)
    )

    # Success indicators
    if any(
        word in message_text
        for word in ["approved", "complete", "passed", "success", "เสร็จ"]
    ):
        return {
            "messages": [
                SystemMessage(
                    content="🎉 Development completed successfully! Ready to report back to Supervisor."
                )
            ],
            "sender": "DevTeam_Coordinator",
            "dev_status": "completed",
            "final_result": "Task completed successfully. All tests passed and code is approved.",
        }

    # Error indicators - route back to coding
    if any(word in message_text for word in ["error", "fail", "bug", "fix", "แก้ไข"]):
        return {
            "messages": [
                SystemMessage(
                    content="Issues detected. Routing back to Coder for fixes."
                )
            ],
            "sender": "DevTeam_Coordinator",
            "dev_status": "coding",
        }

    # Default progression through the development cycle
    if current_status == "coding":
        next_status = "reviewing"
        next_message = "Code submitted. Sending to Critic for review."
    elif current_status == "reviewing":
        next_status = "testing"
        next_message = "Review completed. Sending to Tester for validation."
    elif current_status == "testing":
        next_status = "coding"  # Loop back if more work needed
        next_message = "Testing completed. May need additional development iterations."
    else:
        next_status = "coding"
        next_message = "Continuing development process."

    return {
        "messages": [SystemMessage(content=next_message)],
        "sender": "DevTeam_Coordinator",
        "dev_status": next_status,
        "iteration_count": iteration_count + 1,
    }


def dev_team_coder_node(state: DevTeamState) -> DevTeamState:
    """Enhanced Coder node for DevTeam subgraph"""
    messages = state["messages"]
    task_summary = state.get("task_summary", "")

    print("    📝 [DevTeam:Coder] กำลังพัฒนาโค้ด...")

    # Enhanced prompt with web search capabilities
    dynamic_prompt = f"""
Role: Senior Developer in collaborative development team with web search access.

**Current Context:**
- Task: {task_summary or "Implement requested feature"}
- Team: Working with Critic and Tester for quality assurance
- Process: Research → Code → Review → Test → Iterate

**Available Tools:**
- web_search(): Search for current information, API docs, library versions
- web_search_with_domain(): Search specific domains (docs.python.org, fastapi.tiangolo.com)

**Implementation Guidelines:**
1. **Research First**: Use web_search() to check current best practices, API docs, and library versions
2. Write clean, well-documented code following project standards
3. Include proper error handling and edge cases
4. Consider scalability and maintainability
5. Save code to appropriate files with clear naming
6. Provide implementation summary for team review

**Research Workflow:**
- Before coding: Search for current documentation and examples
- During implementation: Verify technical assumptions with web search
- For new technologies: Research compatibility and best practices

**Collaboration Flow:**
- After research: Implement based on current information
- After coding: Send to Critic for quality review
- Address any issues found during review
- Code will be tested by Tester before final approval

**Communication Style:**
Be clear about what was implemented and any assumptions made.
If you encounter issues, explain them clearly for team resolution.
Reference any web search findings that influenced the implementation.

Implementation ready - proceeding with research and development.
"""

    sys_msg = SystemMessage(content=dynamic_prompt)

    response = coder_llm.invoke([sys_msg] + messages)
    return {"messages": [response], "sender": "DevTeam_Coder", "dev_status": "coding"}


def dev_team_critic_node(state: DevTeamState) -> DevTeamState:
    """Enhanced Critic node for DevTeam subgraph"""
    messages = state["messages"]

    print("    🤔 [DevTeam:Critic] กำลังตรวจสอบโค้ด...")

    dynamic_review_prompt = """
Role: Senior Code Reviewer in collaborative development team.

**Review Context:**
- Working with Coder and Tester for comprehensive quality assurance
- Focus on constructive feedback and clear communication
- Balance between quality standards and development velocity

**Review Criteria:**
1. **Code Correctness**: Logic, algorithms, edge cases
2. **Security**: Vulnerabilities, input validation, data protection
3. **Performance**: Efficiency, scalability considerations
4. **Maintainability**: Code structure, documentation, readability
5. **Testability**: How easily the code can be tested

**Communication Guidelines:**
- Be specific about issues found with code examples
- Suggest concrete improvements, not just problems
- Consider the development context and constraints
- Balance perfection with pragmatism

**Decision Framework:**
- APPROVED: Code meets quality standards, ready for testing
- APPROVED with notes: Minor issues that don't block testing
- REJECTED: Major issues requiring fixes before testing

**Next Steps:**
After review, code goes to Tester for validation.
Be prepared to discuss findings with the team.
"""

    sys_msg = SystemMessage(content=dev_team_review_prompt)
    response = critic_llm.invoke([sys_msg] + messages)

    return {
        "messages": [response],
        "sender": "DevTeam_Critic",
        "dev_status": "reviewing",
    }


def dev_team_tester_node(state: DevTeamState) -> DevTeamState:
    """Enhanced Tester node for DevTeam subgraph"""
    messages = state["messages"]

    print("    🧪 [DevTeam:Tester] กำลังทดสอบโค้ด...")

    dynamic_test_prompt = """
Role: QA Engineer in collaborative development team.

**Testing Context:**
- Final quality gate before implementation approval
- Working with Coder and Critic to ensure robust solutions
- Focus on user impact and system reliability

**Testing Scope:**
1. **Functional Testing**: Core features work as specified
2. **Integration Testing**: Works with existing systems
3. **Error Handling**: Graceful failure and recovery
4. **Performance**: Reasonable response times and resource usage
5. **Edge Cases**: Boundary conditions and unusual scenarios

**Testing Approach:**
- Automated tests where possible
- Manual verification for complex scenarios
- Regression testing to ensure no existing functionality broken
- User experience validation

**Communication Style:**
- Clear pass/fail criteria with evidence
- Specific about what was tested and how
- Actionable feedback for any issues found
- Context about impact and severity

**Decision Framework:**
- TESTS PASSED: Implementation meets requirements
- TESTS PASSED with notes: Acceptable with minor issues
- TESTS FAILED: Critical issues requiring fixes

**Quality Assurance:**
Final checkpoint before delivery to stakeholders.
Ensure the solution is production-ready.
"""

    sys_msg = SystemMessage(content=dev_team_test_prompt)
    response = tester_llm.invoke([sys_msg] + messages)

    return {"messages": [response], "sender": "DevTeam_Tester", "dev_status": "testing"}


# Create DevTeam Subgraph
def create_dev_team_subgraph():
    """Create the DevTeam subgraph with autonomous agent collaboration"""

    dev_team_workflow = SubgraphStateGraph(DevTeamState)

    # Add nodes
    dev_team_workflow.add_node("coordinator", dev_team_coordinator)
    dev_team_workflow.add_node("coder", dev_team_coder_node)
    dev_team_workflow.add_node("critic", dev_team_critic_node)
    dev_team_workflow.add_node("tester", dev_team_tester_node)

    # Set entry point
    dev_team_workflow.set_entry_point("coordinator")

    # Define the development workflow
    def route_after_coordinator(state: DevTeamState):
        """Route based on coordinator's decision"""
        dev_status = state.get("dev_status", "planning")

        if dev_status == "completed":
            return "end"  # Exit subgraph
        elif dev_status == "failed":
            return "end"  # Exit subgraph
        elif dev_status == "coding":
            return "coder"
        elif dev_status == "reviewing":
            return "critic"
        elif dev_status == "testing":
            return "tester"
        else:
            return "coder"  # Default to coding

    def route_after_coder(state: DevTeamState):
        """Always go to critic after coding"""
        return "critic"

    def route_after_critic(state: DevTeamState):
        """Route based on critic's decision"""
        messages = state.get("messages", [])
        if not messages:
            return "tester"  # Default

        latest_message = str(messages[-1].content).lower()
        if "rejected" in latest_message or "fix" in latest_message:
            return "coder"  # Send back to coder
        else:
            return "tester"  # Proceed to testing

    def route_after_tester(state: DevTeamState):
        """Route based on tester's decision"""
        messages = state.get("messages", [])
        if not messages:
            return "coordinator"  # Default

        latest_message = str(messages[-1].content).lower()
        if "failed" in latest_message or "fix" in latest_message:
            return "coder"  # Send back to coder
        else:
            return "coordinator"  # Report back to coordinator

    # Add conditional edges
    dev_team_workflow.add_conditional_edges(
        "coordinator",
        route_after_coordinator,
        {"coder": "coder", "critic": "critic", "tester": "tester", "end": END},
    )

    dev_team_workflow.add_edge("coder", "critic")
    dev_team_workflow.add_conditional_edges("critic", route_after_critic)
    dev_team_workflow.add_conditional_edges("tester", route_after_tester)

    return dev_team_workflow.compile()


# Global DevTeam subgraph instance
_dev_team_subgraph = None


def get_dev_team_subgraph():
    """Get or create the DevTeam subgraph instance"""
    global _dev_team_subgraph
    if _dev_team_subgraph is None:
        _dev_team_subgraph = create_dev_team_subgraph()
    return _dev_team_subgraph


# ==========================================
# 4.5 DYNAMIC GROUP CHAT / NEXT SPEAKER ROUTING
# ==========================================


class ConversationContext(Enum):
    """Types of conversation contexts for routing decisions"""

    PLANNING = "planning"
    CODING = "coding"
    REVIEWING = "reviewing"
    TESTING = "testing"
    DEBUGGING = "debugging"
    COMPLETING = "completing"
    CLARIFYING = "clarifying"
    REPORTING = "reporting"


class NextSpeakerRouter:
    """Intelligent router that determines who should speak next based on conversation context"""

    def __init__(self):
        self.conversation_history = []
        self.participant_roles = {
            "supervisor": "CEO/Orchestrator - makes high-level decisions and delegates",
            "Planner": "Strategic Planner - analyzes requirements and creates plans",
            "DevTeam": "Development Team - implements, tests, and reviews code",
            "Coder": "Individual Developer - writes and modifies code",
            "Critic": "Code Reviewer - analyzes code quality and logic",
            "Tester": "QA Engineer - runs tests and validates functionality",
            "tools": "Tool Executor - runs scripts and external commands",
        }

    def analyze_message_context(self, message_content: str) -> ConversationContext:
        """Analyze message content to determine conversation context"""
        content_lower = message_content.lower()

        # Completion indicators
        if any(
            word in content_lower
            for word in [
                "completed",
                "finished",
                "done",
                "success",
                "approved",
                "passed",
                "เสร็จ",
            ]
        ):
            return ConversationContext.COMPLETING

        # Testing context
        if any(
            word in content_lower
            for word in ["test", "run", "validate", "check", "verify", "ทดสอบ", "รัน"]
        ):
            return ConversationContext.TESTING

        # Code review context
        if any(
            word in content_lower
            for word in [
                "review",
                "check",
                "analyze",
                "logic",
                "quality",
                "ตรวจสอบ",
                "วิเคราะห์",
            ]
        ):
            return ConversationContext.REVIEWING

        # Coding context
        if any(
            word in content_lower
            for word in [
                "code",
                "implement",
                "write",
                "create",
                "function",
                "class",
                "เขียน",
                "โค้ด",
                "สร้าง",
                "ฟังก์ชัน",
            ]
        ):
            return ConversationContext.CODING

        # Error/Debugging context
        if any(
            word in content_lower
            for word in [
                "error",
                "bug",
                "fix",
                "debug",
                "issue",
                "problem",
                "แก้ไข",
                "debug",
                "ปัญหา",
                "error",
            ]
        ):
            return ConversationContext.DEBUGGING

        # Planning context
        if any(
            word in content_lower
            for word in [
                "plan",
                "design",
                "strategy",
                "approach",
                "how",
                "what",
                "วางแผน",
                "ออกแบบ",
                "วิธี",
                "อะไร",
            ]
        ):
            return ConversationContext.PLANNING

        # Clarification needed
        if any(
            word in content_lower
            for word in [
                "clarify",
                "explain",
                "understand",
                "clear",
                "ไม่เข้าใจ",
                "อธิบาย",
            ]
        ):
            return ConversationContext.CLARIFYING

        return ConversationContext.REPORTING

    def get_next_speaker(
        self, current_speaker: str, message_content: str, conversation_state: dict
    ) -> str:
        """
        Determine who should speak next based on current context

        Args:
            current_speaker: Who just spoke
            message_content: What was said
            conversation_state: Current conversation state

        Returns:
            Next speaker name
        """
        context = self.analyze_message_context(message_content)

        print(f"🎯 [Router] Context: {context.value}, Current: {current_speaker}")

        # Context-based routing logic
        if context == ConversationContext.COMPLETING:
            # Task completed - route back to supervisor
            if current_speaker in ["Coder", "Critic", "Tester"]:
                return "supervisor"
            return "supervisor"

        elif context == ConversationContext.TESTING:
            # Testing needed - route to Tester
            if current_speaker != "Tester":
                return "Tester"
            # If Tester already speaking, might need to go back to Coder
            return "Coder"

        elif context == ConversationContext.REVIEWING:
            # Code review needed - route to Critic
            if current_speaker != "Critic":
                return "Critic"
            return "Coder"  # Review done, back to coding

        elif context == ConversationContext.CODING:
            # Coding work - route to Coder (or DevTeam in hierarchical mode)
            if conversation_state.get("hierarchical_mode", False):
                return "DevTeam"
            else:
                if current_speaker != "Coder":
                    return "Coder"
                return "Critic"  # Code written, send to review

        elif context == ConversationContext.DEBUGGING:
            # Errors found - route back to Coder for fixes
            return "Coder"

        elif context == ConversationContext.PLANNING:
            # Planning needed - route to Planner
            if current_speaker != "Planner":
                return "Planner"
            # Planning done, start implementation
            if conversation_state.get("hierarchical_mode", False):
                return "DevTeam"
            else:
                return "Coder"

        elif context == ConversationContext.CLARIFYING:
            # Need clarification - ask supervisor
            return "supervisor"

        # Default routing based on current speaker
        routing_map = {
            "supervisor": "Planner",  # Supervisor delegates to Planner
            "Planner": "DevTeam"
            if conversation_state.get("hierarchical_mode", False)
            else "Coder",
            "Coder": "Critic",  # Code → Review
            "Critic": "Tester",  # Review → Test
            "Tester": "supervisor",  # Test results → Supervisor
            "DevTeam": "supervisor",  # DevTeam reports → Supervisor
            "tools": current_speaker,  # Tool results go back to who called them
        }

        return routing_map.get(current_speaker, "supervisor")

    def should_terminate(self, message_content: str, iteration_count: int) -> bool:
        """Determine if conversation should terminate"""
        content_lower = message_content.lower()

        # Success termination
        success_indicators = [
            "task completed",
            "implementation finished",
            "all tests passed",
            "approved",
            "success",
            "done",
            "เสร็จสิ้น",
            "สำเร็จ",
        ]

        # Failure termination (too many iterations)
        if iteration_count > 15:
            print("🔄 [Router] Max iterations reached, terminating")
            return True

        # Success termination
        if any(indicator in content_lower for indicator in success_indicators):
            print("✅ [Router] Success detected, terminating")
            return True

        return False


# Global router instance
_next_speaker_router = None


def get_next_speaker_router() -> NextSpeakerRouter:
    """Get or create the NextSpeakerRouter instance"""
    global _next_speaker_router
    if _next_speaker_router is None:
        _next_speaker_router = NextSpeakerRouter()
    return _next_speaker_router


# ==========================================
# ADVANCED AGENT SELECTION LOGIC
# ==========================================


def _select_specialized_agent(
    message_content: str, current_sender: str
) -> Optional[str]:
    """
    Analyze message content to determine if a specialized agent should handle the task.

    Returns the name of the most appropriate specialized agent, or None if no specialized
    agent is needed.
    """
    content_lower = message_content.lower()

    # Skip specialized routing if already in specialized agent workflow
    specialized_agents = [
        "CodeReviewAgent",
        "ResearchAgent",
        "DataAnalysisAgent",
        "DocumentationAgent",
        "DevOpsAgent",
    ]
    if current_sender in specialized_agents:
        return None

    # Code Review Agent - Security and code quality analysis
    code_review_keywords = [
        "security",
        "vulnerability",
        "audit",
        "review code",
        "code quality",
        "static analysis",
        "security scan",
        "penetration test",
        "bug bounty",
        "secure coding",
        "owasp",
        "cve",
        "exploit",
        "injection",
        "xss",
        "csrf",
        "authentication",
        "authorization",
        "encryption",
    ]
    if any(keyword in content_lower for keyword in code_review_keywords):
        return "CodeReviewAgent"

    # Research Agent - Academic research and evidence-based analysis
    research_keywords = [
        "research",
        "study",
        "evidence",
        "academic",
        "literature",
        "meta-analysis",
        "systematic review",
        "peer review",
        "methodology",
        "hypothesis",
        "statistical significance",
        "confidence interval",
        "p-value",
        "randomized controlled trial",
        "case study",
        "evidence-based",
    ]
    if any(keyword in content_lower for keyword in research_keywords):
        return "ResearchAgent"

    # Data Analysis Agent - Statistics and visualization
    data_keywords = [
        "statistics",
        "data analysis",
        "visualization",
        "chart",
        "graph",
        "correlation",
        "regression",
        "anova",
        "hypothesis test",
        "confidence",
        "trend analysis",
        "forecasting",
        "time series",
        "clustering",
        "classification",
        "machine learning",
        "predictive model",
    ]
    if any(keyword in content_lower for keyword in data_keywords):
        return "DataAnalysisAgent"

    # Documentation Agent - Technical writing and API docs
    docs_keywords = [
        "documentation",
        "api docs",
        "readme",
        "user guide",
        "technical writing",
        "swagger",
        "openapi",
        "javadoc",
        "docstring",
        "api reference",
        "tutorial",
        "getting started",
        "how-to",
        "documentation maintenance",
    ]
    if any(keyword in content_lower for keyword in docs_keywords):
        return "DocumentationAgent"

    # DevOps Agent - Infrastructure and deployment
    devops_keywords = [
        "deployment",
        "ci/cd",
        "pipeline",
        "infrastructure",
        "docker",
        "kubernetes",
        "terraform",
        "ansible",
        "jenkins",
        "github actions",
        "monitoring",
        "logging",
        "scaling",
        "load balancer",
        "microservices",
        "serverless",
        "cloud architecture",
        "devops",
        "infrastructure as code",
    ]
    if any(keyword in content_lower for keyword in devops_keywords):
        return "DevOpsAgent"

    # Multi-agent orchestration triggers
    orchestration_keywords = [
        "orchestrate:",
        "multi-agent",
        "parallel processing",
        "consensus",
        "sequential workflow",
        "agent team",
        "collaborative analysis",
    ]
    if any(keyword in content_lower for keyword in orchestration_keywords):
        # Extract orchestration strategy if specified
        if "orchestrate:sequential" in content_lower:
            return "MultiAgentSequential"
        elif "orchestrate:parallel" in content_lower:
            return "MultiAgentParallel"
        elif "orchestrate:consensus" in content_lower:
            return "MultiAgentConsensus"
        else:
            return "MultiAgentAuto"

    return None


# Enhanced AgentState for dynamic conversations
class DynamicAgentState(TypedDict):
    """Enhanced state for dynamic group chat"""

    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str
    next_agent: str
    conversation_context: ConversationContext
    iteration_count: int
    hierarchical_mode: bool
    termination_reason: Optional[str]


# ==========================================
# SPECIALIZED AGENT NODES
# ==========================================


def specialized_agent_node(state: AgentState, agent_name: str):
    """Generic node for specialized agents (sync wrapper for async agent.process_task)"""
    import asyncio

    messages = state["messages"]
    last_message = messages[-1]

    print(f"  🔬 [{agent_name}] : Processing specialized task...")

    # Get the task from the last message
    task_content = str(last_message.content)

    # Get the specialized agent
    agent = advanced_registry.get_agent(agent_name)
    if not agent:
        error_msg = f"Specialized agent '{agent_name}' not found."
        print(f"  ❌ [{agent_name}] : {error_msg}")
        return {"messages": [SystemMessage(content=error_msg)], "sender": agent_name, "next_agent": "supervisor"}

    try:
        # Process the task using the specialized agent (run async method in sync context)
        result = asyncio.run(agent.process_task(task_content))

        # Format response for the conversation
        if "error" in result:
            response_content = f"❌ **{agent_name} Error**: {result['error']}\n\n**Suggestions**: {', '.join(result.get('fallback_suggestions', []))}"
        else:
            response_content = (
                f"🔬 **{agent_name} Analysis Complete**\n\n**Response**: {result['response']}\n\n**Confidence**: {result['confidence']:.2f}\n\n**Key Recommendations**:\n"
                + "\n".join(f"- {rec}" for rec in result.get("recommendations", [])[:3])
            )

        response = SystemMessage(content=response_content)
        return {"messages": [response], "sender": agent_name, "next_agent": "supervisor"}

    except Exception as e:
        error_msg = f"❌ **{agent_name} Failed**: {str(e)}"
        print(f"  ❌ [{agent_name}] : {error_msg}")
        return {"messages": [SystemMessage(content=error_msg)], "sender": agent_name, "next_agent": "supervisor"}


async def multi_agent_orchestration_node(state: AgentState, strategy: str):
    """Node for multi-agent orchestration"""
    messages = state["messages"]
    last_message = messages[-1]

    print(f"  🎭 [MultiAgent_{strategy}] : Orchestrating with {strategy} strategy...")

    # Get the task from the last message
    task_content = str(last_message.content)

    try:
        # Orchestrate the task
        result = await multi_agent_orchestrator.orchestrate_task(task_content, strategy)

        # Format the orchestration result
        if "error" in result:
            response_content = (
                f"❌ **Multi-Agent Orchestration Failed**: {result['error']}"
            )
        else:
            response_content = (
                f"🎭 **Multi-Agent Orchestration Complete ({strategy})**\n\n"
            )

            if strategy == "parallel":
                synthesis = result.get("synthesis", {})
                response_content += f"**Strategy**: Parallel processing across {len(result.get('agents_used', []))} agents\n"
                response_content += (
                    "**Key Insights**:\n"
                    + "\n".join(
                        f"- {insight}"
                        for insight in synthesis.get("key_insights", [])[:3]
                    )
                    + "\n\n"
                )
                response_content += (
                    "**Consolidated Recommendations**:\n"
                    + "\n".join(
                        f"- {rec}"
                        for rec in synthesis.get("consolidated_recommendations", [])[:3]
                    )
                    + "\n\n"
                )
                response_content += f"**Average Confidence**: {synthesis.get('average_confidence', 0):.2f}"

            elif strategy == "sequential":
                response_content += f"**Strategy**: Sequential processing through {len(result.get('agent_sequence', []))} agents\n"
                final_result = result.get("final_result", {})
                if "response" in final_result:
                    response_content += (
                        f"**Final Result**: {final_result['response'][:500]}..."
                    )

            elif strategy == "consensus":
                consensus = result.get("consensus", {})
                response_content += f"**Strategy**: Consensus from {consensus.get('agents_agreed', 0)} agents\n"
                response_content += f"**Top Recommendation**: {consensus.get('top_recommendation', 'N/A')}\n"
                response_content += (
                    f"**Consensus Level**: {consensus.get('consensus_level', 0):.2f}\n"
                )
                response_content += (
                    f"**Confidence Score**: {consensus.get('confidence_score', 0):.2f}"
                )

        response = SystemMessage(content=response_content)
        return {"messages": [response], "sender": f"MultiAgent_{strategy}"}

    except Exception as e:
        error_msg = f"❌ **Multi-Agent Orchestration Failed**: {str(e)}"
        print(f"  ❌ [MultiAgent_{strategy}] : {error_msg}")
        return {
            "messages": [SystemMessage(content=error_msg)],
            "sender": f"MultiAgent_{strategy}",
        }


# ==========================================
# 5. GRAPH BUILD
# ==========================================
db_path = "checkpoints.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
memory = SqliteSaver(conn)

# Create hierarchical workflow with DevTeam subgraph and specialized agents
# Dynamic Group Chat Graph with intelligent routing
workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("Planner", planner_node)
workflow.add_node("DevTeam", get_dev_team_subgraph())  # Hierarchical DevTeam
workflow.add_node("tools", tool_node)

# Add specialized agent nodes
workflow.add_node(
    "CodeReviewAgent", lambda state: specialized_agent_node(state, "CodeReviewAgent")
)
workflow.add_node(
    "ResearchAgent", lambda state: specialized_agent_node(state, "ResearchAgent")
)
workflow.add_node(
    "DataAnalysisAgent",
    lambda state: specialized_agent_node(state, "DataAnalysisAgent"),
)
workflow.add_node(
    "DocumentationAgent",
    lambda state: specialized_agent_node(state, "DocumentationAgent"),
)
workflow.add_node(
    "DevOpsAgent", lambda state: specialized_agent_node(state, "DevOpsAgent")
)

# Add multi-agent orchestration nodes
workflow.add_node(
    "MultiAgent_sequential",
    lambda state: multi_agent_orchestration_node(state, "sequential"),
)
workflow.add_node(
    "MultiAgent_parallel",
    lambda state: multi_agent_orchestration_node(state, "parallel"),
)
workflow.add_node(
    "MultiAgent_consensus",
    lambda state: multi_agent_orchestration_node(state, "consensus"),
)
workflow.add_node(
    "MultiAgent_auto", lambda state: multi_agent_orchestration_node(state, "auto")
)

workflow.set_entry_point("supervisor")


# Advanced dynamic routing function
def advanced_dynamic_route(state: AgentState) -> str:
    """Advanced dynamic routing with specialized agents"""
    next_agent = state.get("next_agent", "supervisor")

    # If termination requested, end the conversation
    if next_agent == "FINISH":
        return END

    # Define all valid agents including specialized ones
    valid_agents = [
        "supervisor",
        "Planner",
        "DevTeam",
        "tools",
        "CodeReviewAgent",
        "ResearchAgent",
        "DataAnalysisAgent",
        "DocumentationAgent",
        "DevOpsAgent",
        "MultiAgent_sequential",
        "MultiAgent_parallel",
        "MultiAgent_consensus",
        "MultiAgent_auto",
    ]

    if next_agent not in valid_agents:
        print(f"⚠️ [Router] Invalid agent '{next_agent}', defaulting to supervisor")
        return "supervisor"

    return next_agent


# Use conditional edges for advanced dynamic routing
workflow.add_conditional_edges(
    "supervisor",
    advanced_dynamic_route,
    {
        "supervisor": "supervisor",  # Allow supervisor to loop back to itself
        "Planner": "Planner",
        "DevTeam": "DevTeam",
        "tools": "tools",
        "CodeReviewAgent": "CodeReviewAgent",
        "ResearchAgent": "ResearchAgent",
        "DataAnalysisAgent": "DataAnalysisAgent",
        "DocumentationAgent": "DocumentationAgent",
        "DevOpsAgent": "DevOpsAgent",
        "MultiAgent_sequential": "MultiAgent_sequential",
        "MultiAgent_parallel": "MultiAgent_parallel",
        "MultiAgent_consensus": "MultiAgent_consensus",
        "MultiAgent_auto": "MultiAgent_auto",
        END: END,  # Termination
    },
)


# Dynamic return edges - agents can route back to supervisor or to other agents
def dynamic_return_route(state: AgentState) -> str:
    """Dynamic routing for returns to supervisor or other agents"""
    next_agent = state.get("next_agent", "supervisor")
    return next_agent if next_agent != "FINISH" else END


# Add return edges for all nodes
workflow.add_conditional_edges("Planner", dynamic_return_route)
workflow.add_conditional_edges("DevTeam", dynamic_return_route)
workflow.add_conditional_edges("tools", dynamic_return_route)
workflow.add_conditional_edges("CodeReviewAgent", dynamic_return_route)
workflow.add_conditional_edges("ResearchAgent", dynamic_return_route)
workflow.add_conditional_edges("DataAnalysisAgent", dynamic_return_route)
workflow.add_conditional_edges("DocumentationAgent", dynamic_return_route)
workflow.add_conditional_edges("DevOpsAgent", dynamic_return_route)
workflow.add_conditional_edges("MultiAgent_sequential", dynamic_return_route)
workflow.add_conditional_edges("MultiAgent_parallel", dynamic_return_route)
workflow.add_conditional_edges("MultiAgent_consensus", dynamic_return_route)
workflow.add_conditional_edges("MultiAgent_auto", dynamic_return_route)

app = workflow.compile(checkpointer=memory, interrupt_before=["tools"])
