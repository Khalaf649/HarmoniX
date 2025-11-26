export class FourierController {
  constructor({
    containerId,
    frequencies = [],
    magnitudes = [],
    title = "FFT",
    parentId = "frequency-domain", // Default parent container
  }) {
    this.containerId = containerId;
    this.parentId = parentId;
    this.frequencies = frequencies;
    this.magnitudes = magnitudes;
    this.title = title;

    this.zoom = 1;
    this.offset = 0;
    this.useAudiogramScale = false; // Toggle: false = linear, true = audiogram (log freq, dB mag)

    // ✅ Create DOM if missing
    this._createViewerElement();
    this.container = document.getElementById(containerId);
    if (!this.container) throw new Error(`Container #${containerId} not found`);

    // Controls
    this.resetBtn = this.container.querySelector(".reset-btn");
    this.zoomInBtn = this.container.querySelector(".zoom-in");
    this.zoomOutBtn = this.container.querySelector(".zoom-out");
    this.zoomLabel = this.container.querySelector(".zoom-label");
    this.panSlider = this.container.querySelector(".pan-slider");
    this.scaleToggle = this.container.querySelector(".scale-toggle");
    this.scaleLabel = this.container.querySelector(".scale-label");
    this.fftTitle = this.container.querySelector(".fft-viewer-title");

    if (this.fftTitle) this.fftTitle.textContent = this.title;

    // Plot container
    this.plotContainer = this.container.querySelector(".fft-plot-container");
    if (!this.plotContainer)
      throw new Error("Plot container element not found inside container");

    // Initialize
    this.initSliders();
    this.bindControls();
    this.render();
  }

  _createViewerElement() {
    const parent = document.getElementById(this.parentId);
    if (!parent) throw new Error(`Parent container ${this.parentId} not found`);

    if (document.getElementById(this.containerId)) return;

    const wrapper = document.createElement("div");
    wrapper.id = this.containerId;
    wrapper.className = "card card-backdrop-blur fft-viewer";
    wrapper.innerHTML = `
      <div class="fft-viewer-header">
        <h3 class="fft-viewer-title">${this.title}</h3>
      </div>
      <div class="fft-plot-container" style="width: 100%; height: 300px;"></div>
      <div class="playback-controls">
        <div class="playback-controls-group">
          <button class="btn btn-secondary btn-sm reset-btn">↺</button>
        </div>
        <div class="playback-controls-slider">
          <span class="playback-controls-label pan-label">Pos</span>
          <input type="range" min="0" max="1" step="0.001" value="0" class="pan-slider slider-input">
        </div>
        <div class="playback-controls-zoom">
          <button class="btn btn-secondary btn-sm zoom-out">-</button>
          <span class="playback-controls-zoom-label zoom-label">1x</span>
          <button class="btn btn-secondary btn-sm zoom-in">+</button>
        </div>
        <div class="playback-controls-scale">
          <label class="switch">
            <input type="checkbox" class="scale-toggle switch-input">
            <span class="switch-slider"></span>
          </label>
          <span class="playback-controls-label scale-label">Linear</span>
        </div>
      </div>
    `;
    parent.appendChild(wrapper);
  }

  initSliders() {
    const slider = this.panSlider;
    if (!slider) return;

    this._styleSliderTrack(slider);
    slider.addEventListener("input", () => this._styleSliderTrack(slider));
  }

  _styleSliderTrack(slider) {
    if (!slider) return;
    const min = parseFloat(slider.min || 0);
    const max = parseFloat(slider.max || 1);
    const val = parseFloat(slider.value || 0);
    const percent = ((val - min) / (max - min)) * 100;
    slider.style.background = `linear-gradient(to right, #1FD5F9 0%, #1FD5F9 ${percent}%, #a0a0a0 ${percent}%, #a0a0a0 100%)`;
  }

  bindControls() {
    this.resetBtn?.addEventListener("click", () => this.reset());
    this.zoomInBtn?.addEventListener("click", () => {
      this.zoom *= 1.5;
      this.clampOffset();
      this.render();
    });
    this.zoomOutBtn?.addEventListener("click", () => {
      this.zoom = Math.max(this.zoom / 1.5, 1);
      this.clampOffset();
      this.render();
    });
    this.panSlider?.addEventListener("input", (e) => {
      this.offset = parseFloat(e.target.value);
      this._styleSliderTrack(this.panSlider);
      this.render();
    });
    this.scaleToggle?.addEventListener("change", (e) => {
      this.useAudiogramScale = e.target.checked;
      this.offset = 0;
      this.zoom = 1;
      if (this.panSlider) this.panSlider.value = 0;
      if (this.scaleLabel) {
        this.scaleLabel.textContent = this.useAudiogramScale
          ? "Audiogram"
          : "Linear";
      }
      this._styleSliderTrack(this.panSlider);
      this.render();
    });
  }

  reset() {
    this.zoom = 1;
    this.offset = 0;
    if (this.panSlider) this.panSlider.value = 0;
    if (this.zoomLabel) this.zoomLabel.textContent = "1x";
    this._styleSliderTrack(this.panSlider);
    this.render();
  }

  clampOffset() {
    const maxOffset = Math.max(0, 1 - 1 / this.zoom);
    this.offset = Math.min(Math.max(this.offset, 0), maxOffset);
    if (this.panSlider) {
      this.panSlider.value = this.offset;
      this._styleSliderTrack(this.panSlider);
    }
    if (this.zoomLabel) this.zoomLabel.textContent = `${this.zoom.toFixed(2)}x`;
  }

  getVisibleData() {
    if (!this.frequencies.length || !this.magnitudes.length)
      return { visibleFreq: [], visibleMag: [] };

    const totalPoints = this.frequencies.length;
    const visibleCount = Math.floor(totalPoints / this.zoom);
    const start = Math.floor(this.offset * (totalPoints - visibleCount));
    const end = Math.min(start + visibleCount, totalPoints);

    const maxPoints = 2000;
    const step = Math.ceil((end - start) / maxPoints);

    const visibleFreq = [];
    const visibleMag = [];
    for (let i = start; i < end; i += step) {
      visibleFreq.push(this.frequencies[i]);
      visibleMag.push(this.magnitudes[i]);
    }

    return { visibleFreq, visibleMag };
  }

  render() {
    const { visibleFreq, visibleMag } = this.getVisibleData();
    if (!visibleFreq.length) {
      if (this.plotContainer) Plotly.purge(this.plotContainer);
      return;
    }

    // Transform data based on scale
    let xData = visibleFreq;
    let yData = visibleMag;
    let xLabel = "Frequency (Hz)";
    let yLabel = "Magnitude";

    if (this.useAudiogramScale) {
      // Audiogram scale: log frequency (Hz), dB magnitude (20*log10(mag))
      xData = visibleFreq.map((f) => (f > 0 ? Math.log10(f) : -10)); // Avoid log(0)
      yData = visibleMag.map((m) => (m > 0 ? 20 * Math.log10(m) : -80)); // Clamp to -80 dB
      xLabel = "Log Frequency (log Hz)";
      yLabel = "Magnitude (dB)";
    }

    const trace = {
      x: xData,
      y: yData,
      type: "scatter",
      mode: "lines",
      line: { color: "#1FD5F9", width: 2 },
      showlegend: false,
    };

    const layout = {
      title: false,
      xaxis: {
        title: xLabel,
        showgrid: false,
        zeroline: false,
        showline: true,
        linewidth: 1,
        mirror: true,
      },
      yaxis: {
        title: yLabel,
        showgrid: false,
        zeroline: false,
        showline: true,
        linewidth: 1,
        mirror: true,
      },
      margin: { l: 50, r: 10, t: 0, b: 40 },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      dragmode: "pan",
      hovermode: false,
    };

    const config = {
      displayModeBar: false,
      staticPlot: false,
      responsive: true,
      scrollZoom: true,
    };

    Plotly.react(this.plotContainer, [trace], layout, config);
  }

  updateData(frequencies, magnitudes) {
    // Update data safely
    this.frequencies = frequencies;
    this.magnitudes = magnitudes;
    this.offset = 0;
    this.zoom = 1;

    if (this.panSlider) this.panSlider.value = 0;
    if (this.zoomLabel) this.zoomLabel.textContent = "1x";
    if (this.scaleToggle) this.scaleToggle.checked = false;
    if (this.scaleLabel) this.scaleLabel.textContent = "Linear";
    this.useAudiogramScale = false;

    this._styleSliderTrack(this.panSlider);

    this.render();
  }
}
