import React, { useState, useEffect } from 'react';
import { StyleSheet, View, SafeAreaView, Button, Text, Alert, ActivityIndicator, Platform } from 'react-native';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';

export default function App() {
  const [recording, setRecording] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [localUri, setLocalUri] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  // Whisper server URL
  const WHISPER_URL = 'http://172.16.29.75:5050/transcribe';

  useEffect(() => {
    async function requestPermission() {
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Microphone permission required', 'This app needs access to your microphone to record audio.');
      }
    }
    requestPermission();
  }, []);

  const startRecording = async () => {
    try {
      setIsRecording(true);
      setTranscript('');
      setLocalUri(null);
      const { recording } = await Audio.Recording.createAsync(Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY);
      setRecording(recording);
    } catch (err) {
      console.log('Error starting recording', err);
      setIsRecording(false);
    }
  };

  const stopRecording = async () => {
    try {
      setIsRecording(false);
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      console.log('Recording URI:', uri);

      setRecording(null);

      if (Platform.OS === 'web') {
        // Web: send blob directly
        transcribeAudioWeb(uri);
      } else {
        // Mobile: copy to FileSystem first
        const fileUri = FileSystem.cacheDirectory + 'recording.m4a';
        await FileSystem.copyAsync({ from: uri, to: fileUri });
        setLocalUri(fileUri);
        playRecording(fileUri);
        transcribeAudioMobile(fileUri);
      }
    } catch (err) {
      console.log('Error stopping recording', err);
    }
  };

  const playRecording = async (uri) => {
    try {
      const sound = new Audio.Sound();
      await sound.loadAsync({ uri });
      await sound.playAsync();
    } catch (err) {
      console.log('Error playing audio', err);
    }
  };

  // Mobile transcription
  const transcribeAudioMobile = async (uri) => {
    try {
      setIsProcessing(true);
      const formData = new FormData();
      formData.append('file', {
        uri,
        name: 'recording.m4a',
        type: 'audio/m4a',
      });

      const res = await fetch(WHISPER_URL, {
        method: 'POST',
        body: formData,
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const data = await res.json();
      setTranscript(data.transcript || 'No transcript returned');
    } catch (err) {
      console.log('Error transcribing audio (mobile)', err);
      setTranscript('Error transcribing audio');
    } finally {
      setIsProcessing(false);
    }
  };

  // Web transcription
  const transcribeAudioWeb = async (blobUri) => {
    try {
      setIsProcessing(true);
      const response = await fetch(blobUri);
      const blob = await response.blob();

      const formData = new FormData();
      formData.append('file', new File([blob], 'recording.webm', { type: blob.type }));

      const res = await fetch(WHISPER_URL, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      setTranscript(data.transcript || 'No transcript returned');
    } catch (err) {
      console.log('Error transcribing audio (web)', err);
      setTranscript('Error transcribing audio');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.inner}>
        <Text style={styles.title}>Mic + Whisper Transcription</Text>

        <Button title={isRecording ? 'Recording...' : 'Start Recording'} onPress={startRecording} disabled={isRecording} />

        <View style={{ height: 10 }} />

        <Button title="Stop Recording & Transcribe" onPress={stopRecording} disabled={!isRecording} />

        {localUri && <Text style={styles.uri}>Saved file: {localUri}</Text>}

        {isProcessing && <ActivityIndicator style={{ marginTop: 10 }} />}
        {transcript ? <Text style={styles.transcript}>Transcript: {transcript}</Text> : null}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', backgroundColor: '#f5f5f5' },
  inner: { padding: 20 },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 20, textAlign: 'center' },
  uri: { marginTop: 20, fontSize: 12, color: '#555' },
  transcript: { marginTop: 20, fontSize: 16, color: '#222' },
});