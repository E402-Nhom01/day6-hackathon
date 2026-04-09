import json
import os
import re
import tempfile
from pathlib import Path
from typing import Dict

import httpx
import numpy as np
import soundfile as sf
import torch
import whisper
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# DeepFilterNet
from df.enhance import enhance, init_df, load_audio

# ----------------------
# Load .env
# ----------------------
load_dotenv()

# ----------------------
# FastAPI Setup
# ----------------------
app = FastAPI(title="Voice Ride Booking API (Vietnamese)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------
# Models
# ----------------------
class ParseRequest(BaseModel):
    text: str
    session_id: str


SESSION_STORE: Dict[str, dict] = {}

# ----------------------
# Fake User Saved Locations
# ----------------------
USER_SAVED_LOCATIONS = {
    "Nhà": "Nhà riêng - 123 Đường ABC, Quận 1, TP.HCM",
    "nhà": "Nhà riêng - 123 Đường ABC, Quận 1, TP.HCM",
    "công ty": "Công ty TechViệt - 456 Tower, Quận 7, TP.HCM",
    "văn phòng": "Công ty TechViệt - 456 Tower, Quận 7, TP.HCM",
    "trường": "Đại học Bách Khoa Hà Nội",
    "đại học": "Đại học Bách Khoa Hà Nội",
    "win uni": "Win University",
    "wini uni": "Win University",
    "vin uni": "Vin University",
}

# ----------------------
# DeepFilterNet Setup
# ----------------------
print("🔄 Loading DeepFilterNet model...")
try:
    df_model, df_state, _ = init_df()
    print("✅ DeepFilterNet loaded!")
except Exception as e:
    print(f"⚠️ DeepFilterNet failed: {e}")
    df_model = None
    df_state = None

# ----------------------
# Whisper
# ----------------------
whisper_model = whisper.load_model("base")


def preprocess_audio_with_deepfilter(audio_bytes: bytes) -> bytes:
    if df_model is None or df_state is None:
        return audio_bytes
    tmp_in_path = tmp_out_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_in_path = tmp.name

        audio, sr = load_audio(tmp_in_path)
        enhanced = enhance(df_model, df_state, audio)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_out:
            sf.write(tmp_out.name, enhanced.cpu().numpy().squeeze(), sr)
            tmp_out_path = tmp_out.name

        with open(tmp_out_path, "rb") as f:
            return f.read()
    except Exception as e:
        print(f"[DEEPFILTER_ERROR] {e}")
        return audio_bytes
    finally:
        for p in [tmp_in_path, tmp_out_path]:
            if p and Path(p).exists():
                Path(p).unlink(missing_ok=True)


def run_whisper(audio_bytes: bytes) -> str:
    cleaned = preprocess_audio_with_deepfilter(audio_bytes)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(cleaned)
        tmp_path = tmp.name

    try:
        result = whisper_model.transcribe(
            tmp_path, language="vi", fp16=False, 
            initial_prompt="đặt xe, về nhà, về công ty, về trường"
        )
        return result["text"].strip()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ----------------------
# OpenRouter
# ----------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def call_openrouter(prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("Missing OPENROUTER_API_KEY")
    # ... (your full call_openrouter implementation - keep the one from previous full code)
    models_to_try = [os.getenv("OPENROUTER_MODEL", "google/gemma-4-26b-a4b-it:free"), 
                     os.getenv("OPENROUTER_FALLBACK_MODEL", "qwen/qwen-2.5-7b-instruct")]
    for model_name in models_to_try:
        for attempt in range(1, 3):
            try:
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 300,
                }
                headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
                with httpx.Client(timeout=60) as client:
                    resp = client.post(f"https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
                if resp.status_code >= 400:
                    raise RuntimeError(resp.text)
                return resp.json()["choices"][0]["message"]["content"].strip()
            except:
                continue
    raise RuntimeError("OpenRouter failed")


# ----------------------
# Improved Correction + Parse with better correction handling
# ----------------------
def run_gwen_correct(text: str, context: dict) -> str:
    prompt = f"""
Bạn là trợ lý đặt xe.

Sửa lỗi chính tả, làm cho câu tự nhiên và chuẩn hóa địa danh.
Giữ nguyên ý người dùng nói (đặc biệt là từ "về nhà", "về trường"...).

Câu gốc: {text}

Chỉ trả về một câu hoàn chỉnh.
"""
    try:
        return call_openrouter(prompt) or text
    except:
        return text


def run_gwen_parse(text: str, context: dict) -> dict:
    context_hint = ""
    if any(context.get(k) for k in ["start_point", "end_point", "vehicle_type"]):
        context_hint = f"""
Thông tin đã biết từ trước:
- Điểm đón: {context.get('start_point') or 'chưa biết'}
- Điểm đến: {context.get('end_point') or 'chưa biết'}
- Loại xe: {context.get('vehicle_type') or 'chưa biết'}
"""

    prompt = f"""
Bạn là trợ lý đặt xe.

{context_hint}

Hiểu rõ câu của người dùng, đặc biệt là trường hợp sửa chữa:
- "về nhà", "về công ty", "về trường" → end_point = Nhà / công ty / trường, start_point thường là "Hiện tại" hoặc để trống.
- Từ như "à không", "thay đổi", "sửa lại", "không phải... mà" → ưu tiên thông tin mới nhất.

Trích xuất thành JSON:

{{
  "start_point": "string hoặc null (nếu không rõ thì để null)",
  "end_point": "string hoặc null",
  "vehicle_type": "car" hoặc "motorbike" hoặc null
}}

Câu: {text}

Chỉ trả JSON thuần túy. Không markdown, không giải thích.
"""

    try:
        raw = call_openrouter(prompt)
        raw = raw.replace("```json", "").replace("```", "").strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise RuntimeError("No JSON")

        parsed = json.loads(match.group(0))

        # Normalize vehicle
        if parsed.get("vehicle_type"):
            vt = str(parsed.get("vehicle_type", "")).lower().strip()
            parsed["vehicle_type"] = "car" if "car" in vt or "ô tô" in vt else "motorbike" if "moto" in vt or "xe máy" in vt else None

        return parsed
    except Exception as e:
        print("[PARSE_ERROR]", e)
        return {"start_point": None, "end_point": None, "vehicle_type": None}


# Merge, Clarification, Resolve... (same as before)
def merge_state(prev: dict, new: dict) -> dict:
    result = dict(prev)
    for k in ["start_point", "end_point", "vehicle_type"]:
        if new.get(k) is not None:
            result[k] = new[k]
    return result


def build_clarification(data: dict) -> dict:
    missing = []
    questions = []

    if not data.get("start_point"):
        missing.append("start_point")
        questions.append("Bạn muốn được đón ở đâu?")
    if not data.get("end_point"):
        missing.append("end_point")
        questions.append("Bạn muốn đi đến đâu?")
    if not data.get("vehicle_type"):
        missing.append("vehicle_type")
        questions.append("Bạn muốn xe máy hay ô tô?")

    return {
        "needs_clarification": len(missing) > 0,
        "missing_fields": missing,
        "questions": questions
    }


def generate_clarification_message(clarification: dict) -> str:
    if not clarification["needs_clarification"]:
        return "✅ Đã đủ thông tin để đặt xe!"
    return "\n".join(clarification["questions"]) if len(clarification["questions"]) > 1 else clarification["questions"][0]


def resolve_saved_location(name: str) -> str:
    return USER_SAVED_LOCATIONS.get(str(name).strip(), name)


# ----------------------
# Main Flow
# ----------------------
def run_parse_flow(text: str, session_id: str):
    prev = SESSION_STORE.get(session_id, {"start_point": None, "end_point": None, "vehicle_type": None})

    intent = detect_intent(text)
    if not intent.get("is_ride_booking", True):
        return {"is_off_topic": True, "off_topic_message": "Xin lỗi, tôi chỉ hỗ trợ đặt xe."}

    corrected = run_gwen_correct(text, prev)
    parsed = run_gwen_parse(corrected, prev)

    merged = merge_state(prev, parsed)
    clarification = build_clarification(merged)

    SESSION_STORE[session_id] = merged

    return {
        "session_id": session_id,
        "corrected_text": corrected,
        "start_point": merged.get("start_point"),
        "end_point": merged.get("end_point"),
        "vehicle_type": merged.get("vehicle_type"),
        "resolved_start": resolve_saved_location(merged.get("start_point") or ""),
        "resolved_end": resolve_saved_location(merged.get("end_point") or ""),
        "needs_clarification": clarification["needs_clarification"],
        "clarification_message": generate_clarification_message(clarification),
        "questions": clarification["questions"]
    }


# API Endpoints (keep as before)
@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    text = run_whisper(audio_bytes)
    return {"text": text}

@app.post("/parse")
async def parse_ride(req: ParseRequest):
    if not req.session_id:
        raise HTTPException(400, "Missing session_id")
    return run_parse_flow(req.text, req.session_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)