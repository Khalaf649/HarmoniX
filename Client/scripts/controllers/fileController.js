import { appState } from "../appState.js";
import { extractSignalFromAudio } from "../utils/extractSignalFromAudio.js";
import { SignalViewer } from "./SignalViewer.js";

export async function handleJsonUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  const fileLabel = document.querySelector(".header-file-label");
  const fileNameDisplay = document.querySelector(".header-file-name");
  const uploaderCard = document.getElementById("uploaderCard");
  const mainApp = document.getElementById("mainApp");

  // Validate JSON file
  if (file.type !== "application/json" && !file.name.endsWith(".json")) {
    alert("❌ Please upload a valid JSON file.");
    return;
  }

  const reader = new FileReader();
  reader.onload = async function (e) {
    try {
      const jsonData = JSON.parse(e.target.result);
      console.log(jsonData);
      fileLabel.textContent = "Loaded File:";
      fileNameDisplay.textContent = file.name;

      // Save JSON in state
      appState.originalJson = jsonData;
      appState.renderedJson = JSON.parse(JSON.stringify(jsonData));

      // Hide uploader card
      uploaderCard.style.display = "none";

      const mode = appState.mode;

      // 1️⃣ Load input signal

      const input = await extractSignalFromAudio(
        appState.renderedJson.original_signal
      );
      console.log(input.amplitudes);
      console.log(input.time);
      appState.inputViewer = new SignalViewer({
        containerId: "input-signal-viewer",
        title: "Input Signal",
        samples: input.amplitudes,
        time: input.time,
        audioSrc: appState.renderedJson.original_signal,
        color: "var(--color-waveform-input)",
      });

      // 2️⃣ Load output signal for current mode
      const outputPath = jsonData[mode].output_signal;

      const output = await extractSignalFromAudio(outputPath);
      appState.outputViewer = new SignalViewer({
        containerId: "output-signal-viewer",
        title: "Output Signal",
        samples: output.amplitudes,
        time: output.time,
        audioSrc: outputPath,
        color: "var(--color-waveform-output)",
      });

      // // 4️⃣ Show main app
      mainApp.style.display = "grid";

      console.log("✅ appState populated:", appState);
    } catch (err) {
      console.error("Error parsing JSON or loading audio:", err);
      alert("❌ Failed to load JSON or audio files.");
    }
  };

  reader.readAsText(file);
}

// Attach event listener
const fileInput = document.getElementById("jsonFile");
fileInput.addEventListener("change", handleJsonUpload);
