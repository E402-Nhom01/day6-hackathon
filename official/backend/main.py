import json
import os
import re
import tempfile
from pathlib import Path
from typing import Dict, Optional

import httpx
import soundfile as sf
import whisper
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# DeepFilterNet
from df.enhance import enhance, init_df, load_audio

# ==================== INIT ====================
load_dotenv()

app = FastAPI(title="XanhSM Voice Booking AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== REQUEST ====================
class ParseRequest(BaseModel):
    text: str
    session_id: str
    user_lat: Optional[float] = None
    user_lng: Optional[float] = None

SESSION_STORE: Dict[str, dict] = {}

# ==================== MODELS ====================
print("🔄 Loading DeepFilterNet...")
try:
    df_model, df_state, _ = init_df()
    print("✅ DeepFilterNet loaded!")
except Exception as e:
    print(f"⚠️ DeepFilterNet failed: {e}")
    df_model = df_state = None

whisper_model = whisper.load_model("base")

# ==================== ENV ====================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# ==================== AUDIO ====================
def preprocess_audio(audio_bytes: bytes) -> bytes:
    if not df_model or not df_state:
        return audio_bytes

    tmp_in = tmp_out = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_in = f.name

        audio, sr = load_audio(tmp_in)
        enhanced = enhance(df_model, df_state, audio)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, enhanced.cpu().numpy().squeeze(), sr)
            tmp_out = f.name

        with open(tmp_out, "rb") as f:
            return f.read()

    except:
        return audio_bytes
    finally:
        for p in [tmp_in, tmp_out]:
            if p and Path(p).exists():
                Path(p).unlink(missing_ok=True)


def run_whisper(audio_bytes: bytes) -> str:
    cleaned = preprocess_audio(audio_bytes)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(cleaned)
        tmp_path = tmp.name

    try:
        result = whisper_model.transcribe(tmp_path, language="vi", fp16=False)
        return result["text"].strip()
    finally:
        Path(tmp_path).unlink(missing_ok=True)

# ==================== TEXT NORMALIZE ====================
def normalize_text(text: str) -> str:
    text = text.lower()

    replacements = {
        "xem máy": "xe máy",
        "xe may": "xe máy",
        "vnuni": "vin uni",
        "vinuni": "vin uni",
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text.strip()

# ==================== OPENROUTER ====================
def call_openrouter(prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("Missing OPENROUTER_API_KEY")

    resp = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        json={
            "model": "qwen/qwen-2.5-7b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        },
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        timeout=60.0,
    )

    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

# ==================== PARSE ====================
def run_parse(text: str) -> dict:
    text = normalize_text(text)

    prompt = f"""
Bạn là AI đặt xe.

Câu:
"{text}"

YÊU CẦU:
- Sửa lỗi chính tả
- Xác định:
  start_point, end_point, vehicle_type

QUY TẮC:
- "từ X đến Y" → start = X, end = Y
- "đến X" → start = "Hiện tại"
- "xe máy" → motorbike
- "ô tô" → car

Trả JSON:
{{
  "corrected_text": "...",
  "start_point": "...",
  "end_point": "...",
  "vehicle_type": "motorbike" hoặc "car"
}}
"""

    try:
        raw = call_openrouter(prompt)
        match = re.search(r"\{[\s\S]*\}", raw)
        return json.loads(match.group(0))
    except:
        return {
            "corrected_text": text,
            "start_point": "Hiện tại",
            "end_point": None,
            "vehicle_type": None,
        }

# ==================== GOOGLE MAP ====================
async def resolve_location(name: str, context=None) -> dict:
    if not name:
        return {"lat": None, "lng": None}

    # Current location
    if name.lower() in ["hiện tại", "current location"]:
        if context and context.get("user_lat"):
            return {
                "display_name": "Vị trí hiện tại",
                "lat": context["user_lat"],
                "lng": context["user_lng"],
                "source": "gps",
            }

    # Google Places
    if GOOGLE_MAPS_API_KEY:
        try:
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": name + " Việt Nam",
                "key": GOOGLE_MAPS_API_KEY,
            }

            async with httpx.AsyncClient() as client:
                res = await client.get(url, params=params)
                data = res.json()

            if data.get("results"):
                r = data["results"][0]
                loc = r["geometry"]["location"]

                return {
                    "display_name": r.get("name"),
                    "full_address": r.get("formatted_address"),
                    "lat": loc["lat"],
                    "lng": loc["lng"],
                    "source": "google",
                }

        except Exception as e:
            print("[Map Error]", e)

    return {"display_name": name, "lat": None, "lng": None}

# ==================== FLOW ====================
async def run_flow(text: str, session_id: str, context: dict):
    parsed = run_parse(text)

    start_resolved = await resolve_location(parsed.get("start_point"), context)
    end_resolved = await resolve_location(parsed.get("end_point"), context)

    return {
        "session_id": session_id,
        "corrected_text": parsed.get("corrected_text"),
        "start_point": parsed.get("start_point"),
        "end_point": parsed.get("end_point"),
        "vehicle_type": parsed.get("vehicle_type"),
        "resolved_start": start_resolved,
        "resolved_end": end_resolved,
        "ready_to_book": end_resolved.get("lat") is not None,
    }

# ==================== API ====================
@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    text = run_whisper(audio_bytes)
    return {"text": text}


@app.post("/parse")
async def parse(req: ParseRequest):
    try:
        context = {
            "user_lat": req.user_lat,
            "user_lng": req.user_lng,
        }
        return await run_flow(req.text, req.session_id, context)
    except Exception as e:
        raise HTTPException(500, str(e))


# ==================== RUN ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)