export class SignalViewer {
  constructor({
    containerId,
    samples = [],
    time = [],
    audioSrc = null,
    color = "lime",
  }) {
    this.container = document.getElementById(containerId);
    if (!this.container) throw new Error(`Container ${containerId} not found`);

    this.canvas = this.container.querySelector(".signal-viewer-canvas");
    this.ctx = this.canvas.getContext("2d");

    // Child controls
    this.playBtn = this.container.querySelector(".play-btn");
    this.stopBtn = this.container.querySelector(".stop-btn");
    this.resetBtn = this.container.querySelector(".reset-btn");
    this.muteBtn = this.container.querySelector(".mute-toggle-btn");
    this.speedSlider = this.container.querySelector(".speed-slider");
    this.speedLabel = this.container.querySelector(".speed-label");
    this.zoomInBtn = this.container.querySelector(".zoom-in");
    this.zoomOutBtn = this.container.querySelector(".zoom-out");
    this.zoomLabel = this.container.querySelector(".zoom-label");

    // Signal & audio
    this.samples = samples;
    this.time = time;
    this.audio = audioSrc ? new Audio(audioSrc) : null;
    this.color = color;

    this.isPlaying = false;
    this.isMuted = false;
    this.speed = 1;
    this.zoom = 1;
    this.offset = 0;

    this.updateCanvasSize();
    this.bindControls();
    this.render();
  }

  updateCanvasSize() {
    this.canvas.width = this.canvas.clientWidth;
    this.canvas.height = this.canvas.clientHeight;
  }

  bindControls() {
    this.playBtn?.addEventListener("click", () => this.togglePlayPause());
    this.stopBtn?.addEventListener("click", () => this.stop());
    this.resetBtn?.addEventListener("click", () => this.reset());
    this.muteBtn?.addEventListener("click", () => this.toggleMute());
    this.zoomInBtn?.addEventListener("click", () => this.zoomIn());
    this.zoomOutBtn?.addEventListener("click", () => this.zoomOut());
    this.speedSlider?.addEventListener("input", (e) =>
      this.setSpeed(parseFloat(e.target.value))
    );
  }

  togglePlayPause() {
    if (!this.audio) return;
    if (this.isPlaying) this.audio.pause();
    else (this.audio.playbackRate = this.speed), this.audio.play();
    this.isPlaying = !this.isPlaying;
    this.playBtn.textContent = this.isPlaying ? "⏸" : "▶";
  }

  stop() {
    if (!this.audio) return;
    this.audio.pause();
    this.audio.currentTime = 0;
    this.isPlaying = false;
    this.playBtn.textContent = "▶";
  }

  reset() {
    this.stop();
    this.zoom = 1;
    this.offset = 0;
    this.render();
  }

  toggleMute() {
    if (!this.audio) return;
    this.audio.muted = !this.audio.muted;
    this.isMuted = this.audio.muted;
    this.muteBtn.textContent = this.isMuted ? "🔇" : "🔊";
  }

  zoomIn() {
    this.zoom = Math.min(this.zoom * 1.5, 10);
    this.render();
  }
  zoomOut() {
    this.zoom = Math.max(this.zoom / 1.5, 0.5);
    this.render();
  }

  setSpeed(value) {
    this.speed = value;
    if (this.audio) this.audio.playbackRate = value;
    if (this.speedLabel)
      this.speedLabel.textContent = `Speed: ${value.toFixed(2)}x`;
  }

  updateData(samples, time, audioSrc = null) {
    this.samples = samples;
    this.time = time;
    if (audioSrc) this.audio = new Audio(audioSrc);
    this.render();
  }

  render() {
    if (!this.samples || !this.time) return;
    const ctx = this.ctx,
      w = this.canvas.width,
      h = this.canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = this.color;
    ctx.beginPath();

    const zoomedLength = Math.floor(this.samples.length / this.zoom);
    const startIdx = Math.floor(this.offset * this.samples.length);

    for (let i = 0; i < zoomedLength; i++) {
      const idx = startIdx + i;
      if (idx >= this.samples.length) break;
      const x = (i / zoomedLength) * w;
      const y = h / 2 - (this.samples[idx] * h) / 2;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
}
