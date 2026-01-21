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


# ==========================================
# 1. MEMORY SYSTEM
# ==========================================
class MemoryManager:
    def __init__(self):
        try:
            self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        except Exception as e:
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

    def list_agent_versions(self, name: str):
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

# ==========================================
# 3. CONFIG & TOOLS
# ==========================================
MODEL_NAME = "gpt-oss:120b-cloud"
llm = ChatOllama(model=MODEL_NAME, temperature=0, request_timeout=120.0)
supervisor_llm_text = ChatOllama(model=MODEL_NAME, temperature=0, request_timeout=120.0)


@tool
def save_file(filename: str, code: str):
    """Saves valid Python code to a specific file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)
        return f"✅ File '{filename}' saved successfully."
    except Exception as e:
        return f"❌ Error saving file: {e}"


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
    Hierarchical Supervisor: Makes high-level decisions and delegates to teams.
    Instead of managing individual agents, now delegates to Planner or DevTeam.
    """
    messages = state["messages"]
    last_message = messages[-1]
    sender = state.get("sender", "User")

    # Handle tool calls and responses
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return {"next_agent": "tools"}
    if isinstance(last_message, ToolMessage):
        return {"next_agent": sender}

    content = last_message.content.lower()

    # 🚀 Hierarchical Decision Making:
    # Instead of routing to individual agents, decide between:
    # - Planner: For planning and analysis tasks
    # - DevTeam: For development, coding, testing tasks

    # Handle DevTeam responses (simplified reporting)
    if sender == "DevTeam":
        dev_team_response = str(last_message.content).lower()
        if any(
            word in dev_team_response
            for word in ["completed", "เสร็จ", "success", "done"]
        ):
            print("  🏢 [Supervisor] : DevTeam reported completion -> Task finished!")
            return {"next_agent": "FINISH"}
        elif any(word in dev_team_response for word in ["failed", "error", "ปัญหา"]):
            print(
                "  🏢 [Supervisor] : DevTeam reported issues -> Sending back for fixes"
            )
            return {"next_agent": "DevTeam"}  # Re-delegate to DevTeam
        else:
            # DevTeam still working, keep them going
            return {"next_agent": "DevTeam"}

    # Initial user request analysis (Hierarchical approach)
    if isinstance(last_message, HumanMessage):
        # Complex planning tasks -> Planner
        if any(
            w in content
            for w in [
                "plan",
                "design",
                "architecture",
                "strategy",
                "analyze",
                "วางแผน",
                "ออกแบบ",
                "วิเคราะห์",
                "ระบบ",
                "โครงสร้าง",
            ]
        ):
            print("  🏢 [Supervisor] : Complex task detected -> Delegating to Planner")
            return {"next_agent": "Planner"}

        # Development/implementation tasks -> DevTeam
        if any(
            w in content
            for w in [
                "code",
                "implement",
                "create",
                "build",
                "develop",
                "write",
                "เขียน",
                "สร้าง",
                "พัฒนา",
                "โค้ด",
                "ฟีเจอร์",
                "feature",
            ]
        ):
            print(
                "  🏢 [Supervisor] : Development task detected -> Delegating to DevTeam"
            )
            return {"next_agent": "DevTeam"}

        # Testing/debugging tasks -> DevTeam
        if any(
            w in content
            for w in [
                "test",
                "debug",
                "fix",
                "run",
                "check",
                "validate",
                "ทดสอบ",
                "แก้ไข",
                "รัน",
                "ตรวจสอบ",
                "validate",
            ]
        ):
            print("  🏢 [Supervisor] : Testing task detected -> Delegating to DevTeam")
            return {"next_agent": "DevTeam"}

    # AI-powered hierarchical routing for complex decisions
    system_prompt = (
        "You are the CEO Supervisor in a hierarchical organization.\n"
        "Your role is to delegate high-level tasks to appropriate teams, not micromanage.\n\n"
        "Decision Framework:\n"
        "- STRATEGIC PLANNING (market analysis, architecture design) → Planner\n"
        "- DEVELOPMENT WORK (coding, testing, debugging) → DevTeam\n"
        "- COMPLEX ANALYSIS (requirements gathering, tech evaluation) → Planner\n"
        "- IMPLEMENTATION (feature building, bug fixing) → DevTeam\n\n"
        "Current Context: DevTeam handles coding/testing autonomously.\n"
        "You receive summarized reports, not technical details.\n\n"
        "Respond with JUST ONE WORD: Planner, DevTeam, or FINISH"
    )

    next_node = "FINISH"
    try:
        print("  🧠 [Supervisor] : กำลังคิด...")
        response = supervisor_llm_text.invoke(
            [SystemMessage(content=system_prompt)] + messages
        )
        content_resp = response.content.strip().lower()

        if "plan" in content_resp:
            next_node = "Planner"
        elif "code" in content_resp:
            next_node = "Coder"
        elif "critic" in content_resp:
            next_node = "Critic"
        elif "test" in content_resp:
            next_node = "Tester"
        elif "finish" in content_resp:
            next_node = "FINISH"
        print(f"     ✅ ตัดสินใจ -> {next_node}")
    except Exception as e:
        next_node = "FINISH"

    if next_node not in registry.get_members() and next_node != "FINISH":
        next_node = "FINISH"
    return {"next_agent": next_node}


