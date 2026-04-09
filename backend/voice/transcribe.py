import whisper
import uuid
import os

model = whisper.load_model("small")

TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

def transcribe_audio(file_bytes: bytes) -> str:
    file_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.wav")

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    result = model.transcribe(file_path)
    os.remove(file_path)

    return result["text"]