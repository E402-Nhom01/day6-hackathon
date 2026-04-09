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
  const [needsClarification, setNeedsClarification] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [clarifyInput, setClarifyInput] = useState("");
  const [confirmation, setConfirmation] = useState("pending");
  const [error, setError] = useState("");

  function ensureSessionId() {
    if (sessionId) return sessionId;
    const newSessionId = crypto.randomUUID();
    setSessionId(newSessionId);
    return newSessionId;
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

    const newSessionId = ensureSessionId();

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream);
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        await handleTranscribeAndParse(audioBlob, newSessionId);
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
    } catch (err) {
      setError("Microphone access denied or unavailable.");
    }
  }

  function stopRecording() {
    setError("");
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
    }
    setIsRecording(false);
  }

  async function handleTranscribeAndParse(audioBlob, activeSessionId) {
    setIsTranscribing(true);
    try {
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");

      const transcribeRes = await fetch("/transcribe", {
        method: "POST",
        body: formData,
      });

      if (!transcribeRes.ok) {
        throw new Error("Transcription failed.");
      }

      const transcribeData = await transcribeRes.json();
      const text = transcribeData.text || "";
      setTranscript(text);

      await sendParse(text, activeSessionId);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setIsTranscribing(false);
    }
  }

  async function sendParse(text, activeSessionId) {
    const parseRes = await fetch("/parse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, session_id: activeSessionId }),
    });

    if (!parseRes.ok) {
      throw new Error("Parsing failed.");
    }

    const parseData = await parseRes.json();
    setCorrectedText(parseData.corrected_text || "");
    setStartPoint(parseData.start_point || "");
    setEndPoint(parseData.end_point || "");
    setVehicleType(parseData.vehicle_type || "");
    setNeedsClarification(Boolean(parseData.needs_clarification));
    setQuestions(parseData.questions || []);
  }

  async function handleClarifySubmit(event) {
    event.preventDefault();
    if (!clarifyInput.trim()) return;
    setIsTranscribing(true);
    setError("");
    try {
      const activeSessionId = ensureSessionId();
      await sendParse(clarifyInput.trim(), activeSessionId);
      setClarifyInput("");
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setIsTranscribing(false);
    }
  }

  function handleConfirm() {
    setConfirmation("confirmed");
  }

  function handleReject() {
    setConfirmation("rejected");
  }

  return (
    <div className="app">
      <div className="card">
        <h1>Voice Ride Booking</h1>
        <p className="subtitle">
          Record your request and we will extract the start, end, and vehicle.
        </p>

        <div className="controls">
          <button
            className="btn primary"
            onClick={startRecording}
            disabled={isRecording || isTranscribing}
          >
            Start Recording
          </button>
          <button
            className="btn"
            onClick={stopRecording}
            disabled={!isRecording}
          >
            Stop Recording
          </button>
        </div>

        {isTranscribing && <div className="status">Processing...</div>}
        {error && <div className="error">{error}</div>}

        <div className="transcript">
          <div className="label">Transcript</div>
          <div className="value">{transcript || "—"}</div>
        </div>

        <div className="transcript">
          <div className="label">Corrected</div>
          <div className="value">{correctedText || "—"}</div>
        </div>

        <div className="grid">
          <div className="box">
            <div className="label">Start</div>
            <div className="value">{startPoint || "—"}</div>
          </div>
          <div className="box">
            <div className="label">End</div>
            <div className="value">{endPoint || "—"}</div>
          </div>
          <div className="box">
            <div className="label">Vehicle</div>
            <div className="vehicle">
              {vehicleType === "car" && (
                <>
                  <svg viewBox="0 0 64 32" className="vehicle-icon" aria-hidden="true">
                    <rect x="6" y="10" width="52" height="12" rx="4" />
                    <rect x="16" y="4" width="20" height="8" rx="2" />
                    <circle cx="18" cy="26" r="4" />
                    <circle cx="46" cy="26" r="4" />
                  </svg>
                  <span>Car</span>
                </>
              )}
              {vehicleType === "motorbike" && (
                <>
                  <svg viewBox="0 0 64 32" className="vehicle-icon" aria-hidden="true">
                    <circle cx="16" cy="24" r="6" />
                    <circle cx="48" cy="24" r="6" />
                    <path d="M16 24 L26 18 L36 18 L44 24" fill="none" stroke="currentColor" strokeWidth="3" />
                    <path d="M30 10 L36 18" fill="none" stroke="currentColor" strokeWidth="3" />
                  </svg>
                  <span>Motorbike</span>
                </>
              )}
              {!vehicleType && <span>—</span>}
            </div>
          </div>
        </div>

        {needsClarification && questions.length > 0 && (
          <div className="clarify">
            <div className="label">Need Clarification</div>
            <ul>
              {questions.map((q, idx) => (
                <li key={idx}>{q}</li>
              ))}
            </ul>
            <form className="clarify-form" onSubmit={handleClarifySubmit}>
              <input
                className="clarify-input"
                type="text"
                placeholder="Nhập câu trả lời của bạn..."
                value={clarifyInput}
                onChange={(e) => setClarifyInput(e.target.value)}
              />
              <button className="btn primary" type="submit" disabled={isTranscribing}>
                Send
              </button>
            </form>
          </div>
        )}

        <div className="confirm-row">
          <button
            className="btn primary"
            onClick={handleConfirm}
            disabled={isTranscribing}
          >
            Confirm
          </button>
          <button className="btn" onClick={handleReject} disabled={isTranscribing}>
            Reject
          </button>
          {confirmation !== "pending" && (
            <div className="confirm-state">
              {confirmation === "confirmed" ? "Confirmed" : "Rejected"}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
