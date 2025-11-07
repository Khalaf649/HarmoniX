import numpy as np
import time
from audio_utils import normalize_audio

class PerformanceComparator:
    """
    Compare performance between traditional equalizer and AI models
    """
    
    @staticmethod
    def calculate_snr(original, processed):
        """Signal-to-Noise Ratio"""
        if len(original) != len(processed):
            min_len = min(len(original), len(processed))
            original = original[:min_len]
            processed = processed[:min_len]
        
        noise = original - processed
        signal_power = np.mean(original**2)
        noise_power = np.mean(noise**2)
        
        if noise_power == 0:
            return float('inf')
        return 10 * np.log10(signal_power / noise_power)
    
    @staticmethod
    def calculate_spectral_similarity(original, processed):
        """Compare frequency spectrum similarity"""
        orig_fft = np.abs(np.fft.fft(original))
        proc_fft = np.abs(np.fft.fft(processed))
        
        # Normalize
        orig_fft = orig_fft / np.max(orig_fft)
        proc_fft = proc_fft / np.max(proc_fft)
        
        # Calculate correlation
        correlation = np.corrcoef(orig_fft, proc_fft)[0, 1]
        return max(0, correlation)  # Ensure non-negative
    
    @staticmethod
    def compare_methods(original_audio, traditional_result, ai_result):
        """
        Comprehensive comparison between traditional and AI approaches
        """
        comparison = {
            'traditional_snr': PerformanceComparator.calculate_snr(original_audio, traditional_result),
            'ai_snr': PerformanceComparator.calculate_snr(original_audio, ai_result),
            'spectral_similarity_traditional': PerformanceComparator.calculate_spectral_similarity(original_audio, traditional_result),
            'spectral_similarity_ai': PerformanceComparator.calculate_spectral_similarity(original_audio, ai_result),
        }
        
        # Determine preference
        snr_preference = 'AI' if comparison['ai_snr'] > comparison['traditional_snr'] else 'Traditional'
        spectral_preference = 'AI' if comparison['spectral_similarity_ai'] > comparison['spectral_similarity_traditional'] else 'Traditional'
        
        comparison['snr_preference'] = snr_preference
        comparison['spectral_preference'] = spectral_preference
        comparison['overall_preference'] = 'AI' if (snr_preference == 'AI' and spectral_preference == 'AI') else 'Traditional'
        
        return comparison
    
    @staticmethod
    def measure_processing_time(processing_function, *args, iterations=5):
        """Measure average execution time"""
        times = []
        result = None
        
        for i in range(iterations):
            start_time = time.time()
            result = processing_function(*args)
            end_time = time.time()
            times.append(end_time - start_time)
        
        return result, np.mean(times), np.std(times)
