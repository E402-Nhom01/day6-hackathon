import { Audio } from 'expo-av';

export function useAudioRecorder() {
  let recording = null;

  const start = async () => {
    await Audio.requestPermissionsAsync();

    recording = new Audio.Recording();
    await recording.prepareToRecordAsync(
      Audio.RecordingOptionsPresets.HIGH_QUALITY
    );
    await recording.startAsync();
  };

  const stop = async () => {
    await recording.stopAndUnloadAsync();
    return recording.getURI();
  };

  return { start, stop };
}