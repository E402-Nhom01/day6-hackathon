import React, { useState, useEffect } from 'react';
import { StyleSheet, View, SafeAreaView, StatusBar } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import useVoice from './hooks/useVoice';
import VoiceInputArea from './components/VoiceInputArea';
import BookingForm from './components/BookingForm';
import SuccessPopup from './components/SuccessPopup';

export default function App() {
  const [appState, setAppState] = useState('IDLE'); // IDLE | RECORDING | PARSING | VALIDATING | SUCCESS
  const [partialTranscript, setPartialTranscript] = useState('');
  const [parsedData, setParsedData] = useState(null);

  const {
    transcript,
    setTranscript,
    startRecording,
    stopRecording,
    transcribe
  } = useVoice();


  const handleStopRecording = async () => {
    setAppState('PARSING');

    const uri = await stopRecording();

    if (!uri) return;

    try {
      const data = await transcribe(uri);

      setParsedData({
        from: data.booking.pickup_location,
        to: data.booking.dropoff_location,
        vehicle: data.booking.vehicle_type
      });

      setAppState('VALIDATING');
    } catch (e) {
      console.error(e);
      setAppState('IDLE');
    }
  };
  const handleCreateBooking = (data) => {
    // In a real app, send data to backend here
    setAppState('SUCCESS');
  };

  const handleReset = () => {
    setAppState('IDLE');
    setParsedData(null);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
      <LinearGradient
        colors={['#ffffff', '#f3f4f6']}
        style={styles.container}
      >
        <View style={styles.content}>
          
          {(appState === 'IDLE' || appState === 'RECORDING' || appState === 'PARSING') && (
            <View style={styles.voiceSection}>
              <VoiceInputArea 
                title="Where to?"
                isRecording={appState === 'RECORDING'}
                onStart={async () => {
                  setAppState('RECORDING');
                  await startRecording();
                }}
                onStop={handleStopRecording}
                partialTranscript={
                  appState === 'PARSING'
                    ? "Processing your request..."
                    : transcript
}
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

        {appState === 'SUCCESS' && (
          <SuccessPopup onReset={handleReset} />
        )}

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
  }
});
