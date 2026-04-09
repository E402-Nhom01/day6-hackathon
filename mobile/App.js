import React, { useState } from 'react';
import { StyleSheet, View, SafeAreaView, StatusBar } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

import VoiceInputArea from './components/VoiceInputArea';
import BookingForm from './components/BookingForm';
import SuccessPopup from './components/SuccessPopup';
import useVoice from './hooks/useVoice';

export default function App() {
  const [appState, setAppState] = useState('IDLE'); // IDLE | RECORDING | PARSING | VALIDATING | SUCCESS
  const [lastTranscript, setLastTranscript] = useState('');
  const [parsedData, setParsedData] = useState(null);

  const { isRecording, isProcessing, error, startRecording, stopRecording } = useVoice();

  const handleStartRecording = async () => {
    setParsedData(null);
    setLastTranscript('');
    setAppState('RECORDING');
    try {
      await startRecording();
    } catch (err) {
      setAppState('IDLE');
    }
  };

  const handleStopRecording = async () => {
    setAppState('PARSING');
    const result = await stopRecording();

    if (result?.transcript) {
      setLastTranscript(result.transcript);
    }

    if (result?.parsedData) {
      setParsedData(result.parsedData);
      setAppState('VALIDATING');
      return;
    }

    setAppState('IDLE');
  };

  const handleCreateBooking = () => {
    setAppState('SUCCESS');
  };

  const handleReset = () => {
    setAppState('IDLE');
    setParsedData(null);
    setLastTranscript('');
  };

  const transcriptText = error
    ? error
    : appState === 'PARSING' || isProcessing
    ? 'Processing your request...'
    : lastTranscript;

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
      <LinearGradient colors={['#ffffff', '#f3f4f6']} style={styles.container}>
        <View style={styles.content}>
          {(appState === 'IDLE' || appState === 'RECORDING' || appState === 'PARSING') && (
            <View style={styles.voiceSection}>
              <VoiceInputArea
                title="Where to?"
                isRecording={isRecording || appState === 'RECORDING'}
                onStart={handleStartRecording}
                onStop={handleStopRecording}
                partialTranscript={transcriptText}
              />
            </View>
          )}

          {appState === 'VALIDATING' && parsedData && (
            <BookingForm
              parsedData={parsedData}
              onConfirm={handleCreateBooking}
              onCancel={handleReset}
            />
          )}
        </View>

        {appState === 'SUCCESS' && <SuccessPopup onReset={handleReset} />}
      </LinearGradient>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    paddingTop: 20,
  },
  voiceSection: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
});
