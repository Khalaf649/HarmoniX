import { appState } from "../appState.js";

export async function saveEQToServer(samples) {
  console.log("Saving EQ to server with mode:", appState.mode);
  console.log(samples);
  console.log("Sample Rate:", appState.inputViewer.sampleRate);
  const response = await fetch("http://localhost:8000/saveEQ", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      samples: Array.from(samples),
      sampleRate: appState.inputViewer.sampleRate,
      mode: appState.mode,
    }),
  });
  console.log("Server response:", response);

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
