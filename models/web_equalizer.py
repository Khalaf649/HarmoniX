# web_equalizer.py
from flask import Flask, render_template, request, jsonify
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from integration_api import ai_models_api
from scipy.io import wavfile
import threading
import simpleaudio as sa
import os

app = Flask(__name__)

class WebEqualizer:
    def __init__(self):
        self.ai_api = ai_models_api
        self.sample_rate = 44100
        self.current_mode = "manual"
        self.input_signal = None
        self.current_audio = None
        
        # Manual equalizer bands
        self.freq_bands = [
            {"name": "Sub Bass", "range": (20, 60), "gain": 1.0, "color": "#1f77b4"},
            {"name": "Bass", "range": (60, 250), "gain": 1.0, "color": "#ff7f0e"},
            {"name": "Low Mids", "range": (250, 500), "gain": 1.0, "color": "#2ca02c"},
            {"name": "Mids", "range": (500, 2000), "gain": 1.0, "color": "#d62728"},
            {"name": "High Mids", "range": (2000, 4000), "gain": 1.0, "color": "#9467bd"},
            {"name": "Highs", "range": (4000, 20000), "gain": 1.0, "color": "#8c564b"}
        ]
        
        # AI mode sliders
        self.ai_sliders = {
            "human_voices": [1.0, 1.0, 1.0, 1.0],
            "musical_instruments": [1.0, 1.0, 1.0, 1.0]
        }
        
        self.create_test_signal()
    
    def create_test_signal(self, duration=5):
        """Create a rich test signal"""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Distinct frequency components
        components = {
            'sub_bass': np.sin(2 * np.pi * 40 * t) * 0.3,
            'bass': np.sin(2 * np.pi * 100 * t) * 0.4,
            'low_mid': np.sin(2 * np.pi * 350 * t) * 0.5,
            'mid': np.sin(2 * np.pi * 1000 * t) * 0.6,
            'high_mid': np.sin(2 * np.pi * 2500 * t) * 0.4,
            'high': np.sin(2 * np.pi * 6000 * t) * 0.3,
        }
        
        # Add rhythm
        rhythm = 0.7 + 0.3 * np.sin(2 * np.pi * 2 * t)
        combined = sum(components.values()) * rhythm
        
        # Fade in/out
        fade_samples = int(0.2 * self.sample_rate)
        envelope = np.ones_like(t)
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        
        self.input_signal = (combined * envelope) / np.max(np.abs(combined))
        return self.input_signal
    
    def manual_equalizer_process(self, audio_data):
        """Apply manual equalizer with band gains"""
        output = np.zeros_like(audio_data)
        fft_data = np.fft.fft(audio_data)
        frequencies = np.fft.fftfreq(len(audio_data), 1/self.sample_rate)
        
        for band in self.freq_bands:
            low_freq, high_freq = band["range"]
            mask = (np.abs(frequencies) >= low_freq) & (np.abs(frequencies) <= high_freq)
            band_fft = fft_data.copy()
            band_fft[~mask] = 0
            band_signal = np.real(np.fft.ifft(band_fft))
            output += band_signal * band["gain"]
            
        return output
    
    def process_audio(self):
        """Process audio based on current mode"""
        if self.current_mode == "manual":
            return self.manual_equalizer_process(self.input_signal)
        else:
            sliders = self.ai_sliders.get(self.current_mode, [1.0, 1.0, 1.0, 1.0])
            return self.ai_api.process_audio(self.input_signal, sliders, self.sample_rate)
    
    def create_visualization(self):
        """Create visualization plot"""
        if self.current_audio is None:
            self.current_audio = self.process_audio()
        
        original = self.input_signal
        processed = self.current_audio
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Time domain
        time_axis = np.linspace(0, len(original)/self.sample_rate, len(original))
        ax1.plot(time_axis[:1000], original[:1000], 'b-', alpha=0.7, label='Original', linewidth=2)
        ax1.plot(time_axis[:1000], processed[:1000], 'r-', alpha=0.8, label='Processed', linewidth=1.5)
        ax1.set_title('Time Domain Comparison')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Amplitude')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Frequency spectrum
        fft_orig = np.abs(np.fft.fft(original))
        fft_proc = np.abs(np.fft.fft(processed))
        freqs = np.fft.fftfreq(len(original), 1/self.sample_rate)
        positive_idx = (freqs > 0) & (freqs < 8000)
        
        ax2.semilogy(freqs[positive_idx], fft_orig[positive_idx], 'b-', alpha=0.6, label='Original', linewidth=2)
        ax2.semilogy(freqs[positive_idx], fft_proc[positive_idx], 'r-', alpha=0.8, label='Processed', linewidth=1.5)
        ax2.set_title('Frequency Spectrum')
        ax2.set_xlabel('Frequency (Hz)')
        ax2.set_ylabel('Magnitude')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Frequency response
        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = np.divide(fft_proc, fft_orig, out=np.ones_like(fft_proc), where=fft_orig > 0.001)
        ax3.plot(freqs[positive_idx], ratio[positive_idx], 'purple', linewidth=2)
        ax3.axhline(y=1, color='red', linestyle='--', alpha=0.5, label='No Change')
        ax3.set_title('Frequency Response (Output/Input)')
        ax3.set_xlabel('Frequency (Hz)')
        ax3.set_ylabel('Gain Ratio')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim(0, 2.5)
        
        # Band gains visualization
        if self.current_mode == "manual":
            bands_x = [f"{band['range'][0]}-{band['range'][1]}" for band in self.freq_bands]
            gains = [band["gain"] for band in self.freq_bands]
            colors = [band["color"] for band in self.freq_bands]
            
            bars = ax4.bar(bands_x, gains, color=colors, alpha=0.7)
            ax4.set_title('Frequency Band Gains')
            ax4.set_ylabel('Gain (0-2)')
            ax4.tick_params(axis='x', rotation=45)
            ax4.axhline(y=1, color='green', linestyle='--', alpha=0.5, label='Neutral')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Convert plot to base64 for web display
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plot_data = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        return plot_data

