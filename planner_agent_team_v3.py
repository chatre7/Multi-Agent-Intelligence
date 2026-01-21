import operator
import subprocess
import os
import sqlite3
from typing import Annotated, Sequence, TypedDict, Dict

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
    messages = state["messages"]
    last_message = messages[-1]
    sender = state.get("sender", "User")

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return {"next_agent": "tools"}
    if isinstance(last_message, ToolMessage):
        return {"next_agent": sender}

    content = last_message.content.lower()

    # 🔥 Smart Handoff Updated:
    # ถ้า Critic บอกว่า APPROVE -> ให้ส่งไป Tester
    if sender == "Critic" and "approve" in content:
        print("  🛡️ [Supervisor] : Critic Approved -> Sending to Tester")
        return {"next_agent": "Tester"}

    # ถ้า Critic บอกว่า REJECT -> ส่งกลับไป Coder (Loop correction)
    if sender == "Critic" and "reject" in content:
        print("  🛡️ [Supervisor] : Critic Rejected -> Sending back to Coder")
        return {"next_agent": "Coder"}

    # Universal Guard
    if "tester" in content and "run" in content:
        return {"next_agent": "Tester"}

    if isinstance(last_message, HumanMessage):
        if any(
            w in content
            for w in ["save", "code", "write", "create", "สร้าง", "เขียน", "บันทึก"]
        ):
            return {"next_agent": "Coder"}
        if any(w in content for w in ["test", "run", "รัน", "ตรวจสอบ"]):
            return {"next_agent": "Tester"}

    # AI Router
    system_prompt = (
        "You are the Supervisor. Who should act next?\n"
        "Options: [Planner, Coder, Critic, Tester, FINISH].\n"
        "Rules:\n"
        "- New complex task -> Planner\n"
        "- Coding -> Coder\n"
        "- Reviewing Code Logic -> Critic (Use this before Testing!)\n"
        "- Running Code -> Tester\n"
        "- Task done -> FINISH\n"
        "Reply with JUST THE AGENT NAME."
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
    print("  🗺️ [Planner] : กำลังวางแผน...")
    sys_msg = SystemMessage(
        content="""
    Role: Technical Planner.
    Task: Break down the request.
    Output Format:
    1. [Coder]: Create file...
    2. [Critic]: Review the code...
    3. [Tester]: Run the code...
    """
    )
    response = planner_llm.invoke([sys_msg] + messages)
    return {"messages": [response], "sender": "Planner"}


def coder_node(state: AgentState):
    messages = state["messages"]
    print("  📝 [Coder] : กำลังเขียนโค้ด...")
    # 🔥 สั่งให้ส่งงาน Critic แทน Tester
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
    print("  🤔 [Critic] : กำลังตรวจ Logic...")

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
    print("  🧪 [Tester] : กำลังตรวจสอบ...")
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
# 5. GRAPH BUILD
# ==========================================
db_path = "checkpoints.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
memory = SqliteSaver(conn)

workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("Planner", planner_node)
workflow.add_node("Coder", coder_node)
workflow.add_node("Critic", critic_node)  # ✅ เพิ่ม Node
workflow.add_node("Tester", tester_node)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("supervisor")
workflow.add_conditional_edges(
    "supervisor",
    lambda x: x["next_agent"],
    {
        "Planner": "Planner",
        "Coder": "Coder",
        "Critic": "Critic",
        "Tester": "Tester",
        "tools": "tools",
        "FINISH": END,
    },
)

workflow.add_edge("Planner", "supervisor")
workflow.add_edge("Coder", "supervisor")
workflow.add_edge("Critic", "supervisor")  # ✅ เพิ่ม Edge
workflow.add_edge("Tester", "supervisor")
workflow.add_edge("tools", "supervisor")

app = workflow.compile(checkpointer=memory, interrupt_before=["tools"])
