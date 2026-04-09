import { Audio } from 'expo-av';
import { useRef } from 'react';

const recordingRef = useRef(null);

const startRecording = async () => {
  await Audio.requestPermissionsAsync();

  const recording = new Audio.Recording();
  await recording.prepareToRecordAsync(
    Audio.RecordingOptionsPresets.HIGH_QUALITY
  );
  await recording.startAsync();

  recordingRef.current = recording;
};

const stopRecording = async () => {
  if (!recordingRef.current) return null;

  await recordingRef.current.stopAndUnloadAsync();
  const uri = recordingRef.current.getURI();

  return uri;
};

const sendAudioToBackend = async (uri) => {
  const formData = new FormData();

  formData.append("file", {
    uri,
    name: "audio.wav",
    type: "audio/wav"
  } as any); // 👈 required for React Native

  const res = await fetch("http://YOUR_IP:8000/voice-booking", {
    method: "POST",
    body: formData,
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return res.json();
};