/**
 * Convert an array of samples into a playable Audio object
 * @param {Float32Array|number[]} samples - amplitudes in [-1,1]
 * @param {number} sampleRate - sample rate of the audio
 * @returns {HTMLAudioElement} - ready-to-play Audio
 */
export function samplesToAudio(samples, sampleRate) {
  const bufferLength = samples.length;
  const wavBuffer = new ArrayBuffer(44 + bufferLength * 2);
  const view = new DataView(wavBuffer);

  // Helpers
  const writeString = (view, offset, str) => {
    for (let i = 0; i < str.length; i++)
      view.setUint8(offset + i, str.charCodeAt(i));
  };
  const write16 = (view, offset, val) => view.setInt16(offset, val, true);
  const write32 = (view, offset, val) => view.setUint32(offset, val, true);

  // WAV header
  writeString(view, 0, "RIFF");
  write32(view, 4, 36 + bufferLength * 2);
  writeString(view, 8, "WAVE");
  writeString(view, 12, "fmt ");
  write32(view, 16, 16);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // Mono
  write32(view, 24, sampleRate);
  write32(view, 28, sampleRate * 2);
  view.setUint16(32, 2, true); // Block align
  view.setUint16(34, 16, true); // Bits per sample
  writeString(view, 36, "data");
  write32(view, 40, bufferLength * 2);

  // Samples
  let offset = 44;
  for (let i = 0; i < bufferLength; i++) {
    let s = Math.max(-1, Math.min(1, samples[i]));
    write16(view, offset, s < 0 ? s * 0x8000 : s * 0x7fff);
    offset += 2;
  }

  const blob = new Blob([view], { type: "audio/wav" });
  return new Audio(URL.createObjectURL(blob));
}
