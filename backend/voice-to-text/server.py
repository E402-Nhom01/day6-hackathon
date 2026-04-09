import os
import whisper
import torch
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ========================
# METADATA CHO SWAGGER
# ========================
app = FastAPI(
    title="Whisper STT API",
    description="""
    API chuyển đổi giọng nói thành văn bản sử dụng mô hình OpenAI Whisper.
    * **Hỗ trợ định dạng:** MP3, WAV, M4A, FLAC.
    * **Ngôn ngữ mặc định:** Tiếng Việt (vi).
    """,
    version="1.0.0",
    contact={
        "name": "AI Engineer",
        "email": "support@example.com",
    },
)

# Schema cho Response để Swagger hiển thị mẫu kết quả
class TranscribeResponse(BaseModel):
    filename: str
    transcript: str

# Load model (nên để bên ngoài endpoint để tránh load lại nhiều lần)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_SIZE = "large-v3"
print(f"--- Loading model {MODEL_SIZE} ---")
model = whisper.load_model(MODEL_SIZE, device=DEVICE)

TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.post(
    "/transcribe", 
    response_model=TranscribeResponse,
    summary="Chuyển đổi Audio sang Text",
    description="Nhận một file âm thanh và trả về đoạn văn bản đã được nhận diện."
)
async def transcribe_audio(
    file: UploadFile = File(..., description="File âm thanh cần nhận diện (mp3, m4a, wav,...)")
):
    if not file.filename.lower().endswith(('.mp3', '.wav', '.m4a', '.flac')):
        raise HTTPException(status_code=400, detail="Định dạng file không được hỗ trợ.")

    file_path = os.path.join(TEMP_DIR, file.filename)

    try:
        # Lưu file tạm
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Transcribe
        result = model.transcribe(
            file_path, 
            fp16=torch.cuda.is_available(), 
            language="vi"
        )
        
        return {
            "filename": file.filename,
            "transcript": result['text'].strip()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)