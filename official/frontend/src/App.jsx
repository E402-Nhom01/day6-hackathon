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
  const [vehicleType, setVehicleType] = useState("");

  const [resolvedStart, setResolvedStart] = useState(null);
  const [resolvedEnd, setResolvedEnd] = useState(null);

  const [needsClarification, setNeedsClarification] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [clarifyInput, setClarifyInput] = useState("");
  const [confirmation, setConfirmation] = useState("pending");
  const [error, setError] = useState("");

  // Generate or reuse session ID
  function ensureSessionId() {
    if (sessionId) return sessionId;
    const newId = crypto.randomUUID();
    setSessionId(newId);
    return newId;
  }

  // Get current GPS location
  async function getCurrentLocation() {
    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        resolve({ lat: null, lng: null });
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => resolve({ lat: null, lng: null }),
        { enableHighAccuracy: true, timeout: 5000 }
      );
    });
  }

  async function startRecording() {
    setError("");
    setTranscript("");
    setCorrectedText("");
    setStartPoint("");
    setEndPoint("");
    setVehicleType("");
    setResolvedStart(null);
    setResolvedEnd(null);
    setNeedsClarification(false);
    setQuestions([]);
    setClarifyInput("");
    setConfirmation("pending");

    const newSessionId = ensureSessionId();

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
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

  // Main function: Transcribe → Parse
  async function handleTranscribeAndParse(audioBlob, activeSessionId) {
    setIsTranscribing(true);
    setError("");

    try {
      // 1. Transcribe
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");

      const transcribeRes = await fetch("/transcribe", {
        method: "POST",
        body: formData,
      });

      if (!transcribeRes.ok) throw new Error("Transcription failed");

      const transcribeData = await transcribeRes.json();
      const text = transcribeData.text || "";
      setTranscript(text);

      // 2. Parse
      await sendParse(text, activeSessionId);
    } catch (err) {
      setError(err.message || "Processing failed. Please try again.");
    } finally {
      setIsTranscribing(false);
    }
  }

  // Send text to /parse endpoint
  async function sendParse(text, activeSessionId) {
    try {
      const location = await getCurrentLocation(); // ✅ ADD THIS

      const res = await fetch("/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text,
          session_id: activeSessionId,
          user_lat: location.lat,   // ✅ SEND GPS
          user_lng: location.lng,
        }),
      });

      if (!res.ok) throw new Error("Parse request failed");

      const data = await res.json();

      setCorrectedText(data.corrected_text || "");
      setStartPoint(data.start_point || "");
      setEndPoint(data.end_point || "");
      setVehicleType(data.vehicle_type || "");

      setResolvedStart(data.resolved_start || null);
      setResolvedEnd(data.resolved_end || null);

      setNeedsClarification(Boolean(data.needs_clarification));
      setQuestions(data.questions || []);

      if (data.ready_to_book) {
        setConfirmation("confirmed");
      }

    } catch (err) {
      setError("Failed to understand your request. Please try again.");
      console.error(err);
    }
  }

  async function handleClarifySubmit(e) {
    e.preventDefault();
    if (!clarifyInput.trim()) return;

    setIsTranscribing(true);
    setError("");
    try {
      const activeSessionId = ensureSessionId();
      await sendParse(clarifyInput.trim(), activeSessionId);
      setClarifyInput("");
    } catch (err) {
      setError("Failed to process clarification.");
    } finally {
      setIsTranscribing(false);
    }
  }

  function handleConfirm() {
    setConfirmation("confirmed");
    alert("Booking confirmed! (This is a demo)");
  }

  function handleReject() {
    setConfirmation("rejected");
    alert("Booking cancelled.");
  }

  return (
    <div className="app">
      <div className="card">
        <h1>🛵 XanhSM Voice Booking</h1>
        <p className="subtitle">Nói tự nhiên, chúng tôi sẽ hiểu và điền thông tin cho bạn</p>

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
          <div className="box">
            <div className="label">Điểm đón (Start)</div>
            <div className="value">{startPoint || "—"}</div>
            {resolvedStart?.full_address && (
              <div className="sub">{resolvedStart.full_address}</div>
            )}
          </div>

          <div className="box">
            <div className="label">Điểm đến (End)</div>
            <div className="value">{endPoint || "—"}</div>
            {resolvedEnd?.full_address && (
              <div className="sub">{resolvedEnd.full_address}</div>
            )}
          </div>

          <div className="box">
            <div className="label">Loại xe</div>
            <div className="vehicle">
              {vehicleType === "car" && <span>🚗 Ô tô</span>}
              {vehicleType === "motorbike" && <span>🏍️ Xe máy</span>}
              {!vehicleType && <span>—</span>}
            </div>
          </div>
        </div>

        {needsClarification && questions.length > 0 && (
          <div className="clarify">
            <div className="label">Cần làm rõ thêm</div>
            <ul>
              {questions.map((q, i) => (
                <li key={i}>{q}</li>
              ))}
            </ul>
            <form onSubmit={handleClarifySubmit}>
              <input
                type="text"
                placeholder="Trả lời ở đây..."
                value={clarifyInput}
                onChange={(e) => setClarifyInput(e.target.value)}
              />
              <button type="submit" disabled={isTranscribing}>
                Gửi
              </button>
            </form>
          </div>
        )}

        <div className="confirm-row">
          <button className="btn primary" onClick={handleConfirm} disabled={isTranscribing || !endPoint}>
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