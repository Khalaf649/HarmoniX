import { appState } from "../appState.js";

export async function saveEQToServer(samples, sampleRate) {
  const response = await fetch("http://localhost:8000/saveEQ", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      samples: Array.from(samples),
      sampleRate: sampleRate || appState.inputViewer.sampleRate,
      mode: appState.mode,
    }),
  });

  if (!response.ok) {
    const text = await response.text();
    let err = {};
    try {
      err = JSON.parse(text);
    } catch {}
    throw new Error(
      err.detail || err.error || text || "Failed to save EQ result"
    );
  }

  const result = await response.json();
  return result.url; // This is "/{mode}_output.wav"
}
