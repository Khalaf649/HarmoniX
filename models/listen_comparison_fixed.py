# listen_comparison_fixed.py
import numpy as np
import matplotlib.pyplot as plt
from integration_api import ai_models_api
import time
from scipy.io import wavfile
import simpleaudio as sa  # Much simpler audio playback

def play_audio_comparison():
    """Play input vs output audio for comparison - FIXED VERSION"""
    
    # Initialize AI API
    ai_api = ai_models_api
    
    print("🎧 AUDIO COMPARISON - LISTEN TO THE DIFFERENCE")
    print("=" * 60)
    
    # Create a more musical test signal
    def create_musical_test_signal(duration=4, sample_rate=44100):
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create a simple melody with different instruments
        # Kick drum (low frequency pulses)
        kick_times = np.sin(2 * np.pi * 2 * t) > 0  # 2 Hz rhythm
        kick = np.sin(2 * np.pi * 80 * t) * kick_times * 0.4
        
        # Bass line (A2 - 110Hz)
        bass = np.sin(2 * np.pi * 110 * t) * 0.3
        
        # Voice (A4 - 440Hz)
        voice = np.sin(2 * np.pi * 440 * t) * 0.5
        
        # Guitar (E5 - 660Hz)
        guitar = np.sin(2 * np.pi * 660 * t) * 0.4
        
        # Hi-hat (noise-based)
        hihat = np.random.normal(0, 0.1, len(t)) * (np.sin(2 * np.pi * 8 * t) > 0) * 0.2
        
        # Apply envelope to avoid clicks
        envelope = np.ones_like(t)
        envelope[:len(t)//8] = np.linspace(0, 1, len(t)//8)  # Fade in
        envelope[7*len(t)//8:] = np.linspace(1, 0, len(t)//8)  # Fade out
        
        combined = (kick + bass + voice + guitar + hihat) * envelope
        return combined / np.max(np.abs(combined))
    
    # Create test signal
    input_signal = create_musical_test_signal(duration=4)
    sample_rate = 44100
    
    print(f"🎵 Created test signal: {len(input_signal)/sample_rate:.1f} seconds")
    print("   Contains: kick drum, bass, voice, guitar, hi-hat")
    
    # Define listening scenarios
    scenarios = [
        {
            'name': '🎤 Voice Isolation',
            'mode': 'human_voices',
            'sliders': [0.8, 1.2, 1.5, 0.1],
            'description': 'Boost voice frequencies, reduce background'
        },
        {
            'name': '🥁 Drum & Bass Boost',
            'mode': 'musical_instruments',
            'sliders': [1.8, 1.5, 0.3, 0.2],
            'description': 'Boost drums and bass, reduce melody/vocals'
        },
        {
            'name': '🎸 Melody Focus',
            'mode': 'musical_instruments', 
            'sliders': [0.3, 0.5, 1.8, 1.2],
            'description': 'Boost melody and vocals, reduce rhythm'
        },
        {
            'name': '🔇 Low Cut',
            'mode': 'human_voices',
            'sliders': [0.0, 0.1, 1.0, 1.0],
            'description': 'Remove low frequencies (high-pass)'
        }
    ]
    
    def play_audio_simple(audio, sample_rate=44100):
        """Play audio using simpleaudio (most reliable)"""
        try:
            # Convert to 16-bit PCM
            audio_16bit = (audio * 32767).astype(np.int16)
            play_obj = sa.play_buffer(audio_16bit, 1, 2, sample_rate)
            return play_obj
        except Exception as e:
            print(f"❌ Could not play audio: {e}")
            print("💡 Audio will be saved to files instead")
            return None
    
    def visualize_audio_comparison(original, processed, title):
        """Show comparison visualization"""
        plt.figure(figsize=(15, 10))
        
        # Time domain comparison
        plt.subplot(3, 1, 1)
        time_axis = np.linspace(0, len(original)/sample_rate, len(original))
        plt.plot(time_axis, original, 'b-', alpha=0.7, label='Original', linewidth=1)
        plt.plot(time_axis, processed, 'r-', alpha=0.8, label='Processed', linewidth=1)
        plt.title(f'{title}\nTime Domain Comparison')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Frequency spectrum comparison
        plt.subplot(3, 1, 2)
        fft_orig = np.abs(np.fft.fft(original))
        fft_proc = np.abs(np.fft.fft(processed))
        freqs = np.fft.fftfreq(len(original), 1/sample_rate)
        positive_idx = (freqs > 0) & (freqs < 5000)
        
        plt.semilogy(freqs[positive_idx], fft_orig[positive_idx], 'b-', alpha=0.6, label='Original', linewidth=1)
        plt.semilogy(freqs[positive_idx], fft_proc[positive_idx], 'r-', alpha=0.8, label='Processed', linewidth=1)
        plt.title('Frequency Spectrum Comparison')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Magnitude (log)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Difference
        plt.subplot(3, 1, 3)
        difference = processed - original
        plt.plot(time_axis, difference, 'g-', alpha=0.8, linewidth=1)
        plt.title('Difference (Processed - Original)')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude Difference')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def play_comparison_sequence(original, processed, scenario_name):
        """Play original and processed with visualization"""
        print(f"\n{'='*50}")
        print(f"🎵 COMPARISON: {scenario_name}")
        print(f"{'='*50}")
        
        # Show visualization first
        visualize_audio_comparison(original, processed, scenario_name)
        
        # Play original
        print("\n▶️  Playing ORIGINAL signal...")
        play_obj = play_audio_simple(original, sample_rate)
        if play_obj:
            play_obj.wait_done()
        
        print("⏸️  Pausing 2 seconds...")
        time.sleep(2)
        
        # Play processed
        print("▶️  Playing PROCESSED signal...")
        play_obj = play_audio_simple(processed, sample_rate)
        if play_obj:
            play_obj.wait_done()
        
        # Calculate and show metrics
        difference = processed - original
        change_percent = (np.std(difference) / np.std(original)) * 100
        
        print(f"\n📊 Quick Analysis:")
        print(f"   Signal change: {change_percent:.1f}%")
        print(f"   RMS Original: {np.sqrt(np.mean(original**2)):.3f}")
        print(f"   RMS Processed: {np.sqrt(np.mean(processed**2)):.3f}")
        print(f"   Volume change: {((np.sqrt(np.mean(processed**2)) - np.sqrt(np.mean(original**2))) / np.sqrt(np.mean(original**2)) * 100):+.1f}%")
    
    # Main listening loop
    while True:
        print("\n" + "="*60)
        print("🎧 CHOOSE A SCENARIO TO LISTEN:")
        print("="*60)
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"{i}. {scenario['name']}")
            print(f"   {scenario['description']}")
            print(f"   Mode: {scenario['mode']}, Sliders: {scenario['sliders']}")
            print()
        
        print("5. 🎵 Custom scenario")
        print("6. 💾 Save audio files only")
        print("7. ❌ Exit")
        
        try:
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == '7':
                print("👋 Goodbye!")
                break
            elif choice == '6':
                save_audio_files_only()
                continue
            elif choice == '5':
                # Custom scenario
                print("\n🎛️  Create custom scenario:")
                mode = input("Mode (human_voices/musical_instruments): ").strip()
                sliders_input = input("Slider values (comma-separated, 0.0-2.0): ").strip()
                sliders = [float(x.strip()) for x in sliders_input.split(',')]
                name = input("Scenario name: ").strip()
                
                custom_scenario = {
                    'name': f"🎛️  {name}",
                    'mode': mode,
                    'sliders': sliders,
                    'description': 'Custom settings'
                }
                
                ai_api.switch_mode(custom_scenario['mode'])
                output_signal = ai_api.process_audio(input_signal, custom_scenario['sliders'], sample_rate)
                play_comparison_sequence(input_signal, output_signal, custom_scenario['name'])
                
            elif choice in ['1', '2', '3', '4']:
                scenario = scenarios[int(choice) - 1]
                
                # Process audio
                ai_api.switch_mode(scenario['mode'])
                output_signal = ai_api.process_audio(input_signal, scenario['sliders'], sample_rate)
                
                # Play comparison
                play_comparison_sequence(input_signal, output_signal, scenario['name'])
                
            else:
                print("❌ Invalid choice. Please try again.")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again.")
        
        # Ask to continue
        continue_choice = input("\n🎧 Listen to another scenario? (y/n): ").strip().lower()
        if continue_choice != 'y':
            print("👋 Goodbye!")
            break

def save_audio_files_only():
    """Save audio examples for listening in any media player"""
    print("\n💾 SAVING AUDIO FILES FOR OFFLINE LISTENING")
    print("=" * 50)
    
    ai_api = ai_models_api
    sample_rate = 44100
    
    # Create a good test signal
    def create_test_signal(duration=6, sample_rate=44100):
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Multiple frequency components
        bass = np.sin(2 * np.pi * 100 * t) * 0.4
        voice = np.sin(2 * np.pi * 440 * t) * 0.6
        melody = np.sin(2 * np.pi * 1000 * t) * 0.5
        highs = np.sin(2 * np.pi * 3000 * t) * 0.3
        
        # Add some rhythm
        rhythm = np.sin(2 * np.pi * 4 * t) > 0
        combined = (bass + voice * 0.7 + melody + highs * 0.5) * (0.7 + 0.3 * rhythm)
        
        # Fade in/out
        envelope = np.ones_like(t)
        fade_samples = int(0.1 * sample_rate)  # 100ms fade
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        
        return (combined * envelope) / np.max(np.abs(combined))
    
    input_signal = create_test_signal(duration=6)
    
    # Save original
    wavfile.write('00_ORIGINAL_SIGNAL.wav', sample_rate, (input_signal * 32767).astype(np.int16))
    print("✅ Saved: 00_ORIGINAL_SIGNAL.wav")
    
    # Save processed examples with descriptive names
    examples = [
        ('01_VOICE_ISOLATED.wav', 'human_voices', [1.2, 1.0, 0.8, 0.1], "Boosted voice frequencies"),
        ('02_BASS_BOOSTED.wav', 'musical_instruments', [0.5, 2.0, 0.7, 0.5], "Enhanced bass, reduced highs"),
        ('03_DRUMS_FOCUS.wav', 'musical_instruments', [2.0, 1.5, 0.3, 0.2], "Emphasized drums and bass"),
        ('04_MELODY_FOCUS.wav', 'musical_instruments', [0.3, 0.5, 2.0, 1.5], "Emphasized melody and vocals"),
        ('05_HIGH_PASS.wav', 'human_voices', [0.0, 0.1, 1.0, 1.0], "Removed low frequencies"),
        ('06_VOICE_REDUCED.wav', 'human_voices', [0.3, 0.5, 0.2, 1.5], "Reduced voice, boosted background"),
    ]
    
    for filename, mode, sliders, description in examples:
        ai_api.switch_mode(mode)
        output = ai_api.process_audio(input_signal, sliders, sample_rate)
        wavfile.write(filename, sample_rate, (output * 32767).astype(np.int16))
        print(f"✅ Saved: {filename} - {description}")
    
    print("\n" + "=" * 50)
    print("🎧 AUDIO FILES SAVED SUCCESSFULLY!")
    print("📁 Files are in: /media/sandy/Work2/task4_DSP/models/")
    print("\nYou can now:")
    print("1. Open these files in any media player (VLC, Windows Media Player, etc.)")
    print("2. Compare original vs processed versions")
    print("3. Hear the differences clearly!")
    print("\nRecommended listening order:")
    print("  1. Play 00_ORIGINAL_SIGNAL.wav")
    print("  2. Play any processed file to hear the difference")
    print("  3. Compare different processing effects")

if __name__ == "__main__":
    try:
        import simpleaudio as sa
        print("✅ simpleaudio is available - audio playback enabled")
        
        # Ask user what they want to do
        print("\n🎧 CHOOSE PLAYBACK MODE:")
        print("1. 🎵 Listen with visualization (requires simpleaudio)")
        print("2. 💾 Save audio files for offline listening (recommended)")
        print("3. 🚀 Both")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice in ['1', '3']:
            play_audio_comparison()
        if choice in ['2', '3']:
            save_audio_files_only()
            
    except ImportError:
        print("❌ simpleaudio not installed - cannot play audio live")
        print("📦 You can install it with: pip install simpleaudio")
        print("🔧 For now, saving audio files instead...")
        save_audio_files_only()