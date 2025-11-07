# teammates_usage.py
from models.integration_api import AIModelsAPI

class EqualizerApp:
    def __init__(self):
        self.ai_api = AIModelsAPI()
        self.current_sliders = []
        self.current_values = [1.0, 1.0, 1.0, 1.0]  # Default all to 100%
    
    def on_mode_selected(self, mode_name):
        """Call this when user selects a mode"""
        slider_labels = self.ai_api.switch_mode(mode_name)
        self.current_sliders = slider_labels
        self.current_values = [1.0] * len(slider_labels)  # Reset to 100%
        return slider_labels
    
    def on_slider_moved(self, slider_index, value_percent):
        """Call this when slider moves (0-100%)"""
        processing_value = value_percent / 100.0
        self.current_values[slider_index] = processing_value
        
        # Process audio with current slider values
        output_audio = self.ai_api.process_audio(
            self.input_audio, 
            self.current_values,
            sample_rate=44100
        )
        return output_audio
    
    def load_audio(self, audio_data, sample_rate=44100):
        """Call this when audio is loaded"""
        self.input_audio = audio_data
        self.sample_rate = sample_rate