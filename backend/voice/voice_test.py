import whisper

model = whisper.load_model("base")  # start with base

result = model.transcribe("audio.m4a", language="vi")

print(result["text"])