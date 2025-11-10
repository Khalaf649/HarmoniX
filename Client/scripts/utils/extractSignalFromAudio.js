export async function extractSignalFromAudio(relativePath) {
  if (!relativePath) return { amplitudes: [], sampleRate: 0 };
  const response = await fetch(relativePath);
  if (!response.ok) throw new Error("Failed to fetch audio file");

  const arrayBuffer = await response.arrayBuffer();
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

  const channelData = audioBuffer.getChannelData(0);
  const sampleRate = audioBuffer.sampleRate;

  // Normalize amplitude
  // Find max amplitude safely without spread
  const maxAmp = channelData.reduce((max, v) => Math.max(max, Math.abs(v)), 0);
  const normalized = channelData.map((v) => v / maxAmp);

  return { amplitudes: normalized, sampleRate };
}
