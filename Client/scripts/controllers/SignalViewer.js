export class SignalViewer {
  constructor({
    containerId,
    samples = [],
    sampleRate = 44100,
    audioSrc = null,
    color = "#999",
    title = "Signal",
    parentId = "time-domain",
  }) {
    this.containerId = containerId;
    this.parentId = parentId;
    this.color = color;
    this.title = title;
    this.sampleRate = sampleRate;
    this.samples = samples || [];
    this.audio = audioSrc && this.samples.length ? new Audio(audioSrc) : null;

    this.time = this.samples.map((_, i) => i / this.sampleRate);

    this._createViewerElement();
    this.container = document.getElementById(containerId);
    if (!this.container) throw new Error(`Container ${containerId} not found`);

    this._boundOnAudioTimeUpdate = this._onAudioTimeUpdate.bind(this);

    this.isPlaying = false;
    this.isMuted = false;
    this.speed = 1;
    this.zoom = 1;
    this.offset = 0;
    this.currentTime = 0;

    // Plot container
    this.plotContainer = this.container.querySelector(".signal-plot-container");
    if (!this.plotContainer) throw new Error("Plot container not found");

    // Controls
    this.playBtn = this.container.querySelector(".play-btn");
    this.stopBtn = this.container.querySelector(".stop-btn");
    this.resetBtn = this.container.querySelector(".reset-btn");
    this.muteBtn = this.container.querySelector(".mute-toggle-btn");
    this.speedSlider = this.container.querySelector(".speed-slider");
    this.speedLabel = this.container.querySelector(".speed-label");
    this.zoomInBtn = this.container.querySelector(".zoom-in");
    this.zoomOutBtn = this.container.querySelector(".zoom-out");
    this.zoomLabel = this.container.querySelector(".zoom-label");
    this.signalTitle = this.container.querySelector(".signal-viewer-title");
    this.signalDuration = this.container.querySelector(
      ".signal-viewer-duration"
    );
    this.panSlider = this.container.querySelector(".pan-slider");
    this.signalTitle.textContent = this.title;

    // Plotly setup
    this.plotData = [];
    this.plotLayout = {};
    this.plotConfig = {
      displayModeBar: false,
      staticPlot: false,
      responsive: true,
    };

    this.bindControls();
    this._initSliders();
    this.render();

    // Audio listeners
    if (this.audio) this._attachAudioListeners();
  }

  _attachAudioListeners() {
    this.audio.addEventListener("timeupdate", this._boundOnAudioTimeUpdate);
    this.audio.addEventListener("ended", () => {
      this.isPlaying = false;
      if (this.playBtn) this.playBtn.textContent = "▶";
    });
  }

  /* -------------------------- Create Viewer DOM -------------------------- */
  _createViewerElement() {
    const parent = document.getElementById(this.parentId);
    if (!parent) throw new Error(`Parent container ${this.parentId} not found`);
    if (document.getElementById(this.containerId)) return;

    const wrapper = document.createElement("div");
    wrapper.id = this.containerId;
    wrapper.className = "card card-backdrop-blur signal-viewer";
    wrapper.innerHTML = `
      <div class="signal-viewer-header">
        <h3 class="signal-viewer-title"></h3>
        <div class="signal-viewer-duration">No Signal</div>
      </div>
      <div class="signal-plot-container" style="width: 100%; height: 300px;"></div>
      <div class="playback-controls">
        <div class="playback-controls-group">
          <button class="btn btn-sm btn-default play-btn">▶</button>
          <button class="btn btn-secondary btn-sm stop-btn">⏹</button>
          <button class="btn btn-secondary btn-sm reset-btn">↺</button>
          <button class="btn btn-secondary btn-sm mute-toggle-btn">🔊</button>
        </div>
        <div class="playback-controls-slider">
          <span class="playback-controls-label speed-label">Speed: 1x</span>
          <input type="range" min="0.25" max="2" step="0.25" value="1" class="speed-slider slider-input">
          <span class="playback-controls-label pan-label">Pos</span>
          <input type="range" min="0" max="1" step="0.001" value="0" class="pan-slider slider-input">
        </div>
        <div class="playback-controls-zoom">
          <button class="btn btn-secondary btn-sm zoom-out">-</button>
          <span class="playback-controls-zoom-label zoom-label">1x</span>
          <button class="btn btn-secondary btn-sm zoom-in">+</button>
        </div>
      </div>
    `;
    parent.appendChild(wrapper);
  }

  /* -------------------------- Slider Styling -------------------------- */
  _initSliders() {
    [this.speedSlider, this.panSlider].filter(Boolean).forEach((slider) => {
      this._styleSliderTrack(slider);
      slider.addEventListener("input", () => this._styleSliderTrack(slider));
    });
  }

  _styleSliderTrack(slider) {
    if (!slider) return;
    const min = parseFloat(slider.min || 0);
    const max = parseFloat(slider.max || 1);
    const val = parseFloat(slider.value || 0);
    const percent = max - min > 0 ? ((val - min) / (max - min)) * 100 : 0;
    slider.style.background = `linear-gradient(to right, #1fd5f9 0%, #1fd5f9 ${percent}%, #a0a0a0 ${percent}%, #a0a0a0 100%)`;
  }

  /* -------------------------- Update Samples -------------------------- */
  updateSamples(samples, sampleRate = this.sampleRate, audioSrc = null) {
    this.samples = samples || [];
    this.sampleRate = sampleRate;
    this.time = this.samples.map((_, i) => i / this.sampleRate);
    this.currentTime = 0;
    this.offset = 0;
    this.zoom = 1;

    // If no samples, clear audio
    if (!this.samples.length) audioSrc = null;

    // Destroy old audio
    if (this.audio) {
      this.audio.pause();
      this.audio.removeEventListener(
        "timeupdate",
        this._boundOnAudioTimeUpdate
      );
      this.audio = null;
      this.isPlaying = false;
      if (this.playBtn) this.playBtn.textContent = "▶";
    }

    if (audioSrc) {
      this.audio = new Audio(audioSrc);
      this._attachAudioListeners();
      this.isMuted = false;
      if (this.muteBtn) this.muteBtn.textContent = "🔊";
    }

    this.render();
  }

  /* -------------------------- Audio / Playback -------------------------- */
  _onAudioTimeUpdate() {
    this.currentTime = this.audio.currentTime;
    this.render();
  }

  togglePlayPause() {
    if (!this.audio) return;
    if (this.isPlaying) this.audio.pause();
    else (this.audio.playbackRate = this.speed), this.audio.play();
    this.isPlaying = !this.isPlaying;
    if (this.playBtn) this.playBtn.textContent = this.isPlaying ? "⏸" : "▶";
  }

  stop() {
    if (!this.audio) return;
    this.audio.pause();
    this.audio.currentTime = 0;
    this.currentTime = 0;
    this.isPlaying = false;
    if (this.playBtn) this.playBtn.textContent = "▶";
    this.render();
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
    if (this.muteBtn) this.muteBtn.textContent = this.isMuted ? "🔇" : "🔊";
  }

  zoomIn() {
    this.zoom = Math.min(this.zoom * 1.5, 4000);
    if (this.zoomLabel) this.zoomLabel.textContent = `${this.zoom.toFixed(2)}x`;
    this.clampOffset();
    this.render();
  }

  zoomOut() {
    this.zoom = Math.max(this.zoom / 1.5, 1);
    if (this.zoomLabel) this.zoomLabel.textContent = `${this.zoom.toFixed(2)}x`;
    this.clampOffset();
    this.render();
  }

  setSpeed(value) {
    this.speed = value;
    if (this.audio) this.audio.playbackRate = value;
    if (this.speedLabel)
      this.speedLabel.textContent = `Speed: ${value.toFixed(2)}x`;
  }

  clampOffset() {
    const maxOffset = Math.max(0, 1 - 1 / this.zoom);
    this.offset = Math.min(Math.max(this.offset, 0), maxOffset);
    if (this.panSlider) {
      this.panSlider.value = this.offset;
      this._styleSliderTrack(this.panSlider);
    }
  }

  bindControls() {
    this.playBtn?.addEventListener("click", () => this.togglePlayPause());
    this.stopBtn?.addEventListener("click", () => this.stop());
    this.resetBtn?.addEventListener("click", () => this.reset());
    this.muteBtn?.addEventListener("click", () => this.toggleMute());
    this.zoomInBtn?.addEventListener("click", () => this.zoomIn());
    this.zoomOutBtn?.addEventListener("click", () => this.zoomOut());

    this.speedSlider?.addEventListener("input", (e) => {
      this.setSpeed(parseFloat(e.target.value));
      this._styleSliderTrack(this.speedSlider);
    });

    this.panSlider?.addEventListener("input", (e) => {
      this.offset = parseFloat(e.target.value);
      this.render();
      this._styleSliderTrack(this.panSlider);
    });
  }

  updateDuration() {
    if (!this.signalDuration) return;
    const totalSeconds = this.samples.length / this.sampleRate;
    const formatTime = (s) =>
      `${Math.floor(s / 60)}:${Math.floor(s % 60)
        .toString()
        .padStart(2, "0")}`;
    this.signalDuration.textContent = `${formatTime(
      this.currentTime
    )} / ${formatTime(totalSeconds)}`;
  }

  getVisibleData() {
    if (!this.samples.length) return { visibleTime: [], visibleSamples: [] };
    const totalSamples = this.samples.length;
    const visibleSamplesCount = Math.floor(totalSamples / this.zoom);
    const start = Math.floor(
      this.offset * (totalSamples - visibleSamplesCount)
    );
    const end = Math.min(start + visibleSamplesCount, totalSamples);

    const maxPoints = 2000;
    const step = Math.ceil((end - start) / maxPoints);

    const visibleTime = [],
      visibleSamples = [];
    for (let i = start; i < end; i += step) {
      visibleTime.push(this.time[i]);
      visibleSamples.push(this.samples[i]);
    }
    return { visibleTime, visibleSamples };
  }

  render() {
    if (!this.samples.length) {
      if (this.plotContainer) Plotly.purge(this.plotContainer);
      if (this.signalDuration) this.signalDuration.textContent = "No Signal";
      return;
    }

    const { visibleTime, visibleSamples } = this.getVisibleData();
    const currentTime = this.currentTime;

    const playedTrace = {
      x: [],
      y: [],
      type: "scatter",
      mode: "lines",
      line: { color: "#1FD5F9", width: 2 },
      showlegend: false,
    };
    const unplayedTrace = {
      x: [],
      y: [],
      type: "scatter",
      mode: "lines",
      line: { color: this.color, width: 2 },
      showlegend: false,
    };

    for (let i = 0; i < visibleTime.length; i++) {
      if (visibleTime[i] <= currentTime) {
        playedTrace.x.push(visibleTime[i]);
        playedTrace.y.push(visibleSamples[i]);
      } else {
        unplayedTrace.x.push(visibleTime[i]);
        unplayedTrace.y.push(visibleSamples[i]);
      }
    }

    this.plotData = [playedTrace, unplayedTrace];

    if (
      currentTime >= visibleTime[0] &&
      currentTime <= visibleTime[visibleTime.length - 1]
    ) {
      this.plotData.push({
        x: [currentTime, currentTime],
        y: [Math.min(...visibleSamples), Math.max(...visibleSamples)],
        type: "scatter",
        mode: "lines",
        line: { color: "#1FD5F9", width: 2, dash: "dash" },
        showlegend: false,
      });
    }

    this.plotLayout = {
      xaxis: { showgrid: false, zeroline: false, showline: true },
      yaxis: { showgrid: false, zeroline: false, showline: true },
      margin: { l: 30, r: 10, t: 0, b: 20 },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      hovermode: false,
      dragmode: "pan",
    };

    Plotly.react(
      this.plotContainer,
      this.plotData,
      this.plotLayout,
      this.plotConfig
    );
    this.updateDuration();
  }
}