def planner_node(state: AgentState):
    messages = state["messages"]
    print("  🗺️ [Planner] : กำลังวางแผนด้วย SpecKit...")

    # Extract the user request from messages
    user_request = ""
    for msg in messages:
        if hasattr(msg, "content") and msg.content:
            user_request += msg.content + "\n"

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

        # Create hierarchical response - delegate to DevTeam
        hierarchical_response = f"""
🏗️ **Strategic Planning Complete - Delegating to DevTeam**

**Planning Summary:**
- **Objective**: {user_request.strip()}
- **Approach**: SpecKit-driven development with quality assurance
- **Architecture**: Modular, scalable implementation
- **Quality Gates**: Automated testing, code review, security validation

**DevTeam Brief:**
"Implement the planned feature following these specifications:
1. Review detailed requirements in `.specify/specs/` directory
2. Execute implementation according to technical plan
3. Complete all acceptance criteria with 100% test coverage
4. Report back only when fully complete and tested

The DevTeam has full autonomy to iterate internally until completion."

**Supervisor**: DevTeam will handle all development work autonomously.
You will receive summarized status reports, not technical details.

**Ready for DevTeam execution! 🚀**
"""

        response = SystemMessage(content=spec_driven_response)

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

    return {"messages": [response], "sender": "Planner"}


def coder_node(state: AgentState):
    messages = state["messages"]
    print("  📝 [Coder] : กำลัง implement ตาม SpecKit specs...")

    # Check for SpecKit-generated specifications
    spec_content = ""
    try:
        import os
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
        import os
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
        import os
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

    # Enhanced prompt with task context
    dev_team_prompt = f"""
Role: Senior Developer in DevTeam.
Task: Implement the required feature as part of the development team.

Task Summary: {task_summary}

Guidelines:
1. Focus on clean, maintainable code
2. Follow existing project patterns and conventions
3. Consider scalability and error handling
4. Save code to appropriate files
5. Prepare for review and testing

After implementation, the code will be reviewed by Critic and tested by Tester.
Provide a clear summary of what was implemented.
"""

    # Use enhanced prompt if task context is available
    if task_summary:
        sys_msg = SystemMessage(content=dev_team_prompt)
    else:
        # Fallback to original approach
        sys_msg = SystemMessage(
            content="""
    Role: Python Dev in DevTeam.
    Task: Write code and SAVE it.
    After saving, prepare summary for team review.
    """
        )

    response = coder_llm.invoke([sys_msg] + messages)
    return {"messages": [response], "sender": "DevTeam_Coder", "dev_status": "coding"}


def dev_team_critic_node(state: DevTeamState) -> DevTeamState:
    """Enhanced Critic node for DevTeam subgraph"""
    messages = state["messages"]

    print("    🤔 [DevTeam:Critic] กำลังตรวจสอบโค้ด...")

    dev_team_review_prompt = """
Role: Senior Code Reviewer in DevTeam.
Task: Review code implementation for quality, correctness, and adherence to standards.

Focus Areas:
1. Code correctness and logic
2. Security vulnerabilities
3. Performance considerations
4. Code style and maintainability
5. Testability

Output Rules:
- If code meets standards: "APPROVED. Ready for testing."
- If minor issues: "APPROVED with notes: [list issues]. Proceed to testing."
- If major issues: "REJECTED. [Coder]: Please fix: [explain issues]"
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

    dev_team_test_prompt = """
Role: QA Engineer in DevTeam.
Task: Test the implemented code for functionality, edge cases, and integration.

Testing Focus:
1. Functional correctness
2. Error handling
3. Integration with existing systems
4. Performance validation
5. Edge cases and boundary conditions

Output Rules:
- If all tests pass: "TESTS PASSED. Implementation ready."
- If minor issues: "TESTS PASSED with notes: [list issues]. Implementation acceptable."
- If major issues: "TESTS FAILED. [Coder]: Please fix: [explain issues]"
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
# 5. GRAPH BUILD
# ==========================================
db_path = "checkpoints.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
memory = SqliteSaver(conn)

# Create hierarchical workflow with DevTeam subgraph
workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("Planner", planner_node)
workflow.add_node(
    "DevTeam", get_dev_team_subgraph()
)  # 🚀 Hierarchical: DevTeam subgraph
workflow.add_node("tools", tool_node)

workflow.set_entry_point("supervisor")
workflow.add_conditional_edges(
    "supervisor",
    lambda x: x["next_agent"],
    {
        "Planner": "Planner",
        "DevTeam": "DevTeam",  # 🚀 Route to DevTeam subgraph instead of individual agents
        "tools": "tools",
        "FINISH": END,
    },
)

workflow.add_edge("Planner", "supervisor")
workflow.add_edge(
    "DevTeam", "supervisor"
)  # 🚀 DevTeam subgraph reports back to supervisor
workflow.add_edge("tools", "supervisor")

app = workflow.compile(checkpointer=memory, interrupt_before=["tools"])
