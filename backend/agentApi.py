import os
import sys
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Import agent graph, logic, và history từ agent.py
from agent import graph, write_log, run_agent, chat_sessions

# Thêm path để import module từ thư mục voice-to-text
sys.path.append(os.path.join(os.path.dirname(__file__), "voice-to-text"))
from server import transcribe_audio_file

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


# ========================
# API ENDPOINTS
# ========================

@app.post(
    "/voice-agent",
    response_model=AgentResponse,
    summary="Voice → Text → Agent",
    description="Nhận file âm thanh, transcribe bằng Whisper, rồi đưa vào Agent xử lý.",
)
async def voice_agent(
    file: UploadFile = File(..., description="File âm thanh (mp3, wav, m4a, flac)"),
    session_id: str = "default",
):
    # Validate file format
    if not file.filename.lower().endswith((".mp3", ".wav", ".m4a", ".flac")):
        raise HTTPException(
            status_code=400,
            detail="Định dạng file không được hỗ trợ. Chỉ chấp nhận: mp3, wav, m4a, flac.",
        )

    file_path = os.path.join(TEMP_DIR, f"{session_id}_{file.filename}")

    try:
        # 1. Lưu file tạm
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Transcribe audio → text
        transcript = transcribe_audio_file(file_path)
        write_log("Whisper Transcript", transcript)
        print(f"[Whisper] Transcript: {transcript}")

        if not transcript:
            raise HTTPException(
                status_code=400,
                detail="Không nhận diện được giọng nói từ file audio.",
            )

        # 3. Đưa transcript vào Agent
        agent_reply = run_agent(transcript, session_id)

        return AgentResponse(
            transcript=transcript,
            agent_reply=agent_reply,
            session_id=session_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.post(
    "/text-agent",
    response_model=AgentResponse,
    summary="Text → Agent",
    description="Nhận text trực tiếp và đưa vào Agent xử lý.",
)
async def text_agent(request: TextRequest):
    try:
        agent_reply = run_agent(request.text, request.session_id)
        return AgentResponse(
            transcript=None,
            agent_reply=agent_reply,
            session_id=request.session_id,
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
