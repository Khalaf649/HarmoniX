export async function extractSignalFromAudio(relativePath) {
  // Fetch audio file
  const response = await fetch(relativePath);
  if (!response.ok) throw new Error("Failed to fetch audio file");

  const arrayBuffer = await response.arrayBuffer();

  // Create AudioContext
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();

  // Decode audio safely using Promise wrapper
  const audioBuffer = await new Promise((resolve, reject) => {
    audioContext.decodeAudioData(
      arrayBuffer,
      (buffer) => resolve(buffer),
      (err) => reject(err)
    );
  });

  // Take first channel
  const channelData = audioBuffer.getChannelData(0);
  const sampleRate = audioBuffer.sampleRate;

  // Create time array
  const timeArray = new Float32Array(channelData.length);
  for (let i = 0; i < channelData.length; i++) {
    timeArray[i] = i / sampleRate;
  }

  return {
    time: Array.from(timeArray),
    amplitudes: Array.from(channelData),
  };
}
