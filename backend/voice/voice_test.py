import whisper

model = whisper.load_model("base")  # start with base

result = model.transcribe("vietnamese.mp3", language="vi")

print(result["text"])