import numpy as np
import scipy.signal as signal

def bandpass_filter(audio_data, sample_rate, low_freq, high_freq):
    """
    Simple bandpass filter using FFT
    """
    # FFT
    fft_data = np.fft.fft(audio_data)
    frequencies = np.fft.fftfreq(len(audio_data), 1/sample_rate)
    
    # Create frequency mask
    mask = (np.abs(frequencies) >= low_freq) & (np.abs(frequencies) <= high_freq)
    fft_data[~mask] = 0
    
    # Inverse FFT
    filtered = np.real(np.fft.ifft(fft_data))
    return filtered

def normalize_audio(audio_data):
    """
    Normalize audio to [-1, 1] range
    """
    max_val = np.max(np.abs(audio_data))
    if max_val > 0:
        return audio_data / max_val
    return audio_data

def resample_audio(audio_data, original_rate, target_rate):
    """
    Resample audio to target rate
    """
    if original_rate == target_rate:
        return audio_data
    
    num_samples = int(len(audio_data) * target_rate / original_rate)
    return signal.resample(audio_data, num_samples)

def mix_sources(sources, weights):
    """
    Mix separated sources with given weights
    """
    if len(sources) == 0:
        return np.array([])
    
    mixed = np.zeros_like(sources[0])
    for source, weight in zip(sources, weights):
        mixed += source * weight
    return mixed

def create_test_signal(duration=3, sample_rate=44100):
    """
    Create a synthetic test signal with multiple frequencies
    """
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Multiple frequency components
    frequencies = [100, 440, 1000, 2000, 5000]  # Hz
    signal_components = [np.sin(2 * np.pi * f * t) for f in frequencies]
    
    # Combine with different amplitudes
    amplitudes = [0.3, 0.5, 0.4, 0.2, 0.1]
    combined = sum(amp * comp for amp, comp in zip(amplitudes, signal_components))
    
    return normalize_audio(combined)
