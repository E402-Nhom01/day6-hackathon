import { useEffect } from "react";
import { useAudioRecorder } from "../hooks/useAudioRecorder";
import { useStreaming } from "../hooks/useStreaming";
import { useVoiceStore } from "../store/useVoiceStore";

export default function VoiceRecorder() {
  const { start } = useAudioRecorder();
  const { sendChunk } = useStreaming();
  const setTranscript = useVoiceStore(s => s.setTranscript);

  useEffect(() => {
    start();

    const interval = setInterval(async () => {
      const uri = await stop(); // stop current chunk
      const res = await sendChunk(uri);

      setTranscript(res.text);

      await start(); // restart recording
    }, 1500);

    return () => clearInterval(interval);
  }, []);

  return null;
}