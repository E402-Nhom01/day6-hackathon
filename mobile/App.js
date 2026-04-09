import React, { useState, useEffect } from 'react';
import { StyleSheet, View, SafeAreaView, StatusBar } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

import VoiceInputArea from './components/VoiceInputArea';
import BookingForm from './components/BookingForm';
import SuccessPopup from './components/SuccessPopup';

export default function App() {
  const [appState, setAppState] = useState('IDLE'); // IDLE | RECORDING | PARSING | VALIDATING | SUCCESS
  const [partialTranscript, setPartialTranscript] = useState('');
  const [parsedData, setParsedData] = useState(null);

  // Simulated transcription over time
  useEffect(() => {
    let interval;
    if (appState === 'RECORDING') {
      const phrases = [
        "I need a ride...",
        "I need a ride from...",
        "I need a ride from Work...",
        "I need a ride from Work to...",
        "I need a ride from Work to the airport."
      ];
      let step = 0;
      
      interval = setInterval(() => {
        if (step < phrases.length) {
          setPartialTranscript(phrases[step]);
          step++;
        }
      }, 800);
    } else {
      setPartialTranscript('');
    }
    return () => clearInterval(interval);
  }, [appState]);

  // Handle stop recording and fake parsing delay
  const handleStopRecording = () => {
    setAppState('PARSING');
    
    // Simulate backend NLP processing
    setTimeout(() => {
      // Hardcoded parsed data based on the mock transcript
      setParsedData({
        from: 'Work',
        to: 'Airport',
        vehicle: null // Intentional to show empty state/fallback
      });
      setAppState('VALIDATING');
    }, 1500);
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
                onStart={() => setAppState('RECORDING')}
                onStop={handleStopRecording}
                partialTranscript={appState === 'PARSING' ? "Processing your request..." : partialTranscript}
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