# Global equalizer instance
equalizer = WebEqualizer()

@app.route('/')
def index():
    """Main page with equalizer interface"""
    return render_template('equalizer.html')

@app.route('/get_initial_data')
def get_initial_data():
    """Get initial equalizer state"""
    return jsonify({
        'modes': ['manual', 'human_voices', 'musical_instruments'],
        'current_mode': equalizer.current_mode,
        'manual_bands': equalizer.freq_bands,
        'ai_sliders': equalizer.ai_sliders
    })

@app.route('/update_band_gain', methods=['POST'])
def update_band_gain():
    """Update manual band gain"""
    data = request.json
    band_index = data.get('band_index')
    gain = data.get('gain')
    
    if 0 <= band_index < len(equalizer.freq_bands):
        equalizer.freq_bands[band_index]["gain"] = max(0.0, min(2.0, float(gain)))
        equalizer.current_audio = equalizer.process_audio()
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/update_ai_slider', methods=['POST'])
def update_ai_slider():
    """Update AI mode slider"""
    data = request.json
    mode = data.get('mode')
    slider_index = data.get('slider_index')
    value = data.get('value')
    
    if mode in equalizer.ai_sliders and 0 <= slider_index < len(equalizer.ai_sliders[mode]):
        equalizer.ai_sliders[mode][slider_index] = max(0.0, min(2.0, float(value)))
        equalizer.current_audio = equalizer.process_audio()
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/switch_mode', methods=['POST'])
def switch_mode():
    """Switch between equalizer modes"""
    data = request.json
    mode = data.get('mode')
    
    if mode in ['manual', 'human_voices', 'musical_instruments']:
        equalizer.current_mode = mode
        equalizer.current_audio = equalizer.process_audio()
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/get_visualization')
def get_visualization():
    """Get current visualization"""
    plot_data = equalizer.create_visualization()
    return jsonify({'plot': plot_data})

@app.route('/play_audio')
def play_audio():
    """Play current audio"""
    def play_audio_thread():
        try:
            audio_16bit = (equalizer.current_audio * 32767).astype(np.int16)
            play_obj = sa.play_buffer(audio_16bit, 1, 2, equalizer.sample_rate)
            play_obj.wait_done()
        except Exception as e:
            print(f"Playback error: {e}")
    
    threading.Thread(target=play_audio_thread).start()
    return jsonify({'success': True})

