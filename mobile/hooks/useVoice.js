import { Audio } from 'expo-av';
import { useCallback, useRef, useState } from 'react';

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://YOUR_IP:8000';

const MIME_BY_EXT = {
  wav: 'audio/wav',
  mp3: 'audio/mpeg',
  m4a: 'audio/m4a',
  aac: 'audio/aac',
  caf: 'audio/x-caf',
  ogg: 'audio/ogg',
  opus: 'audio/opus',
  flac: 'audio/flac',
  m4b: 'audio/m4b',
  '3gp': 'audio/3gpp',
};

const getFileMeta = (uri) => {
  const parts = uri.split('.');
  const ext = parts.length > 1 ? parts[parts.length - 1].toLowerCase() : 'm4a';
  const type = MIME_BY_EXT[ext] || 'audio/m4a';
  return {
    name: `audio.${ext}`,
    type,
  };
};

export default function useVoice() {
  const recordingRef = useRef(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);

  const startRecording = useCallback(async () => {
    setError(null);
    await Audio.requestPermissionsAsync();

    await Audio.setAudioModeAsync({
      allowsRecordingIOS: true,
      playsInSilentModeIOS: true,
    });

    const recording = new Audio.Recording();
    await recording.prepareToRecordAsync(
      Audio.RecordingOptionsPresets.HIGH_QUALITY
    );
    await recording.startAsync();

    recordingRef.current = recording;
    setIsRecording(true);
  }, []);

  const sendAudioToBackend = useCallback(async (uri) => {
    const formData = new FormData();
    const meta = getFileMeta(uri);

    formData.append('file', {
      uri,
      name: meta.name,
      type: meta.type,
    });

    const res = await fetch(`${API_BASE_URL}/voice-booking`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || 'Failed to transcribe audio');
    }

    return res.json();
  }, []);

  const stopRecording = useCallback(async () => {
    if (!recordingRef.current) return null;

    setIsProcessing(true);
    setError(null);

    try {
      await recordingRef.current.stopAndUnloadAsync();
      const uri = recordingRef.current.getURI();
      recordingRef.current = null;
      setIsRecording(false);

      if (!uri) throw new Error('No audio URI returned');

      const result = await sendAudioToBackend(uri);
      return result;
    } catch (err) {
      setError(err?.message || 'Voice processing failed');
      return null;
    } finally {
      setIsProcessing(false);
    }
  }, [sendAudioToBackend]);

  return {
    isRecording,
    isProcessing,
    error,
    startRecording,
    stopRecording,
  };
}
