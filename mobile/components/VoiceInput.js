import { Pressable, Text } from "react-native";

export default function VoiceInput({ isRecording, onStart, onStop }) {
  return (
    <Pressable
      onPress={isRecording ? onStop : onStart}
      style={{
        backgroundColor: isRecording ? "#ef4444" : "#111827",
        padding: 16,
        borderRadius: 50,
        alignItems: "center",
        marginBottom: 20
      }}
    >
      <Text style={{ color: "#fff", fontWeight: "600" }}>
        {isRecording ? "Stop" : "🎙️ Speak"}
      </Text>
    </Pressable>
  );
}