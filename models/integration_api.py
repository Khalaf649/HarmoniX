# models/integration_api.py
import sys
import os

# Fix import paths
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Use absolute imports
from model_manager import ModelManager
from performance import PerformanceComparator
from audio_utils import create_test_signal

class AIModelsAPI:
    """
    Simple API for teammates to integrate with AI models
    """
    def __init__(self):
        self.manager = ModelManager()
        self.performance = PerformanceComparator()
        print("AI Models API initialized")
    
    def switch_mode(self, mode_name):
        """
        Switch processing mode
        Returns: list of slider labels for UI
        """
        success = self.manager.set_mode(mode_name)
        if success:
            return self.manager.get_current_sliders()
        else:
            print(f"Failed to switch to {mode_name} mode")
            return []
    
    def process_audio(self, audio_data, slider_values, sample_rate=44100):
        """
        Main processing function
        audio_data: numpy array of audio
        slider_values: list of values from UI sliders (0.0 to 1.0)
        sample_rate: audio sample rate
        Returns: processed audio as numpy array
        """
        return self.manager.process_audio(audio_data, slider_values, sample_rate)
    
    def compare_with_traditional(self, original_audio, traditional_result, ai_result):
        """
        Compare AI results with traditional equalizer
        """
        return self.performance.compare_methods(original_audio, traditional_result, ai_result)
    
    def get_available_modes(self):
        """Get list of available processing modes"""
        return self.manager.get_available_modes()
    
    def get_model_status(self):
        """Get status of all models"""
        return self.manager.get_model_status()
    
    def create_test_audio(self, duration=3, sample_rate=44100):
        """Create test audio for demonstration"""
        return create_test_signal(duration, sample_rate)

# Global instance for easy access
ai_models_api = AIModelsAPI()