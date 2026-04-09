import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json

# Import Whisper server
import importlib.util
_voice_server_path = os.path.join(os.path.dirname(__file__), "../voice-to-text/server.py")
_spec = importlib.util.spec_from_file_location("voice_server", _voice_server_path)
_voice_server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_voice_server)
transcribe_audio_file = _voice_server.transcribe_audio_file

app = FastAPI(title="Test Xanh SM Buddy API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

# Hard-coded agent logic for testing
def run_agent_simple(transcript: str):
    # Base case: map "Nhà" to a specific location
    if "nhà" in transcript.lower() or "home" in transcript.lower():
        return json.dumps({
            "user_id": "bro_01",
            "pickup_text": "Nhà",
            "destination_text": "Vin Uni",
            "vehicle_type": "bike",
            "current_gps": {"lat": 21.0285, "lng": 105.8542}
        })
    # Default fallback
    return json.dumps({
        "message": f"Received: {transcript}"
    })


class AgentResponse(BaseModel):
    transcript: Optional[str] = None
    agent_reply: str
    session_id: str


@app.post("/voice-agent")
async def voice_agent(file: UploadFile = File(...), session_id: str = "default"):
    # Validate file
    if not file.filename.lower().endswith((".mp3", ".wav", ".m4a", ".flac")):
        raise HTTPException(status_code=400, detail="File type not supported")

    file_path = os.path.join(TEMP_DIR, f"{session_id}_{file.filename}")

    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Transcribe
        transcript = transcribe_audio_file(file_path)

        if not transcript:
            transcript = "(Không nhận diện được giọng nói)"

        # Run hard-coded agent
        agent_reply = run_agent_simple(transcript)

        return AgentResponse(
            transcript=transcript,
            agent_reply=agent_reply,
            session_id=session_id
        )

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)