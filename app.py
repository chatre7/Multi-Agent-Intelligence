import streamlit as st
import json
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
# Import ตัวแปร app (Graph) จากไฟล์ Backend ของเรา
from planner_agent_team_v3 import app as agent_app

# ==========================================
# 1. SETUP PAGE & SESSION
# ==========================================
st.set_page_config(page_title="AI Agent Team", page_icon="🤖", layout="wide")

st.title("🤖 AI Developer Team (Agentic RAG)")
st.caption("🚀 Powered by Planner + Coder + Tester + Supervisor Agents")

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = "web_session_v1"

# Sidebar: ปุ่มเคลียร์ประวัติ
with st.sidebar:
    st.header("⚙️ Control Panel")
    if st.button("🗑️ Clear History"):
        st.session_state["messages"] = []
        st.rerun()
    st.info(f"Thread ID: {st.session_state['thread_id']}")

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def get_avatar(sender_name):
    """เลือก Icon ตามบทบาทของ Agent"""
    if "Planner" in sender_name: return "🗺️"
    if "Coder" in sender_name: return "📝"
    if "Tester" in sender_name: return "🧪"
    if "Critic" in sender_name: return "🤔"
    if "Reviewer" in sender_name: return "🧐"
    if "Supervisor" in sender_name: return "🧠"
    return "🤖"

def stream_graph_updates(user_input=None):
    """ฟังก์ชันหลักสำหรับรัน Graph และแสดงผลข้อความ"""
    config = {"configurable": {"thread_id": st.session_state["thread_id"]}}
    
    if user_input:
        # กรณี User พิมพ์สั่งงานใหม่
        inputs = {"messages": [HumanMessage(content=user_input)], "sender": "User"}
        iterator = agent_app.stream(inputs, config, stream_mode="values")
    else:
        # กรณี Resume (กดปุ่ม Approve) ส่ง None เพื่อให้ทำต่อ
        iterator = agent_app.stream(None, config, stream_mode="values")

    # วนลูปรับข้อความจาก AI
    for event in iterator:
        message = event.get("messages")
        if message:
            last_msg = message[-1]
            # เราจะแสดงเฉพาะข้อความจาก AI (AIMessage) ที่มีเนื้อหา (content)
            # และไม่แสดง Tool Call ดิบๆ (มันดูยาก)
            if isinstance(last_msg, AIMessage) and last_msg.content:
                sender = event.get("sender", "Agent")
                
                # แสดงผลหน้าจอ
                with st.chat_message(sender, avatar=get_avatar(sender)):
                    st.markdown(f"**{sender}:**")
                    st.write(last_msg.content)
                
                # บันทึกลง Session State (กันหน้าจohายตอน Refresh)
                # เช็คกันซ้ำ: ถ้าข้อความล่าสุดเหมือนกันเป๊ะ ไม่ต้อง append
                if not st.session_state["messages"] or st.session_state["messages"][-1]["content"] != last_msg.content:
                    st.session_state["messages"].append({"role": sender, "content": last_msg.content})

# ==========================================
# 3. DISPLAY CHAT HISTORY
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
# 4. CHAT INPUT
# ==========================================
if prompt := st.chat_input("สั่งงานทีม AI ของคุณที่นี่..."):
    # แสดงข้อความ User
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    # ส่งเข้า Graph
    with st.spinner("🤖 ทีมงานกำลังระดมสมอง..."):
        stream_graph_updates(user_input=prompt)

# ==========================================
# 5. HUMAN-IN-THE-LOOP (APPROVAL BUTTONS)
# ==========================================
# ส่วนนี้จะทำงานทุกครั้งที่หน้าจอ Refresh เพื่อเช็คว่า AI ติดสถานะ "รออนุมัติ" หรือไม่
try:
    config = {"configurable": {"thread_id": st.session_state["thread_id"]}}
    snapshot = agent_app.get_state(config)
    
    # เช็คว่า Next Step คือ 'tools' หรือไม่ (ถ้าใช่ แปลว่าติด interrupt_before)
    if snapshot.next and "tools" in snapshot.next:
        last_msg = snapshot.values['messages'][-1]
        
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
                    st.warning(f"**AI ขออนุญาตใช้เครื่องมือ:** `{tool_name}`")
                
                st.code(f"Arguments: {json.dumps(tool_args, indent=2)}")
                
                col1, col2 = st.columns([1, 1])
                
                # ปุ่มอนุมัติ (Approve)
                with col1:
                    if st.button("✅ อนุญาต (Approve)", type="primary", use_container_width=True):
                        with st.spinner("กำลังดำเนินการต่อ... (Executing Tool)"):
                            # Resume Graph (ส่ง None)
                            stream_graph_updates(user_input=None)
                        st.rerun() # Refresh หน้าจอเพื่อเคลียร์ปุ่ม

                # ปุ่มปฏิเสธ (Reject)
                with col2:
                    if st.button("❌ ไม่อนุญาต (Reject)", use_container_width=True):
                        with st.spinner("กำลังส่งคำปฏิเสธ..."):
                            # สร้างข้อความปฏิเสธ (ToolMessage) ใส่กลับไปใน State
                            tool_msgs = [ToolMessage(tool_call_id=tool_call['id'], content="User denied execution.")]
                            agent_app.update_state(config, {"messages": tool_msgs}, as_node="tools")
                            
                            # ให้ AI รับรู้ว่าโดนปฏิเสธ แล้วทำงานต่อ (เช่น ขอโทษ หรือถามใหม่)
                            stream_graph_updates(user_input=None)
                        st.rerun()

except Exception as e:
    # กัน Error กรณี State ยังไม่เกิด
    pass