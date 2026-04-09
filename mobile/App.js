import React, { useState, useEffect } from "react";
import { StyleSheet, SafeAreaView, View, Button, Text, ScrollView, ActivityIndicator, TextInput, Alert } from "react-native";
import { Audio } from "expo-av";

export default function App() {
  const [recording, setRecording] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [chatHistory, setChatHistory] = useState([]); // array of {type:'user'|'sm', text:string}
  const [isProcessing, setIsProcessing] = useState(false);
  const [whisperText, setWhisperText] = useState(""); // intermediate text
  const [userConfirmed, setUserConfirmed] = useState(""); // text confirmed to send to agent

  const WHISPER_URL = "http://localhost:3002/transcribe";
  const AGENT_URL = "http://localhost:3003/text-agent?session_id=default";

  useEffect(() => {
    (async () => {
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== "granted") {
        Alert.alert("Microphone permission required", "This app needs access to your mic.");
      }
    })();
  }, []);

  const startRecording = async () => {
    setIsRecording(true);
    const { recording } = await Audio.Recording.createAsync(Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY);
    setRecording(recording);
    setWhisperText("");
  };

  const stopRecording = async () => {
    if (!recording) return;

    setIsRecording(false);
    setIsProcessing(true);

    try {
      // Stop recording
      await recording.stopAndUnloadAsync();
      const blobUri = recording.getURI();

      // Convert URI to blob
      const blobResponse = await fetch(blobUri);
      const blob = await blobResponse.blob();

      const formData = new FormData();
      formData.append("file", new File([blob], "recording.m4a", { type: blob.type }));

      // Send to voice-agent
      const res = await fetch("http://localhost:3003/voice-agent?session_id=default", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      // Display Whisper transcript first
      const whisperText = data.transcript || "(Không nhận diện được giọng nói)";
      setChatHistory(prev => [...prev, { type: "whisper", text: whisperText }]);

      // Display Agent response next
      const agentReply = data.agent_reply || "(Agent chưa trả lời)";
      setChatHistory(prev => [...prev, { type: "sm", text: agentReply }]);

      // Optional: log booking info for debug
      if (data.booking_status) {
        console.log("Booking API result:", data.booking_status);
      }

    } catch (err) {
      console.log("Error processing audio:", err);
      setChatHistory(prev => [
        ...prev,
        { type: "sm", text: "(Lỗi nhận diện audio hoặc agent)" },
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  const sendToAgent = async () => {
    if (!userConfirmed) return;

    setChatHistory(prev => [...prev, { type: "user", text: userConfirmed }]);
    setUserConfirmed(""); // reset input

    setIsProcessing(true);
    try {
      const res = await fetch(AGENT_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userConfirmed }),
      });
      const data = await res.json();
      const agentReply = data.message || "(Agent không trả lời)";
      setChatHistory(prev => [...prev, { type: "sm", text: agentReply }]);
    } catch (err) {
      console.log("Agent error:", err);
      setChatHistory(prev => [...prev, { type: "sm", text: "(Lỗi kết nối Agent)" }]);
    } finally {
      setIsProcessing(false);
      setWhisperText(""); // clear after sending
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.inner}>
        <Text style={styles.title}>Xanh SM Buddy Chat</Text>

        <View style={{ flexDirection: "row", marginBottom: 10 }}>
          <Button title={isRecording ? "Recording..." : "Start Recording"} onPress={startRecording} disabled={isRecording} />
          <View style={{ width: 10 }} />
          <Button title="Stop Recording" onPress={stopRecording} disabled={!isRecording} />
        </View>

        {isProcessing && <ActivityIndicator style={{ marginBottom: 10 }} />}

        {whisperText ? (
          <View style={{ marginVertical: 10 }}>
            <Text>Whisper heard:</Text>
            <TextInput
              style={styles.textInput}
              value={userConfirmed}
              onChangeText={setUserConfirmed}
              placeholder="Edit before sending..."
            />
            <Button title="Send to SM Buddy" onPress={sendToAgent} disabled={!userConfirmed} />
          </View>
        ) : null}

        <View style={styles.chatContainer}>
          {chatHistory.map((msg, idx) => (
            <View
              key={idx}
              style={[
                styles.chatBubble,
                msg.type === "user"
                  ? styles.userBubble
                  : msg.type === "whisper"
                  ? styles.whisperBubble
                  : styles.smBubble,
              ]}
            >
              <Text style={styles.chatText}>{msg.text}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f5f5" },
  inner: { padding: 20, flexGrow: 1 },
  title: { fontSize: 24, fontWeight: "bold", marginBottom: 20, textAlign: "center" },
  chatContainer: { flex: 1, marginTop: 10 },
  chatBubble: { padding: 10, marginBottom: 8, borderRadius: 8, maxWidth: "80%" },
  userBubble: { backgroundColor: "#cce5ff", alignSelf: "flex-end" },
  whisperBubble: { backgroundColor: "#99ddff", alignSelf: "flex-end" },
  smBubble: { backgroundColor: "#e2e2e2", alignSelf: "flex-start" },
  chatText: { fontSize: 16, color: "#222" },
});