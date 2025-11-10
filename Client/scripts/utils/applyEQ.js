import { appState } from "../appState.js";

export async function applyEQ() {
  if (!appState.inputViewer || !appState.renderedJson) {
    throw new Error("Input signal or appState not initialized");
  }

  const samples = appState.inputViewer.samples;
  const fs = appState.inputViewer.sampleRate;
  const sliders = appState.renderedJson[appState.mode]?.sliders || [];

  const response = await fetch("http://localhost:8080/applyEqualizer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ samples, fs, sliders }),
  });
  console.log(response);

  if (!response.ok) {
    const text = await response.text();
    let err = {};
    try {
      err = JSON.parse(text);
    } catch {}
    throw new Error(err.error || text || "Failed to apply EQ");
  }

  const result = await response.json();
  return result.samples;
}
