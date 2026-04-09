import os
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from voice.transcribe import transcribe_audio

app = FastAPI(title="Voice Booking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VoiceBookingResponse(BaseModel):
    transcript: str
    parsedData: dict


def _clean_text(text: str) -> str:
    return text.strip().strip(". ")


def _parse_booking(text: str) -> dict:
    lower = text.lower()

    origin: Optional[str] = None
    destination: Optional[str] = None
    vehicle: Optional[str] = None

    # English pattern: "from X to Y"
    if " from " in lower and " to " in lower:
        try:
            before, after = lower.split(" from ", 1)
            origin_part, dest_part = after.split(" to ", 1)
            origin = _clean_text(origin_part)
            destination = _clean_text(dest_part)
        except ValueError:
            pass

    # Vietnamese pattern: "từ X đến|tới Y"
    if not origin or not destination:
        for sep in [" đến ", " tới "]:
            if "từ " in lower and sep in lower:
                try:
                    after_tu = lower.split("từ ", 1)[1]
                    origin_part, dest_part = after_tu.split(sep, 1)
                    origin = _clean_text(origin_part)
                    destination = _clean_text(dest_part)
                    break
                except ValueError:
                    pass

    if "xe máy" in lower or "bike" in lower:
        vehicle = "bike"
    if "ô tô" in lower or "xe hơi" in lower or "car" in lower:
        vehicle = "car"

    return {
        "from": origin if origin else None,
        "to": destination if destination else None,
        "vehicle": vehicle,
    }


@app.post("/voice-booking", response_model=VoiceBookingResponse)
async def voice_booking(file: UploadFile = File(...)):
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty audio file")

        transcript = transcribe_audio(content)
        parsed = _parse_booking(transcript)

        return {
            "transcript": transcript,
            "parsedData": parsed,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Server error: {exc}")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
