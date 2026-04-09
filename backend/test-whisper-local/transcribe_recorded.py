import os
import whisper
import torch

# ========================
# CONFIG
# ========================
MODEL_SIZE = "large-v3"
# AUDIO_DIR = os.path.join(os.path.dirname(__file__), "recorded-audio")
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "record-3")

def main():
    # Kiểm tra xem có GPU không để chạy cho nhanh
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading Whisper model '{MODEL_SIZE}' on {device}...")
    model = whisper.load_model(MODEL_SIZE, device=device)

    # Lấy danh sách các file audio
    if not os.path.exists(AUDIO_DIR):
        print(f"Directory not found: {AUDIO_DIR}")
        return

    audio_files = [f for f in os.listdir(AUDIO_DIR) if f.lower().endswith(('.mp3', '.wav', '.m4a', '.flac'))]
    
    if not audio_files:
        print(f"No audio files found in {AUDIO_DIR}")
        return

    print(f"Found {len(audio_files)} files. Starting transcription...\n")

    for filename in audio_files:
        file_path = os.path.join(AUDIO_DIR, filename)
        print(f"Processing: {filename}")
        
        try:
            # Chạy nhận diện
            # language="vi" để tối ưu cho tiếng Việt
            result = model.transcribe(file_path, fp16=torch.cuda.is_available(), language="vi")
            
            transcript = result['text'].strip()
            print(f"TRANSCRIPT: {transcript}")
            print("-" * 50)
            
        except Exception as e:
            print(f"Error transcribing {filename}: {e}")

if __name__ == "__main__":
    main()
