export function useSilenceDetection(onStop) {
  let lastAudio = Date.now();

  const update = () => {
    lastAudio = Date.now();
  };

  setInterval(() => {
    if (Date.now() - lastAudio > 2000) {
      onStop();
    }
  }, 500);

  return { update };
}