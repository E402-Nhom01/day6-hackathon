import queue
import sounddevice as sd
import numpy as np
import whisper
import threading
import keyboard  # Cần chạy bằng quyền Admin/Sudo
import io
import torch

# ========================
# CONFIG
# ========================
SAMPLE_RATE = 16000
CHANNELS = 1
MODEL_SIZE = "large-v3"  # Các lựa chọn: tiny, base, small, medium, large-v3

# Kiểm tra xem có GPU không để chạy cho nhanh
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🚀 Loading Whisper model '{MODEL_SIZE}' on {device}...")
model = whisper.load_model(MODEL_SIZE, device=device)

audio_queue = queue.Queue()
full_audio_buffer = []
is_recording = True

# ========================
# AUDIO CALLBACK
# ========================
def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    if is_recording:
        audio_queue.put(indata.copy())

# ========================
# AUDIO COLLECTOR THREAD
# ========================
def collect_audio():
    global full_audio_buffer
    while True:
        chunk = audio_queue.get()
        full_audio_buffer.append(chunk)

# ========================
# TRANSCRIBE FUNCTION (LOCAL WHISPER)
# ========================
def transcribe_audio():
    global full_audio_buffer

    if not full_audio_buffer:
        print("⚠️ No audio recorded")
        return

    print("\n⏳ Transcribing locally with Whisper...")

    # Gom các chunk audio lại
    buffer_copy = list(full_audio_buffer)
    full_audio_buffer.clear()
    
    # Kết hợp các mảnh thành một mảng numpy duy nhất
    audio_data = np.concatenate(buffer_copy, axis=0).flatten()

    # Whisper yêu cầu float32 và normalize về khoảng [-1, 1]
    # Vì InputStream đang dùng dtype='int16', ta cần chuyển đổi:
    audio_data_fp32 = audio_data.astype(np.float32) / 32768.0

    try:
        # Chạy nhận diện
        # task="transcribe" để chuyển audio sang text
        # language="vi" để tối ưu cho tiếng Việt
        result = model.transcribe(audio_data_fp32, fp16=torch.cuda.is_available(), language="vi")

        if result['text'].strip():
            print("\n📝 TRANSCRIPT:")
            print(result['text'].strip())
        else:
            print("⚠️ Could not detect any speech")

    except Exception as e:
        print("❌ Error during transcription:", e)

    print("\n🎤 Continue speaking... (press 'q' to transcribe)")

# ========================
# MAIN
# ========================
def main():
    print("🎤 Recording started...")
    print(f"⚙️ Running on: {device.upper()}")
    print("⌨️ Press 'q' to transcribe | Press 'esc' to exit\n")

    # Thread gom audio
    threading.Thread(target=collect_audio, daemon=True).start()

    # Đăng ký phím tắt
    keyboard.add_hotkey('q', transcribe_audio)

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype='int16',
        callback=audio_callback
    ):
        keyboard.wait('esc')
        print("👋 Exiting...")

# ========================
# RUN
# ========================
if __name__ == "__main__":
    main()