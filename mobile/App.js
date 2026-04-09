import React, { useState, useRef } from "react";
import { View, Text, Button, TextInput, StyleSheet, Alert, Platform } from "react-native";
import { Audio } from "expo-av";

export default function App() {
  const [recording, setRecording] = useState(null);
  const [transcript, setTranscript] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [vehicle, setVehicle] = useState("");
  const recordingRef = useRef(null);

  const startRecording = async () => {
    try {
      const { status } = await Audio.requestPermissionsAsync(); 
      if (status !== "granted") {
        Alert.alert("Permission required", "Microphone permission is needed to record audio.");
        return;
      }

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const rec = new Audio.Recording();
      await rec.prepareToRecordAsync(Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY);
      await rec.startAsync();

      setRecording(rec);
      recordingRef.current = rec;
    } catch (err) {
      console.error("Failed to start recording", err);
      Alert.alert("Error", "Could not start recording.");
    }
  };

  const stopRecording = async () => {
    try {
      const rec = recordingRef.current;
      if (!rec) return;

      await rec.stopAndUnloadAsync();
      const uri = rec.getURI();
      setRecording(null);

      const formData = new FormData();
      formData.append("file", {
        uri,
        name: "recording.m4a",
        type: "audio/m4a",
      });

      const response = await fetch(
        "http://172.16.29.75:3003/voice-agent?session_id=default",
        {
          method: "POST",
          body: formData,
          // Remove this header:
          // headers: { "Content-Type": "multipart/form-data" },
        }
      );

    const data = await response.json();
    console.log("Agent response:", data);

    setTranscript(data.transcript || "");
    setFrom(data.from || "");
    setTo(data.to || "");
    setVehicle(data.vehicle_type || "");
  } catch (err) {
    console.error("Stop recording error", err);
    Alert.alert("Error", "Failed to process audio.");
  }
};

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Voice Agent Debug</Text>

      <Button
        title={recording ? "Recording..." : "Start Recording"}
        onPress={startRecording}
        disabled={!!recording}
      />
      <Button
        title="Stop Recording"
        onPress={stopRecording}
        disabled={!recording}
      />

      <View style={styles.result}>
        <Text style={styles.label}>Transcript:</Text>
        <TextInput style={styles.input} value={transcript} editable={false} />

        <Text style={styles.label}>From:</Text>
        <TextInput style={styles.input} value={from} onChangeText={setFrom} />

        <Text style={styles.label}>To:</Text>
        <TextInput style={styles.input} value={to} onChangeText={setTo} />

        <Text style={styles.label}>Vehicle Type:</Text>
        <TextInput style={styles.input} value={vehicle} onChangeText={setVehicle} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, justifyContent: "flex-start" },
  label: { fontWeight: "bold", marginTop: 10 },
  input: { borderWidth: 1, borderColor: "#ccc", padding: 8, marginTop: 5, borderRadius: 5 },
  result: { marginTop: 20 },
});