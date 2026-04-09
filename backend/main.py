from fastapi import FastAPI, UploadFile, File
from whisper_service import transcribe_audio
from agent import extract_booking
from models import UserContext
import json

app = FastAPI()

# mock user context (you will replace with DB later)
USER_CONTEXT = {
    "user_id": "bro_01",
    "saved_locations": [
        {"label": "Nhà riêng", "address": "Số 1 Chùa Bộc, Hà Nội", "lat": 21.007, "lng": 105.827},
        {"label": "Công ty", "address": "Vinhomes Ocean Park", "lat": 20.995, "lng": 105.942}
    ],
    "recent_trips": [
        {"destination": "Vincom Bà Triệu", "count": 5}
    ]
}

@app.post("/voice-booking")
async def voice_booking(file: UploadFile = File(...)):
    audio_bytes = await file.read()

    # 1. Speech → text
    transcript = transcribe_audio(audio_bytes)

    # 2. Text → structured booking
    booking = extract_booking(transcript, USER_CONTEXT)

    return {
        "transcript": transcript,
        "booking": booking
    }