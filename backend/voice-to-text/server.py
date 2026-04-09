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

def transcribe_audio_file(file_path: str) -> str:
    """Transcribe file audio bằng Whisper, trả về text."""
    result = model.transcribe(
        file_path, 
        fp16=torch.cuda.is_available(), 
        language="vi",
        condition_on_previous_text=False # Giảm thiểu hallucination lặp lại
    )
    
    # Các câu hallucination thường gặp của Whisper cho tiếng Việt khi im lặng
    hallucinations = [
        "cảm ơn các bạn",
        "cảm ơn đã theo dõi",
        "đăng ký kênh",
        "nhớ đăng ký kênh",
        "hẹn gặp lại",
        "xin chào các bạn",
        "âm nhạc",
        "subtitles by",
        "amara.org",
        "chúc các bạn"
    ]
    
    valid_segments = []
    for segment in result.get("segments", []):
        # Nếu mô hình chắc chắn > 60% là không có tiếng người, ta bỏ qua đoạn đó
        if segment.get("no_speech_prob", 0) > 0.6:
            continue
            
        seg_text = segment.get("text", "").strip()
        seg_lower = seg_text.lower()
        
        # Nếu segment chứa các câu spam quen thuộc thì bỏ qua
        if any(h in seg_lower for h in hallucinations) and len(seg_text) < 60:
            continue
            
        valid_segments.append(seg_text)

    return " ".join(valid_segments).strip()

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
        transcript = transcribe_audio_file(file_path)
        
        return {
            "filename": file.filename,
            "transcript": transcript
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)