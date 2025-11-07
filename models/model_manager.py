from ai_models import HumanVoiceSeparator, MusicalInstrumentSeparator
from audio_utils import mix_sources

class ModelManager:
    """
    Manages AI model lifecycle and audio processing
    """
    def __init__(self):
        self.models = {
            "human_voices": HumanVoiceSeparator(),
            "musical_instruments": MusicalInstrumentSeparator()
        }
        self.current_model = None
        self.current_mode = None
    
    def set_mode(self, mode_name):
        """
        Switch between different processing modes
        Returns: True if successful, False otherwise
        """
        if mode_name in self.models:
            self.current_model = self.models[mode_name]
            self.current_mode = mode_name
            print(f"Switched to {mode_name} mode")
            return True
        else:
            print(f"Unknown mode: {mode_name}")
            return False
    
    def process_audio(self, audio_data, slider_values, sample_rate=44100):
        """
        Process audio using current model and slider values
        """
        if self.current_model is None:
            print("No model selected. Returning original audio.")
            return audio_data
        
        try:
            # Separate audio into components
            separated_components = self.current_model.separate(audio_data, sample_rate)
            
            # Apply slider values to mix components
            if len(separated_components) > 0:
                # Ensure we have enough slider values
                num_components = min(len(separated_components), len(slider_values))
                adjusted_sliders = slider_values[:num_components]
                
                # Mix components according to slider values
                output_audio = mix_sources(
                    separated_components[:num_components], 
                    adjusted_sliders
                )
                
                return output_audio
            else:
                print("No components separated. Returning original audio.")
                return audio_data
                
        except Exception as e:
            print(f"Audio processing failed: {e}")
            return audio_data
    
    def get_current_sliders(self):
        """Get slider labels for current mode"""
        if self.current_model:
            return self.current_model.get_slider_labels()
        return []
    
    def get_available_modes(self):
        """Get list of available processing modes"""
        return list(self.models.keys())
    
    def get_model_status(self):
        """Get status of all models"""
        status = {}
        for mode_name, model in self.models.items():
            status[mode_name] = {
                'loaded': model.is_loaded,
                'slider_labels': model.get_slider_labels()
            }
        return status
