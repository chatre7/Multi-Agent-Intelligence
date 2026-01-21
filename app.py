import streamlit as st
import json
import time
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

# Import ตัวแปร app (Graph) จากไฟล์ Backend ของเรา
from planner_agent_team_v3 import app as agent_app

# ==========================================
# 1. SETUP PAGE & SESSION
# ==========================================
st.set_page_config(page_title="AI Agent Team", page_icon="🤖", layout="wide")

# Custom CSS for better UI
st.markdown("""
<style>
    .agent-status {
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        font-weight: bold;
    }
    .status-active {
        background-color: #d4edda;
        border: 2px solid #28a745;
    }
    .status-next {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
    }
    .status-complete {
        background-color: #d1ecf1;
        border: 2px solid #17a2b8;
    }
    .metric-box {
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 10px 0;
    }
    .error-box {
        padding: 15px;
        background-color: #f8d7da;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 10px 0;
    }
    .success-box {
        padding: 15px;
        background-color: #d4edda;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 AI Developer Team (Multi-Agent System)")
st.caption("🚀 Powered by Planner + Specialized Agents + Dynamic Routing")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = "web_session_v1"
if "current_agent" not in st.session_state:
    st.session_state["current_agent"] = None
if "next_agent" not in st.session_state:
    st.session_state["next_agent"] = None
if "step_count" not in st.session_state:
    st.session_state["step_count"] = 0
if "start_time" not in st.session_state:
    st.session_state["start_time"] = None
if "agent_history" not in st.session_state:
    st.session_state["agent_history"] = []

# ==========================================
# 2. SIDEBAR - STATUS & CONTROLS
# ==========================================
with st.sidebar:
    st.header("⚙️ Control Panel")

    # Clear History Button
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state["messages"] = []
        st.session_state["current_agent"] = None
        st.session_state["next_agent"] = None
        st.session_state["step_count"] = 0
        st.session_state["start_time"] = None
        st.session_state["agent_history"] = []
        st.rerun()

    st.divider()

    # System Info
    st.subheader("📊 System Status")
    st.info(f"**Thread ID:** {st.session_state['thread_id']}")

    # Current Agent Status
    if st.session_state["current_agent"]:
        st.markdown(f"""
        <div class="agent-status status-active">
            🔄 Current: {st.session_state["current_agent"]}
        </div>
        """, unsafe_allow_html=True)

    # Next Agent Status
    if st.session_state["next_agent"] and st.session_state["next_agent"] != "FINISH":
        st.markdown(f"""
        <div class="agent-status status-next">
            ⏭️ Next: {st.session_state["next_agent"]}
        </div>
        """, unsafe_allow_html=True)
    elif st.session_state["next_agent"] == "FINISH":
        st.markdown("""
        <div class="agent-status status-complete">
            ✅ Status: Complete
        </div>
        """, unsafe_allow_html=True)

    # Metrics
    if st.session_state["step_count"] > 0:
        st.divider()
        st.subheader("📈 Performance Metrics")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Steps", st.session_state["step_count"])
        with col2:
            if st.session_state["start_time"]:
                elapsed = time.time() - st.session_state["start_time"]
                st.metric("Time", f"{elapsed:.1f}s")

    # Agent History
    if st.session_state["agent_history"]:
        st.divider()
        st.subheader("📜 Agent Flow")
        for i, agent in enumerate(st.session_state["agent_history"], 1):
            st.text(f"{i}. {agent}")


# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def get_avatar(sender_name):
    """เลือก Icon ตามบทบาทของ Agent"""
    # Specialized Agents
    if "CodeReview" in sender_name:
        return "🔬"
    if "Research" in sender_name:
        return "🔍"
    if "DataAnalysis" in sender_name:
        return "📊"
    if "Documentation" in sender_name:
        return "📝"
    if "DevOps" in sender_name:
        return "🚀"

    # Core Agents
    if "Planner" in sender_name:
        return "🗺️"
    if "Coder" in sender_name:
        return "💻"
    if "Tester" in sender_name:
        return "🧪"
    if "Critic" in sender_name:
        return "🤔"
    if "Reviewer" in sender_name:
        return "🧐"
    if "Supervisor" in sender_name:
        return "🧠"

    # Default
    return "🤖"


def get_agent_color(sender_name):
    """เลือกสีตามประเภท Agent"""
    if any(x in sender_name for x in ["CodeReview", "Research", "DataAnalysis", "Documentation", "DevOps"]):
        return "#007bff"  # Blue for specialized agents
    if "Planner" in sender_name:
        return "#28a745"  # Green for planner
    if any(x in sender_name for x in ["Coder", "Tester", "Critic"]):
        return "#6f42c1"  # Purple for dev team
    if "Supervisor" in sender_name:
        return "#fd7e14"  # Orange for supervisor
    return "#6c757d"  # Gray for others


def format_agent_message(sender, content):
    """Format agent message with nice styling"""
    color = get_agent_color(sender)
    avatar = get_avatar(sender)

    # Check for errors
    if "❌" in content or "error" in content.lower():
        return f"""
        <div class="error-box">
            <h4>{avatar} {sender} - Error</h4>
            <p>{content}</p>
        </div>
        """

    # Check for success
    if "✅" in content or "complete" in content.lower():
        return f"""
        <div class="success-box">
            <h4>{avatar} {sender}</h4>
            <p>{content}</p>
        </div>
        """

    # Normal message
    return f"""
    <div style="border-left: 4px solid {color}; padding: 10px; margin: 10px 0; background-color: #f8f9fa; border-radius: 5px;">
        <h4 style="color: {color}; margin: 0;">{avatar} {sender}</h4>
        <div style="margin-top: 10px;">{content}</div>
    </div>
    """


def stream_graph_updates(user_input=None):
    """ฟังก์ชันหลักสำหรับรัน Graph และแสดงผลข้อความ"""
    config = {"configurable": {"thread_id": st.session_state["thread_id"]}}

    # Start timing
    if user_input and not st.session_state["start_time"]:
        st.session_state["start_time"] = time.time()
        st.session_state["step_count"] = 0
        st.session_state["agent_history"] = []

    if user_input:
        # กรณี User พิมพ์สั่งงานใหม่
        inputs = {"messages": [HumanMessage(content=user_input)], "sender": "User"}
        iterator = agent_app.stream(inputs, config, stream_mode="values")
    else:
        # กรณี Resume (กดปุ่ม Approve) ส่ง None เพื่อให้ทำต่อ
        iterator = agent_app.stream(None, config, stream_mode="values")

    # Progress placeholder
    progress_placeholder = st.empty()

    try:
        # วนลูปรับข้อความจาก AI
        for event in iterator:
            # Update step count
            st.session_state["step_count"] += 1

            # Get sender and next_agent
            sender = event.get("sender", "Agent")
            next_agent = event.get("next_agent", "N/A")

            # Update status
            st.session_state["current_agent"] = sender
            st.session_state["next_agent"] = next_agent

            # Track agent history (avoid duplicates)
            if not st.session_state["agent_history"] or st.session_state["agent_history"][-1] != sender:
                st.session_state["agent_history"].append(sender)

            # Show progress
            with progress_placeholder.container():
                st.info(f"⚙️ Step {st.session_state['step_count']}: {sender} → {next_agent}")

            message = event.get("messages")
            if message:
                last_msg = message[-1]

                # Display AIMessage and SystemMessage with content
                if (isinstance(last_msg, (AIMessage, SystemMessage)) and last_msg.content):
                    # แสดงผลหน้าจอ
                    with st.chat_message(sender, avatar=get_avatar(sender)):
                        st.markdown(f"**{sender}:**")
                        st.write(last_msg.content)

                    # บันทึกลง Session State
                    if (
                        not st.session_state["messages"]
                        or st.session_state["messages"][-1]["content"] != last_msg.content
                    ):
                        st.session_state["messages"].append(
                            {"role": sender, "content": last_msg.content}
                        )

            # Clear progress after last step
            time.sleep(0.1)  # Small delay for better UX

        # Clear progress indicator when done
        progress_placeholder.empty()

    except Exception as e:
        progress_placeholder.empty()
        st.error(f"❌ **Error occurred:** {str(e)}")
        st.exception(e)


# ==========================================
# 4. DISPLAY CHAT HISTORY
# ==========================================
for msg in st.session_state["messages"]:
    role = msg["role"]
    content = msg["content"]

    if role == "user":
        st.chat_message("user").write(content)
    else:
        with st.chat_message(role, avatar=get_avatar(role)):
            st.markdown(f"**{role}:**")
            st.markdown(content)

# ==========================================
# 5. CHAT INPUT
# ==========================================
if prompt := st.chat_input("💬 สั่งงานทีม AI ของคุณที่นี่... (เช่น: Review this code, Research AI trends, Analyze data)"):
    # Reset timing
    st.session_state["start_time"] = time.time()
    st.session_state["step_count"] = 0
    st.session_state["agent_history"] = []

    # แสดงข้อความ User
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # ส่งเข้า Graph
    with st.spinner("🤖 ทีมงานกำลังระดมสมอง..."):
        stream_graph_updates(user_input=prompt)

    # Rerun to update sidebar
    st.rerun()

# ==========================================
# 6. HUMAN-IN-THE-LOOP (APPROVAL BUTTONS)
# ==========================================
try:
    config = {"configurable": {"thread_id": st.session_state["thread_id"]}}
    snapshot = agent_app.get_state(config)

    # เช็คว่า Next Step คือ 'tools' หรือไม่
    if snapshot.next and "tools" in snapshot.next:
        last_msg = snapshot.values["messages"][-1]

        # ดึงรายละเอียด Tool ที่ AI จะใช้
        if last_msg.tool_calls:
            tool_call = last_msg.tool_calls[0]
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            # สร้าง Container แจ้งเตือนสวยๆ
            with st.container(border=True):
                col_icon, col_text = st.columns([1, 10])
                with col_icon:
                    st.warning("✋")
                with col_text:
                    st.warning(f"**🔧 AI ขออนุญาตใช้เครื่องมือ:** `{tool_name}`")

                st.code(f"Arguments:\n{json.dumps(tool_args, indent=2)}", language="json")

                col1, col2 = st.columns([1, 1])

                # ปุ่มอนุมัติ (Approve)
                with col1:
                    if st.button(
                        "✅ อนุญาต (Approve)", type="primary", use_container_width=True
                    ):
                        with st.spinner("⚙️ กำลังดำเนินการ..."):
                            stream_graph_updates(user_input=None)
                        st.rerun()

                # ปุ่มปฏิเสธ (Reject)
                with col2:
                    if st.button("❌ ไม่อนุญาต (Reject)", use_container_width=True):
                        with st.spinner("🚫 กำลังส่งคำปฏิเสธ..."):
                            tool_msgs = [
                                ToolMessage(
                                    tool_call_id=tool_call["id"],
                                    content="User denied execution.",
                                )
                            ]
                            agent_app.update_state(
                                config, {"messages": tool_msgs}, as_node="tools"
                            )
                            stream_graph_updates(user_input=None)
                        st.rerun()

except Exception:
    # กัน Error กรณี State ยังไม่เกิด
    pass

# ==========================================
# 7. FOOTER
# ==========================================
st.divider()
st.caption("🎯 **Available Agents:** CodeReviewAgent 🔬 | ResearchAgent 🔍 | DataAnalysisAgent 📊 | DocumentationAgent 📝 | DevOpsAgent 🚀")
st.caption("💡 **Tips:** ใช้คำสั่งเช่น 'Review code', 'Research topic', 'Analyze data', 'Generate docs', 'Setup CI/CD'")
