import { appState } from "../appState.js";

// New: send the audio file (blob) + sliders as multipart/form-data
export async function ApplyAi(fileUrl, sliders) {
  try {
    const endpoint = appState.mode === "musical" ? "MusicAi" : "HumanAi";

    // Fetch the file (from a public path like `public/...`) as a Blob
    const resp = await fetch(fileUrl);
    if (!resp.ok) throw new Error(`Failed to fetch file: ${resp.statusText}`);
    const blob = await resp.blob();

    const fd = new FormData();
    // Attempt to derive a filename from the URL
    const urlParts = fileUrl.split("/");
    const filename = urlParts[urlParts.length - 1] || "input.wav";
    fd.append("file", blob, filename);
    fd.append("sliders", JSON.stringify(sliders || []));
    console.log("Sending to AI API:", endpoint, fd);

    const response = await fetch(`http://localhost:8000/${endpoint}`, {
      method: "POST",
      body: fd,
    });

    if (!response.ok) {
      throw new Error(`AI API Error: ${response.statusText}`);
    }

    const data = await response.json();
    console.log("AI API response:", data);

    return {
      samples: new Float32Array(data.samples || []),
      frequencies: data.frequencies || [],
      magnitudes: data.magnitudes || [],
      sampleRate: data.sampleRate || 44100,
    };
  } catch (err) {
    console.error("Failed to call AI API:", err);
    throw new Error("Failed to process audio with AI: " + err.message);
  }
}
