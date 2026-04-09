import os
import shutil
import importlib.util
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import hàm transcribe từ server.py (do đã move cùng chung folder)
vtt_path = os.path.join(os.path.dirname(__file__), "server.py")
spec = importlib.util.spec_from_file_location("vtt_server", vtt_path)
vtt_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vtt_server)

transcribe_audio_file = vtt_server.transcribe_audio_file

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_test_audio")
os.makedirs(TEMP_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    ui_path = os.path.join(os.path.dirname(__file__), "test_ui.html")
    with open(ui_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/test-transcribe")
async def test_transcribe(file: UploadFile = File(...)):
    """API nội bộ để UI test trực tiếp hàm transcribe_audio_file"""
    # webm là định dạng phổ biến trình duyệt thu âm
    ext = file.filename.split('.')[-1]
    if ext not in ['webm', 'mp3', 'wav', 'm4a', 'flac']:
        # Có thể audio lưu dạng blob không có ext rõ, mặc định webm
        file.filename = "recorded.webm"
        
    file_path = os.path.join(TEMP_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Gọi luồng core VTT đang có
        result = transcribe_audio_file(file_path)
        return {"success": True, "text": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    print("Khởi động UI Test Tool tại: http://127.0.0.1:4000")
    uvicorn.run(app, host="127.0.0.1", port=4000)
