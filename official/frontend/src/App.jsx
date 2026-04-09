import React, { useRef, useState } from "react";

export default function App() {
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);

  const [sessionId, setSessionId] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);

  const [transcript, setTranscript] = useState("");
  const [correctedText, setCorrectedText] = useState("");
  const [startPoint, setStartPoint] = useState("");
  const [endPoint, setEndPoint] = useState("");
  const [vehicleType, setVehicleType] = useState(""); // "motorbike" or "car"

  const [needsClarification, setNeedsClarification] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [clarifyInput, setClarifyInput] = useState("");
  const [confirmation, setConfirmation] = useState("pending");
  const [error, setError] = useState("");

  // Edit states
  const [editingField, setEditingField] = useState(null); // "start", "end", or "vehicle"
  const [tempStart, setTempStart] = useState("");
  const [tempEnd, setTempEnd] = useState("");
  const [tempVehicle, setTempVehicle] = useState("");

  function ensureSessionId() {
    if (sessionId) return sessionId;
    const newId = crypto.randomUUID();
    setSessionId(newId);
    return newId;
  }

  async function startRecording() {
    setError("");
    setTranscript("");
    setCorrectedText("");
    setStartPoint("");
    setEndPoint("");
    setVehicleType("");
    setNeedsClarification(false);
    setQuestions([]);
    setClarifyInput("");
    setConfirmation("pending");
    setEditingField(null);

    const newSessionId = ensureSessionId();

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        await handleTranscribeAndParse(audioBlob, newSessionId);
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
    } catch (err) {
      setError("Cannot access microphone. Please allow permission.");
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }
    setIsRecording(false);
  }

  async function handleTranscribeAndParse(audioBlob, activeSessionId) {
    setIsTranscribing(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");

      const res = await fetch("/transcribe", { method: "POST", body: formData });
      if (!res.ok) throw new Error("Transcription failed");

      const data = await res.json();
      setTranscript(data.text || "");

      await sendParse(data.text || "", activeSessionId);
    } catch (err) {
      setError(err.message || "Processing failed.");
    } finally {
      setIsTranscribing(false);
    }
  }

  async function sendParse(text, activeSessionId) {
    try {
      const res = await fetch("/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, session_id: activeSessionId }),
      });

      if (!res.ok) throw new Error("Parse failed");

      const data = await res.json();

      setCorrectedText(data.corrected_text || "");
      setStartPoint(data.start_point || "");
      setEndPoint(data.end_point || "");
      setVehicleType(data.vehicle_type || "");
      setNeedsClarification(Boolean(data.needs_clarification));
      setQuestions(data.questions || []);
    } catch (err) {
      console.error(err);
      setError("Failed to update information.");
    }
  }

  // ====================== EDIT HANDLERS ======================

  const startEdit = (field) => {
    if (field === "start") setTempStart(startPoint);
    if (field === "end") setTempEnd(endPoint);
    if (field === "vehicle") setTempVehicle(vehicleType);
    setEditingField(field);
  };

  const cancelEdit = () => {
    setEditingField(null);
  };

  async function saveEdit() {
    if (!sessionId) return;

    setIsTranscribing(true);
    let correctionText = "";

    try {
      if (editingField === "start" && tempStart.trim()) {
        correctionText = `Sửa điểm đón thành: ${tempStart.trim()}`;
      } else if (editingField === "end" && tempEnd.trim()) {
        correctionText = `Sửa điểm đến thành: ${tempEnd.trim()}`;
      } else if (editingField === "vehicle" && tempVehicle) {
        const vietName = tempVehicle === "car" ? "ô tô" : "xe máy";
        correctionText = `Đổi loại xe thành ${vietName}`;
      }

      if (correctionText) {
        await sendParse(correctionText, sessionId);
      }

      setEditingField(null);
    } catch (err) {
      setError("Failed to save changes.");
    } finally {
      setIsTranscribing(false);
    }
  }

  async function handleClarifySubmit(e) {
    e.preventDefault();
    if (!clarifyInput.trim()) return;

    setIsTranscribing(true);
    try {
      await sendParse(clarifyInput.trim(), ensureSessionId());
      setClarifyInput("");
    } catch (err) {
      setError("Failed to process clarification.");
    } finally {
      setIsTranscribing(false);
    }
  }

  function handleConfirm() {
    if (!endPoint) {
      alert("Vui lòng nhập điểm đến trước khi xác nhận.");
      return;
    }
    setConfirmation("confirmed");
    alert("✅ Đặt xe thành công! (Demo)");
  }

  function handleReject() {
    setConfirmation("rejected");
    alert("Đã hủy đặt xe.");
  }

  return (
    <div className="app">
      <div className="card">
        <h1>🛵 XanhSM Voice Booking</h1>
        <p className="subtitle">Nói tự nhiên hoặc chỉnh sửa thông tin bên dưới</p>

        <div className="controls">
          <button className="btn primary" onClick={startRecording} disabled={isRecording || isTranscribing}>
            🎤 Bắt đầu ghi âm
          </button>
          <button className="btn" onClick={stopRecording} disabled={!isRecording}>
            ⏹ Dừng ghi âm
          </button>
        </div>

        {isTranscribing && <div className="status">Đang xử lý...</div>}
        {error && <div className="error">{error}</div>}

        <div className="transcript">
          <div className="label">Transcript (Nguyên bản)</div>
          <div className="value">{transcript || "—"}</div>
        </div>

        <div className="transcript">
          <div className="label">Corrected</div>
          <div className="value">{correctedText || "—"}</div>
        </div>

        <div className="grid">
          {/* ==================== START POINT ==================== */}
          <div className="box">
            <div className="label">Điểm đón (Start)</div>
            {editingField === "start" ? (
              <div className="edit-mode">
                <input
                  type="text"
                  value={tempStart}
                  onChange={(e) => setTempStart(e.target.value)}
                  className="edit-input"
                  placeholder="Nhập điểm đón..."
                  autoFocus
                />
                <div className="edit-buttons">
                  <button className="btn small primary" onClick={saveEdit}>Lưu</button>
                  <button className="btn small" onClick={cancelEdit}>Hủy</button>
                </div>
              </div>
            ) : (
              <div className="display-mode">
                <div className="value">{startPoint || "—"}</div>
                <button className="edit-btn" onClick={() => startEdit("start")}>✏️ Sửa</button>
              </div>
            )}
          </div>

          {/* ==================== END POINT ==================== */}
          <div className="box">
            <div className="label">Điểm đến (End)</div>
            {editingField === "end" ? (
              <div className="edit-mode">
                <input
                  type="text"
                  value={tempEnd}
                  onChange={(e) => setTempEnd(e.target.value)}
                  className="edit-input"
                  placeholder="Nhập điểm đến..."
                  autoFocus
                />
                <div className="edit-buttons">
                  <button className="btn small primary" onClick={saveEdit}>Lưu</button>
                  <button className="btn small" onClick={cancelEdit}>Hủy</button>
                </div>
              </div>
            ) : (
              <div className="display-mode">
                <div className="value">{endPoint || "—"}</div>
                <button className="edit-btn" onClick={() => startEdit("end")}>✏️ Sửa</button>
              </div>
            )}
          </div>

          {/* ==================== VEHICLE TYPE ==================== */}
          <div className="box">
            <div className="label">Loại xe</div>
            {editingField === "vehicle" ? (
              <div className="edit-mode vehicle-edit">
                <button
                  className={`vehicle-option ${tempVehicle === "motorbike" ? "selected" : ""}`}
                  onClick={() => setTempVehicle("motorbike")}
                >
                  🏍️ Xe máy
                </button>
                <button
                  className={`vehicle-option ${tempVehicle === "car" ? "selected" : ""}`}
                  onClick={() => setTempVehicle("car")}
                >
                  🚗 Ô tô
                </button>
                <div className="edit-buttons">
                  <button className="btn small primary" onClick={saveEdit}>Lưu</button>
                  <button className="btn small" onClick={cancelEdit}>Hủy</button>
                </div>
              </div>
            ) : (
              <div className="display-mode">
                <div className="vehicle">
                  {vehicleType === "car" && <span>🚗 Ô tô</span>}
                  {vehicleType === "motorbike" && <span>🏍️ Xe máy</span>}
                  {!vehicleType && <span>—</span>}
                </div>
                <button className="edit-btn" onClick={() => startEdit("vehicle")}>✏️ Chọn</button>
              </div>
            )}
          </div>
        </div>

        {needsClarification && questions.length > 0 && (
          <div className="clarify">
            <div className="label">Cần làm rõ thêm</div>
            <ul>
              {questions.map((q, i) => <li key={i}>{q}</li>)}
            </ul>
            <form onSubmit={handleClarifySubmit}>
              <input
                type="text"
                placeholder="Trả lời ở đây..."
                value={clarifyInput}
                onChange={(e) => setClarifyInput(e.target.value)}
              />
              <button type="submit" disabled={isTranscribing}>Gửi</button>
            </form>
          </div>
        )}

        <div className="confirm-row">
          <button
            className="btn primary"
            onClick={handleConfirm}
            disabled={isTranscribing || !endPoint}
          >
            Xác nhận đặt xe
          </button>
          <button className="btn" onClick={handleReject} disabled={isTranscribing}>
            Hủy
          </button>
        </div>

        {confirmation !== "pending" && (
          <div className={`confirm-state ${confirmation}`}>
            {confirmation === "confirmed" ? "✅ Đã xác nhận đặt xe" : "❌ Đã hủy"}
          </div>
        )}
      </div>
    </div>
  );
}