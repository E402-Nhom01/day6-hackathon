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