import os
import sys
import requests
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
# CONFIG LOGGING
# ==========================================
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = os.path.join(LOG_DIR, f"session_{session_time}.txt")

def write_log(role: str, content: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%H:%M:%S")
        f.write(f"[{timestamp}] {role}:\n{content}\n")
        f.write("-" * 50 + "\n")

# ==========================================
# System prompt
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# ==========================================
# Agent State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# ==========================================
# LLM + Tools
tools_list = [search_ride_locations]
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    temperature=0.2,
)
llm_with_tools = llm.bind_tools(tools_list)

# ==========================================
# Whisper server
WHISPER_URL = os.getenv("WHISPER_URL", "http://127.0.0.1:5050/transcribe")

def transcribe_audio_file_from_url(audio_url: str) -> str:
    """
    Sends an audio URL (from Expo Web or mobile) to the Whisper server
    and returns the transcript.
    """
    try:
        files = {"file": requests.get(audio_url, stream=True).raw}
        response = requests.post(WHISPER_URL, files={"file": ("voice.webm", requests.get(audio_url, stream=True).content)})
        response.raise_for_status()
        data = response.json()
        return data.get("transcript", "(Không có transcript)")
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return "(Lỗi khi chuyển giọng nói sang văn bản)"

# ==========================================
# Agent Node
def agent_node(state: AgentState):
    messages = state["messages"]

    now = datetime.now()
    time_context = f"<context>\n- Hôm nay là ngày: {now.strftime('%d/%m/%Y')}\n- Giờ hiện tại: {now.strftime('%H:%M')}\n</context>\n\n"
    dynamic_prompt = time_context + SYSTEM_PROMPT

    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=dynamic_prompt)] + messages
    else:
        messages[0] = SystemMessage(content=dynamic_prompt)

    response = llm_with_tools.invoke(messages)

    # Log tool calls
    if response.tool_calls:
        for tc in response.tool_calls:
            msg = f"Called tool: {tc['name']}({tc['args']})"
            print(msg)
            write_log("SYSTEM (Tool Call)", msg)
    return {"messages": [response]}

# ==========================================
# Build Graph
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools_list))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")
graph = builder.compile()

# ==========================================
# Chat session storage
chat_sessions: dict[str, list] = {}

def run_agent(user_text: str, session_id: str = "default") -> str:
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    chat_history = chat_sessions[session_id]
    chat_history.append(("human", user_text))
    write_log("User", user_text)

    result = graph.invoke({"messages": chat_history})
    chat_history = result["messages"]
    chat_sessions[session_id] = chat_history

    # Extract final text
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

    text = text.strip() or "(Đang tra cứu dữ liệu...)"
    write_log("SM Buddy", text)
    return text

# ==========================================
# Main Loop with Whisper audio integration
if __name__ == "__main__":
    greeting_msg = "Chào bạn! Mình là trợ lý hỗ trợ đặt xe. Bạn có thể gõ câu hỏi hoặc gửi audio từ Expo Web."
    print("="*60)
    print("Xanh SM Buddy - Trợ lý Đặt lịch Thông minh")
    print(f"  Log session: {LOG_FILE}")
    print("  Gõ 'quit' để thoát")
    print("="*60)
    print(f"\nTravelBuddy:\n{greeting_msg}")
    write_log("TravelBuddy (Greeting)", greeting_msg)

    session_id = "default"
    chat_sessions[session_id] = []

    while True:
        try:
            user_input = input("\n[Bạn]: ").strip()
        except (EOFError, KeyboardInterrupt):
            user_input = "quit"

        if user_input.lower() in ("quit", "exit", "q"):
            write_log("SYSTEM", "Người dùng đã ngắt kết nối.")
            print("\n👋 Hẹn gặp lại bạn!")
            sys.exit(0)

        # If input is a Whisper audio URL from Expo Web
        if user_input.startswith("http"):  # simple check for blob or hosted URL
            print("Chuyển giọng nói sang văn bản (Whisper)...")
            user_input = transcribe_audio_file_from_url(user_input)
            print(f"[Bạn (Whisper)]: {user_input}")

        print("SM Buddy đang suy nghĩ...")
        reply = run_agent(user_input, session_id)
        print(f"\nSM Buddy: {reply}")