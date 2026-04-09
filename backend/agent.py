import os
import sys
from datetime import datetime
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from tools import search_ride_locations
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# CẤU HÌNH LOGGING
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True) 

session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = os.path.join(LOG_DIR, f"session_{session_time}.txt")

def write_log(role: str, content: str):
    """Hàm ghi thông tin vào file log"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%H:%M:%S")
        f.write(f"[{timestamp}] {role}:\n{content}\n")
        f.write("-" * 50 + "\n")
# ==========================================

# 1. Đọc System Prompt
prompt_path = os.path.join(BASE_DIR, "system_prompt.txt")
with open(prompt_path, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# 2. Khai báo State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# 3. Khởi tạo LLM và Tools
tools_list = [search_ride_locations]
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    temperature=0.2,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)
llm_with_tools = llm.bind_tools(tools_list)

# 4. Agent Node
def agent_node(state: AgentState):
    messages = state["messages"]
    
    current_now = datetime.now()
    current_date_str = current_now.strftime("%d/%m/%Y")
    current_time_str = current_now.strftime("%H:%M")
    
    time_context = f"<context>\n- Hôm nay là ngày: {current_date_str}\n- Giờ hiện tại: {current_time_str}\n</context>\n\n"
    dynamic_prompt = time_context + SYSTEM_PROMPT

    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=dynamic_prompt)] + messages
    else:
        messages[0] = SystemMessage(content=dynamic_prompt)

    response = llm_with_tools.invoke(messages)

    # === LOGGING ===
    if response.tool_calls:
        for tc in response.tool_calls:
            msg = f"Gọi tool: {tc['name']}({tc['args']})"
            print(msg)
            write_log("SYSTEM (Tool Call)", msg) 
    else:
        print(f"Trả lời trực tiếp")

    return {"messages": [response]}

# 5. Xây dựng Graph
builder = StateGraph(AgentState)

builder.add_node("agent", agent_node)
tool_node = ToolNode(tools_list)
builder.add_node("tools", tool_node)

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

graph = builder.compile()

# ========================
# LƯU TRỮ CHAT HISTORY THEO SESSION
# ========================
chat_sessions: dict[str, list] = {}

def run_agent(user_text: str, session_id: str = "default") -> str:
    """Đưa text vào LangGraph agent và trả về response."""
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    chat_history = chat_sessions[session_id]
    chat_history.append(("human", user_text))

    write_log("User", user_text)

    result = graph.invoke({"messages": chat_history})
    chat_history = result["messages"]
    chat_sessions[session_id] = chat_history

    # Trích xuất text từ message cuối cùng
    final = chat_history[-1]
    text = ""
    if isinstance(final.content, list):
        for item in final.content:
            if isinstance(item, dict) and "text" in item:
                text += item["text"] + " "
            elif isinstance(item, str):
                text += item + " "
    else:
        text = str(final.content)

    text = text.strip()
    if not text:
        text = "(Đang tra cứu dữ liệu...)"

    write_log("SM Buddy", text)
    return text

# 6. Chat loop 
if __name__ == "__main__":
    greeting_msg = "Chào bạn! Mình là trợ lý hỗ trợ đặt xe. Bạn đang muốn đi đâu hoặc có ngân sách bao nhiêu? 😊"
    
    print("=" * 60)
    print("Xanh SM Buddy - Trợ lý Đặt lịch Thông minh")
    print(f"  Log session đang được lưu tại: {LOG_FILE}")
    print("  Gõ 'quit' để thoát")
    print("=" * 60)

    print(f"\nTravelBuddy:\n{greeting_msg}")
    write_log("TravelBuddy (Greeting)", greeting_msg)
    
    chat_history = []
    
    # Vòng lặp chính xử lý Logic Agent bằng cách nhập text trực tiếp
    while True:
        try:
            user_input = input("\n[Bạn]: ").strip()
        except (EOFError, KeyboardInterrupt):
            user_input = "quit"
            
        if not user_input:
            continue
        
        if user_input.lower() in ("quit", "exit", "q"):
            write_log("SYSTEM", "Người dùng đã ngắt kết nối.")
            print("\n👋 Hẹn gặp lại bạn!")
            sys.exit(0) 
            
        write_log("User", user_input) 
        
        print("SM Buddy đang suy nghĩ...")
        
        chat_history.append(("human", user_input))
        
        try:
            result = graph.invoke({"messages": chat_history})
            chat_history = result["messages"]
            final = chat_history[-1]
            
            text = ""
            if isinstance(final.content, list):
                for item in final.content:
                    if isinstance(item, dict) and "text" in item:
                        text += item["text"] + " "
                    elif isinstance(item, str): 
                        text += item + " "
            else:
                text = str(final.content)
            
            text = text.strip()
            
            if not text:
                text = "(Đang tra cứu dữ liệu...)"
                
            print(f"\nSM Buddy: {text}")
            write_log("SM Buddy", text)

        except Exception as e:
            error_msg = "Xin lỗi bạn, đường truyền mạng đến máy chủ bị gián đoạn (Network Error). Bạn vui lòng nhập lại câu hỏi nhé!"
            print(f"\nSM Buddy: {error_msg}")
            write_log("SYSTEM ERROR", str(e))
            
            if chat_history and chat_history[-1][0] == "human":
                chat_history.pop()