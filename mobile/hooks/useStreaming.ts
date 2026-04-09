export function useStreaming() {
  const sendChunk = async (uri) => {
    const formData = new FormData();

    formData.append("file", {
      uri,
      name: "chunk.wav",
      type: "audio/wav"
    });

    const res = await fetch("http://localhost:8000/transcribe", {
      method: "POST",
      body: formData
    });

    return res.json();
  };

  return { sendChunk };
}