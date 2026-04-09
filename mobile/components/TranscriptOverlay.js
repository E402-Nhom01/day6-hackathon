import { View, Text } from "react-native";

export default function TranscriptOverlay({ text }) {
  if (!text) return null;

  return (
    <View style={{
      position: "absolute",
      bottom: 120,
      left: 20,
      right: 20,
      backgroundColor: "black",
      padding: 12,
      borderRadius: 12
    }}>
      <Text style={{ color: "white" }}>{text}</Text>
    </View>
  );
}