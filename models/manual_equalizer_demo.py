# manual_equalizer_demo.py
import numpy as np
import matplotlib.pyplot as plt
from integration_api import ai_models_api
from scipy.io import wavfile
import simpleaudio as sa
import time

class ManualEqualizerDemo:
    def __init__(self):
        self.ai_api = ai_models_api
        self.sample_rate = 44100
        self.current_mode = "manual"
        self.input_signal = None
        
        # Manual equalizer settings
        self.band_center = 1000  # Hz - horizontal control
        self.band_width = 500    # Hz - horizontal control  
        self.band_gain = 1.0     # 0-2 scale - vertical control
        
        # Frequency bands for manual mode
        self.freq_bands = [
            {"name": "Sub Bass", "range": (20, 60), "gain": 1.0},
            {"name": "Bass", "range": (60, 250), "gain": 1.0},
            {"name": "Low Mids", "range": (250, 500), "gain": 1.0},
            {"name": "Mids", "range": (500, 2000), "gain": 1.0},
            {"name": "High Mids", "range": (2000, 4000), "gain": 1.0},
            {"name": "Highs", "range": (4000, 20000), "gain": 1.0}
        ]
        
        self.current_band_index = 3  # Start with Mids band
        
    def create_test_signal(self, duration=5):
        """Create a rich test signal with multiple frequency components"""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Create distinct frequency components
        components = {
            'sub_bass': np.sin(2 * np.pi * 40 * t) * 0.3,
            'bass': np.sin(2 * np.pi * 100 * t) * 0.4,
            'low_mid': np.sin(2 * np.pi * 350 * t) * 0.5,
            'mid': np.sin(2 * np.pi * 1000 * t) * 0.6,
            'high_mid': np.sin(2 * np.pi * 2500 * t) * 0.4,
            'high': np.sin(2 * np.pi * 6000 * t) * 0.3,
            'very_high': np.sin(2 * np.pi * 10000 * t) * 0.2
        }
        
        # Add some rhythm and variation
        rhythm = 0.7 + 0.3 * np.sin(2 * np.pi * 2 * t)  # 2Hz rhythm
        combined = sum(components.values()) * rhythm
        
        # Fade in/out
        fade_samples = int(0.2 * self.sample_rate)
        envelope = np.ones_like(t)
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        
        signal = (combined * envelope) / np.max(np.abs(combined))
        self.input_signal = signal
        return signal
    
    def manual_band_filter(self, audio_data, center_freq, width, gain):
        """Apply manual band filter with adjustable center, width, and gain"""
        fft_data = np.fft.fft(audio_data)
        frequencies = np.fft.fftfreq(len(audio_data), 1/self.sample_rate)
        
        # Create bell curve filter
        low_freq = center_freq - width/2
        high_freq = center_freq + width/2
        
        # Apply gain to the selected band
        mask = (np.abs(frequencies) >= low_freq) & (np.abs(frequencies) <= high_freq)
        fft_data[mask] *= gain
        
        return np.real(np.fft.ifft(fft_data))
    
    def manual_multiband_eq(self, audio_data):
        """Apply multi-band equalizer with individual band gains"""
        if self.current_mode != "manual":
            return audio_data
            
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
        """Process audio based on current mode and settings"""
        if self.current_mode == "manual":
            return self.manual_multiband_eq(self.input_signal)
        else:
            # Use AI separation modes
            if self.current_mode == "human_voices":
                sliders = [1.0, 1.0, 1.0, 1.0]  # Default, will be overridden by band gains
            else:  # musical_instruments
                sliders = [1.0, 1.0, 1.0, 1.0]
            
            return self.ai_api.process_audio(self.input_signal, sliders, self.sample_rate)
    
    def update_manual_band(self, band_index, gain):
        """Update gain for a specific frequency band"""
        if 0 <= band_index < len(self.freq_bands):
            self.freq_bands[band_index]["gain"] = max(0.0, min(2.0, gain))
    
    def play_audio_comparison(self, original, processed, title):
        """Play original and processed audio with visualization"""
        print(f"\n🎵 Playing: {title}")
        
        # Show visualization
        self.show_comparison_plots(original, processed, title)
        
        # Play original
        print("▶️  Playing ORIGINAL signal...")
        self.play_audio(original)
        time.sleep(1)
        
        # Play processed
        print("▶️  Playing PROCESSED signal...")
        self.play_audio(processed)
        
        # Show current settings
        self.print_current_settings()
    
    def play_audio(self, audio):
        """Play audio using simpleaudio"""
        try:
            audio_16bit = (audio * 32767).astype(np.int16)
            play_obj = sa.play_buffer(audio_16bit, 1, 2, self.sample_rate)
            play_obj.wait_done()
        except Exception as e:
            print(f"❌ Could not play audio: {e}")
    
    def show_comparison_plots(self, original, processed, title):
        """Show detailed comparison plots"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Audio Comparison: {title}', fontsize=16)
        
        # Time domain
        time_axis = np.linspace(0, len(original)/self.sample_rate, len(original))
        axes[0, 0].plot(time_axis, original, 'b-', alpha=0.7, label='Original')
        axes[0, 0].plot(time_axis, processed, 'r-', alpha=0.8, label='Processed')
        axes[0, 0].set_title('Time Domain')
        axes[0, 0].set_xlabel('Time (s)')
        axes[0, 0].set_ylabel('Amplitude')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Frequency spectrum
        fft_orig = np.abs(np.fft.fft(original))
        fft_proc = np.abs(np.fft.fft(processed))
        freqs = np.fft.fftfreq(len(original), 1/self.sample_rate)
        positive_idx = (freqs > 0) & (freqs < 10000)
        
        axes[0, 1].semilogy(freqs[positive_idx], fft_orig[positive_idx], 'b-', alpha=0.6, label='Original')
        axes[0, 1].semilogy(freqs[positive_idx], fft_proc[positive_idx], 'r-', alpha=0.8, label='Processed')
        axes[0, 1].set_title('Frequency Spectrum')
        axes[0, 1].set_xlabel('Frequency (Hz)')
        axes[0, 1].set_ylabel('Magnitude')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Frequency response
        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = np.divide(fft_proc, fft_orig, out=np.ones_like(fft_proc), where=fft_orig > 0.001)
        axes[1, 0].plot(freqs[positive_idx], ratio[positive_idx], 'purple', linewidth=2)
        axes[1, 0].axhline(y=1, color='red', linestyle='--', alpha=0.5, label='No Change')
        axes[1, 0].set_title('Frequency Response (Output/Input)')
        axes[1, 0].set_xlabel('Frequency (Hz)')
        axes[1, 0].set_ylabel('Gain Ratio')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_ylim(0, 2.5)
        
        # Current band settings visualization
        if self.current_mode == "manual":
            bands_x = [f"{band['range'][0]}-{band['range'][1]}Hz" for band in self.freq_bands]
            gains = [band["gain"] for band in self.freq_bands]
            
            bars = axes[1, 1].bar(bands_x, gains, color='skyblue', alpha=0.7)
            # Highlight current band
            if 0 <= self.current_band_index < len(bars):
                bars[self.current_band_index].set_color('red')
            
            axes[1, 1].set_title('Current Band Gains')
            axes[1, 1].set_ylabel('Gain (0-2)')
            axes[1, 1].tick_params(axis='x', rotation=45)
            axes[1, 1].axhline(y=1, color='green', linestyle='--', alpha=0.5, label='Neutral')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def print_current_settings(self):
        """Print current equalizer settings"""
        print(f"\n⚙️  CURRENT SETTINGS:")
        print(f"   Mode: {self.current_mode}")
        
        if self.current_mode == "manual":
            print("   Frequency Band Gains:")
            for i, band in enumerate(self.freq_bands):
                marker = " ← CURRENT" if i == self.current_band_index else ""
                print(f"     {band['name']} ({band['range'][0]}-{band['range'][1]}Hz): {band['gain']:.2f}{marker}")
    
    def interactive_manual_control(self):
        """Interactive manual equalizer control"""
        print("\n🎛️  MANUAL EQUALIZER CONTROL")
        print("=" * 50)
        print("Use number keys to select frequency bands:")
        
        for i, band in enumerate(self.freq_bands):
            print(f"  {i+1}. {band['name']} ({band['range'][0]}-{band['range'][1]}Hz) - Current: {band['gain']:.2f}")
        
        print("\nControls:")
        print("  [1-6] - Select frequency band")
        print("  [↑/↓] - Increase/decrease gain for selected band (0.1 steps)")
        print("  [P]   - Play current settings")
        print("  [S]   - Save audio files")
        print("  [M]   - Switch to mode selection")
        print("  [Q]   - Quit manual mode")
        
        while True:
            try:
                choice = input("\n🎛️  Enter command: ").strip().lower()
                
                if choice == 'q':
                    break
                elif choice == 'm':
                    return "mode_select"
                elif choice == 'p':
                    processed = self.process_audio()
                    self.play_audio_comparison(self.input_signal, processed, "Manual Equalizer")
                elif choice == 's':
                    self.save_audio_files()
                elif choice in ['1', '2', '3', '4', '5', '6']:
                    band_idx = int(choice) - 1
                    self.current_band_index = band_idx
                    current_gain = self.freq_bands[band_idx]["gain"]
                    print(f"✅ Selected: {self.freq_bands[band_idx]['name']}")
                    print(f"   Current gain: {current_gain:.2f}")
                    print("   Use ↑/↓ arrows to adjust gain")
                
                elif choice in ['↑', 'up']:
                    if 0 <= self.current_band_index < len(self.freq_bands):
                        new_gain = min(2.0, self.freq_bands[self.current_band_index]["gain"] + 0.1)
                        self.freq_bands[self.current_band_index]["gain"] = new_gain
                        print(f"📈 Increased {self.freq_bands[self.current_band_index]['name']} gain to: {new_gain:.2f}")
                
                elif choice in ['↓', 'down']:
                    if 0 <= self.current_band_index < len(self.freq_bands):
                        new_gain = max(0.0, self.freq_bands[self.current_band_index]["gain"] - 0.1)
                        self.freq_bands[self.current_band_index]["gain"] = new_gain
                        print(f"📉 Decreased {self.freq_bands[self.current_band_index]['name']} gain to: {new_gain:.2f}")
                
                else:
                    print("❌ Invalid command. Use 1-6 to select bands, ↑/↓ to adjust, P to play, Q to quit.")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        
        return "main_menu"
    
    def save_audio_files(self):
        """Save current audio settings to files"""
        print("\n💾 Saving audio files...")
        
        # Save original
        wavfile.write('original_signal.wav', self.sample_rate, 
                     (self.input_signal * 32767).astype(np.int16))
        
        # Save processed
        processed = self.process_audio()
        filename = f'processed_{self.current_mode}.wav'
        wavfile.write(filename, self.sample_rate, 
                     (processed * 32767).astype(np.int16))
        
        print(f"✅ Saved: original_signal.wav")
        print(f"✅ Saved: {filename}")
        print(f"🎧 Play these files to hear the difference!")
    
    def run_demo(self):
        """Main demo loop"""
        print("🎛️  ADVANCED EQUALIZER DEMO")
        print("=" * 60)
        print("Features:")
        print("• Manual frequency band control (6 bands)")
        print("• AI-powered voice/instrument separation") 
        print("• Real-time audio comparison")
        print("• Visual frequency analysis")
        print("• Save audio files for offline listening")
        
        # Create test signal
        print("\n🎵 Creating test signal...")
        self.create_test_signal()
        print("✅ Test signal ready!")
        
        while True:
            print("\n" + "=" * 50)
            print("🏠 MAIN MENU - CHOOSE MODE:")
            print("=" * 50)
            print("1. 🎛️  MANUAL Equalizer")
            print("   Control 6 frequency bands individually")
            print("   Adjust gains from 0.0 to 2.0")
            print()
            print("2. 🎤 AI VOICE Separation") 
            print("   Separate and control voice frequencies")
            print("   Uses AI models for intelligent separation")
            print()
            print("3. 🥁 AI INSTRUMENT Separation")
            print("   Separate drums, bass, melody, vocals")
            print("   Uses AI models for instrument isolation")
            print()
            print("4. 💾 Save Current Audio Files")
            print("5. ❌ Exit")
            
            choice = input("\nEnter choice (1-5): ").strip()
            
            if choice == '5':
                print("👋 Goodbye!")
                break
            elif choice == '1':
                self.current_mode = "manual"
                result = self.interactive_manual_control()
                if result == "mode_select":
                    continue
            elif choice == '2':
                self.current_mode = "human_voices"
                print("\n🎤 AI Voice Separation Mode")
                print("Processing audio with voice separation...")
                processed = self.process_audio()
                self.play_audio_comparison(self.input_signal, processed, "AI Voice Separation")
            elif choice == '3':
                self.current_mode = "musical_instruments" 
                print("\n🥁 AI Instrument Separation Mode")
                print("Processing audio with instrument separation...")
                processed = self.process_audio()
                self.play_audio_comparison(self.input_signal, processed, "AI Instrument Separation")
            elif choice == '4':
                self.save_audio_files()
            else:
                print("❌ Invalid choice. Please try again.")

# Run the demo
if __name__ == "__main__":
    try:
        demo = ManualEqualizerDemo()
        demo.run_demo()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()