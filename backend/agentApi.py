import os
import sys
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import httpx
from typing import Optional

# Import agent graph, logic, và history từ agent.py
from agent import graph, write_log, run_agent, chat_sessions

import importlib.util

# Load module server.py từ thư mục voice-to-text bằng importlib do thư mục có chứa ký tự '-'
# Viêc này tránh conflict với backend/server.py
_voice_server_path = os.path.join(os.path.dirname(__file__), "voice-to-text", "server.py")
_spec = importlib.util.spec_from_file_location("voice_server", _voice_server_path)
_voice_server = importlib.util.module_from_spec(_spec)
# Add to sys.modules for any future resolution within that module (though not strictly necessary here)
sys.modules["voice_server"] = _voice_server
_spec.loader.exec_module(_voice_server)
transcribe_audio_file = _voice_server.transcribe_audio_file

# ========================
# KHỞI TẠO FASTAPI
# ========================
app = FastAPI(
    title="Xanh SM Buddy API",
    description="""
    API tích hợp Voice-to-Text (Whisper) và Agent (LangGraph).
    - Nhận file âm thanh, chuyển thành text, rồi xử lý qua Agent.
    - Hoặc nhận text trực tiếp để xử lý qua Agent.
    """,
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

# ========================
# SCHEMA
# ========================
class TextRequest(BaseModel):
    text: str
    session_id: Optional[str] = "default"


class AgentResponse(BaseModel):
    transcript: Optional[str] = None
    agent_reply: str
    session_id: str
    booking_status: Optional[dict] = None


async def call_booking_api(agent_reply_str: str):
    """
    Hàm helper để parse agent_reply và gọi đến API booking intent.
    """
    try:
        # 1. Parse JSON từ agent
        data = json.loads(agent_reply_str)
        
        # 2. Chuẩn bị payload cho booking API
        # Chỉ lấy các field mà main.py yêu cầu
        payload = {
            "user_id": data.get("user_id", "bro_01"),
            "pickup_text": data.get("pickup_text", "Home"),
            "destination_text": data.get("destination_text"),
            "vehicle_type": data.get("vehicle_type", "bike"),
            "current_gps": data.get("current_gps", {})
        }
        
        # 3. Gọi API http://127.0.0.1:8000/api/v1/booking/intent
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://127.0.0.1:8000/api/v1/booking/intent",
                json=payload,
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "ERROR", "message": f"Booking API error: {response.status_code}"}
                
    except json.JSONDecodeError:
        # Nếu agent chưa trả về JSON (đang hội thoại bình thường) thì bỏ qua
        return None
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


# ========================
# API ENDPOINTS
# ========================

@app.post("/voice-agent")
async def voice_agent(
    file: UploadFile = File(..., description="File âm thanh (mp3, wav, m4a, flac)"),
    session_id: str = "default",
):
    file_path = os.path.join(TEMP_DIR, f"{session_id}_{file.filename}")

    try:
        # 1. Lưu file tạm
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Transcribe audio → text
        transcript = transcribe_audio_file(file_path)

        if not transcript:
            return {"error": "Không nhận diện được giọng nói từ file audio."}

        # 3. Gửi transcript vào Agent
        agent_reply_str = run_agent(transcript, session_id)

        # 4. Parse agent output
        import json
        try:
            agent_json = json.loads(agent_reply_str)
        except:
            agent_json = {}

        # 5. Trả về frontend trực tiếp (for debug and display)
        return {
            "transcript": transcript,
            "from": agent_json.get("pickup_text", ""),
            "to": agent_json.get("destination_text", ""),
            "vehicle_type": agent_json.get("vehicle_type", "")
        }

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
@app.post(
    "/text-agent",
    summary="Text → Agent",
    description="Nhận text trực tiếp và đưa vào Agent xử lý.",
)
async def text_agent(request: TextRequest):
    try:
        agent_reply = run_agent(request.text, request.session_id)
        
        # Gọi Booking API nếu có đủ thông tin (JSON)
        booking_res = await call_booking_api(agent_reply)
        
        if booking_res:
            return booking_res

        return AgentResponse(
            transcript=None,
            agent_reply=agent_reply,
            session_id=request.session_id,
            booking_status=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")


@app.delete(
    "/session/{session_id}",
    summary="Xoá session chat",
    description="Xoá lịch sử chat của một session.",
)
async def delete_session(session_id: str):
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        return {"message": f"Đã xoá session '{session_id}'."}
    raise HTTPException(status_code=404, detail=f"Session '{session_id}' không tồn tại.")


# ========================
# CHẠY SERVER
# ========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3003)