@app.route('/save_audio')
def save_audio():
    """Save current audio to file"""
    try:
        filename = f'web_equalizer_output.wav'
        wavfile.write(filename, equalizer.sample_rate, 
                     (equalizer.current_audio * 32767).astype(np.int16))
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create the HTML template
    with open('templates/equalizer.html', 'w') as f:
        f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Equalizer - Web Interface</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50, #34495e);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .content {
            display: grid;
            grid-template-columns: 400px 1fr;
            gap: 0;
            min-height: 800px;
        }
        
        .controls {
            background: #f8f9fa;
            padding: 30px;
            border-right: 1px solid #e9ecef;
        }
        
        .mode-selector {
            margin-bottom: 30px;
        }
        
        .mode-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .mode-btn {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 10px;
            background: #e9ecef;
            color: #495057;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .mode-btn.active {
            background: #007bff;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,123,255,0.3);
        }
        
        .mode-btn:hover:not(.active) {
            background: #dee2e6;
        }
        
        .sliders-container {
            margin-top: 20px;
        }
        
        .band-slider {
            margin-bottom: 25px;
        }
        
        .band-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .band-name {
            font-weight: 600;
            color: #495057;
        }
        
        .band-value {
            background: #007bff;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }
        
        .slider {
            width: 100%;
            height: 8px;
            -webkit-appearance: none;
            background: #e9ecef;
            border-radius: 10px;
            outline: none;
        }
        
        .slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #007bff;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .slider::-webkit-slider-thumb:hover {
            background: #0056b3;
            transform: scale(1.2);
        }
        
        .action-buttons {
            margin-top: 30px;
            display: flex;
            gap: 15px;
        }
        
        .action-btn {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .play-btn {
            background: #28a745;
            color: white;
        }
        
        .play-btn:hover {
            background: #218838;
            transform: translateY(-2px);
        }
        
        .save-btn {
            background: #6c757d;
            color: white;
        }
        
        .save-btn:hover {
            background: #545b62;
            transform: translateY(-2px);
        }
        
        .visualization {
            padding: 30px;
            background: white;
        }
        
        .plot-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .plot-image {
            width: 100%;
            height: auto;
            border-radius: 8px;
        }
        
        .ai-sliders {
            margin-top: 20px;
        }
        
        .ai-slider {
            margin-bottom: 20px;
        }
        
        .ai-slider-label {
            font-weight: 600;
            color: #495057;
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎛️ AI Audio Equalizer</h1>
            <p>Control frequency bands manually or use AI-powered separation</p>
        </div>
        
        <div class="content">
            <div class="controls">
                <div class="mode-selector">
                    <h3>🎚️ Equalizer Mode</h3>
                    <div class="mode-buttons">
                        <button class="mode-btn" onclick="switchMode('manual')">Manual EQ</button>
                        <button class="mode-btn" onclick="switchMode('human_voices')">AI Voices</button>
                        <button class="mode-btn" onclick="switchMode('musical_instruments')">AI Instruments</button>
                    </div>
                </div>
                
                <div class="sliders-container">
                    <div id="manual-sliders">
                        <h3>🎛️ Frequency Bands</h3>
                        <div id="band-sliders"></div>
                    </div>
                    
                    <div id="ai-sliders" style="display: none;">
                        <h3>🤖 AI Controls</h3>
                        <div id="ai-voice-sliders" class="ai-sliders">
                            <!-- AI voice sliders will be added here -->
                        </div>
                        <div id="ai-instrument-sliders" class="ai-sliders" style="display: none;">
                            <!-- AI instrument sliders will be added here -->
                        </div>
                    </div>
                </div>
                
                <div class="action-buttons">
                    <button class="action-btn play-btn" onclick="playAudio()">▶️ Play Audio</button>
                    <button class="action-btn save-btn" onclick="saveAudio()">💾 Save Audio</button>
                </div>
            </div>
            
            <div class="visualization">
                <h3>📊 Audio Visualization</h3>
                <div class="plot-container">
                    <img id="plot-image" class="plot-image" src="" alt="Audio Visualization">
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentMode = 'manual';
        
        // Initialize the interface
        async function initialize() {
            const response = await fetch('/get_initial_data');
            const data = await response.json();
            
            currentMode = data.current_mode;
            updateModeButtons();
            
            if (currentMode === 'manual') {
                createManualSliders(data.manual_bands);
            } else {
                createAISliders(data.current_mode, data.ai_sliders);
            }
            
            updateVisualization();
        }
        
        // Create manual frequency band sliders
        function createManualSliders(bands) {
            const container = document.getElementById('band-sliders');
            container.innerHTML = '';
            
            bands.forEach((band, index) => {
                const sliderDiv = document.createElement('div');
                sliderDiv.className = 'band-slider';
                sliderDiv.innerHTML = `
                    <div class="band-header">
                        <span class="band-name">${band.name}</span>
                        <span class="band-value">${band.gain.toFixed(2)}</span>
                    </div>
                    <input type="range" class="slider" min="0" max="2" step="0.01" 
                           value="${band.gain}" 
                           oninput="updateBandGain(${index}, this.value)"
                           style="accent-color: ${band.color}">
                    <div style="font-size: 0.8em; color: #6c757d; margin-top: 5px;">
                        ${band.range[0]} - ${band.range[1]} Hz
                    </div>
                `;
                container.appendChild(sliderDiv);
            });
        }
        
        // Create AI mode sliders
        function createAISliders(mode, sliders) {
            const voiceContainer = document.getElementById('ai-voice-sliders');
            const instrumentContainer = document.getElementById('ai-instrument-sliders');
            
            if (mode === 'human_voices') {
                voiceContainer.style.display = 'block';
                instrumentContainer.style.display = 'none';
                
                const labels = ['Voice 1', 'Voice 2', 'Voice 3', 'Background'];
                voiceContainer.innerHTML = '';
                
                labels.forEach((label, index) => {
                    const sliderDiv = document.createElement('div');
                    sliderDiv.className = 'ai-slider';
                    sliderDiv.innerHTML = `
                        <div class="ai-slider-label">${label}</div>
                        <input type="range" class="slider" min="0" max="2" step="0.01" 
                               value="${sliders[mode][index]}" 
                               oninput="updateAISlider('${mode}', ${index}, this.value)">
                    `;
                    voiceContainer.appendChild(sliderDiv);
                });
            } else {
                voiceContainer.style.display = 'none';
                instrumentContainer.style.display = 'block';
                
                const labels = ['Drums', 'Bass', 'Melody', 'Vocals'];
                instrumentContainer.innerHTML = '';
                
                labels.forEach((label, index) => {
                    const sliderDiv = document.createElement('div');
                    sliderDiv.className = 'ai-slider';
                    sliderDiv.innerHTML = `
                        <div class="ai-slider-label">${label}</div>
                        <input type="range" class="slider" min="0" max="2" step="0.01" 
                               value="${sliders[mode][index]}" 
                               oninput="updateAISlider('${mode}', ${index}, this.value)">
                    `;
                    instrumentContainer.appendChild(sliderDiv);
                });
            }
        }
        
        // Switch between modes
        async function switchMode(mode) {
            const response = await fetch('/switch_mode', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({mode: mode})
            });
            
            if (response.ok) {
                currentMode = mode;
                updateModeButtons();
                
                if (mode === 'manual') {
                    document.getElementById('manual-sliders').style.display = 'block';
                    document.getElementById('ai-sliders').style.display = 'none';
                    // Reload manual sliders
                    const data = await (await fetch('/get_initial_data')).json();
                    createManualSliders(data.manual_bands);
                } else {
                    document.getElementById('manual-sliders').style.display = 'none';
                    document.getElementById('ai-sliders').style.display = 'block';
                    // Reload AI sliders
                    const data = await (await fetch('/get_initial_data')).json();
                    createAISliders(mode, data.ai_sliders);
                }
                
                updateVisualization();
            }
        }
        
        // Update mode buttons appearance
        function updateModeButtons() {
            document.querySelectorAll('.mode-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            document.querySelectorAll('.mode-btn').forEach(btn => {
                if (btn.textContent.includes(currentMode === 'manual' ? 'Manual' : 
                    currentMode === 'human_voices' ? 'Voices' : 'Instruments')) {
                    btn.classList.add('active');
                }
            });
        }
        
        // Update manual band gain
        async function updateBandGain(bandIndex, gain) {
            await fetch('/update_band_gain', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({band_index: bandIndex, gain: parseFloat(gain)})
            });
            
            // Update display value
            document.querySelectorAll('.band-value')[bandIndex].textContent = parseFloat(gain).toFixed(2);
            updateVisualization();
        }
        
        // Update AI slider
        async function updateAISlider(mode, sliderIndex, value) {
            await fetch('/update_ai_slider', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    mode: mode,
                    slider_index: sliderIndex,
                    value: parseFloat(value)
                })
            });
            updateVisualization();
        }
        
        // Update visualization
        async function updateVisualization() {
            const response = await fetch('/get_visualization');
            const data = await response.json();
            document.getElementById('plot-image').src = 'data:image/png;base64,' + data.plot;
        }
        
        // Play audio
        async function playAudio() {
            await fetch('/play_audio');
        }
        
        // Save audio
        async function saveAudio() {
            const response = await fetch('/save_audio');
            const data = await response.json();
            if (data.success) {
                alert('Audio saved as: ' + data.filename);
            } else {
                alert('Error saving audio: ' + data.error);
            }
        }
        
        // Initialize on load
        window.onload = initialize;
        
        // Auto-refresh visualization every 2 seconds when sliders are being dragged
        let isDragging = false;
        document.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('slider')) {
                isDragging = true;
                startAutoRefresh();
            }
        });
        
        document.addEventListener('mouseup', () => {
            isDragging = false;
        });
        
        function startAutoRefresh() {
            if (isDragging) {
                updateVisualization();
                setTimeout(startAutoRefresh, 200);
            }
        }
    </script>
</body>
</html>
''')
    
    print("🚀 Starting Web Equalizer...")
    print("📡 Open your web browser and go to: http://localhost:5000")
    print("🎛️  You can now control the equalizer with your mouse!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)