from flask import Flask, request, jsonify
import whisper
import tempfile
import os
from flask_cors import CORS  # <-- allow cross-origin requests from Expo Web

app = Flask(__name__)
CORS(app)  # allow all origins (for dev/testing)

model = whisper.load_model("base")  # tiny, small, base, etc.

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    audio_file = request.files['file']

    # Get the file extension dynamically from the uploaded file
    _, ext = os.path.splitext(audio_file.filename)
    if not ext:
        ext = ".webm"  # default if none

    # Save to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    # Transcribe with Whisper
    try:
        result = model.transcribe(tmp_path, language="vi")  # Vietnamese
        transcript = result["text"]
    except Exception as e:
        transcript = f"Error: {str(e)}"
    finally:
        os.remove(tmp_path)  # clean up temp file

    return jsonify({"transcript": transcript})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)