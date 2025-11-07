import numpy as np
import torch
from audio_utils import bandpass_filter, normalize_audio

class BaseSeparator:
    """
    Base class for all audio separators
    """
    def __init__(self, mode_name):
        self.mode_name = mode_name
        self.slider_labels = []
        self.is_loaded = False
    
    def load_model(self):
        """Load pre-trained model - to be implemented by subclasses"""
        self.is_loaded = True
    
    def separate(self, audio_data, sample_rate=44100):
        """Separate audio into components"""
        raise NotImplementedError("Subclasses must implement separate method")
    
    def get_slider_labels(self):
        return self.slider_labels
    
    def _fallback_separation(self, audio_data, sample_rate, frequency_bands):
        """Fallback frequency-based separation"""
        components = []
        for low_freq, high_freq in frequency_bands:
            component = bandpass_filter(audio_data, sample_rate, low_freq, high_freq)
            components.append(normalize_audio(component))
        return np.array(components)

class HumanVoiceSeparator(BaseSeparator):
    def __init__(self):
        super().__init__("Human Voices")
        self.slider_labels = ["Voice 1", "Voice 2", "Voice 3", "Background"]
        self.vad_model = None
        self.load_model()
    
    def load_model(self):
        """Load Silero VAD model for voice detection"""
        try:
            # This will download Silero VAD automatically
            self.vad_model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                trust_repo=True
            )
            self.utils = utils
            self.is_loaded = True
            print("Silero VAD model loaded successfully")
        except Exception as e:
            print(f"Silero VAD loading failed: {e}")
            self.vad_model = None
            self.is_loaded = False
    
    def separate(self, audio_data, sample_rate=44100):
        """Separate voices using VAD and frequency analysis"""
        if self.vad_model is not None and sample_rate == 16000:
            return self._separate_with_vad(audio_data)
        else:
            return self._fallback_separation(audio_data, sample_rate)
    
    def _separate_with_vad(self, audio_data):
        """Use VAD to detect and separate speech segments"""
        try:
            # Get speech timestamps
            get_speech_timestamps = self.utils[0]
            audio_tensor = torch.from_numpy(audio_data).float()
            
            speech_timestamps = get_speech_timestamps(
                audio_tensor, self.vad_model, sampling_rate=16000
            )
            
            # Create voice components based on detected speech
            components = self._create_voice_components(audio_data, speech_timestamps)
            return components
            
        except Exception as e:
            print(f"VAD separation failed: {e}, using fallback")
            return self._fallback_separation(audio_data, 16000)
    
    def _create_voice_components(self, audio_data, speech_timestamps):
        """Create separate components from speech timestamps"""
        components = []
        
        if len(speech_timestamps) >= 3:
            # Use actual speech segments
            for i in range(min(3, len(speech_timestamps))):
                start = speech_timestamps[i]['start']
                end = speech_timestamps[i]['end']
                component = np.zeros_like(audio_data)
                component[start:end] = audio_data[start:end]
                components.append(component)
        else:
            # Not enough speech segments, use frequency bands
            voice_bands = [(80, 300), (300, 800), (800, 2000)]
            for low_freq, high_freq in voice_bands:
                component = bandpass_filter(audio_data, 16000, low_freq, high_freq)
                components.append(component)
        
        # Add background component
        if len(components) < 4:
            background = audio_data - sum(components[:3])
            components.append(background)
        
        # Ensure we have exactly 4 components
        while len(components) < 4:
            components.append(np.zeros_like(audio_data))
        
        return np.array(components[:4])
    
    def _fallback_separation(self, audio_data, sample_rate):
        """Frequency-based voice separation fallback"""
        voice_bands = [
            (80, 300),    # Low voice range
            (300, 800),   # Mid voice range  
            (800, 2000),  # High voice range
            (2000, 4000)  # Background/breathing
        ]
        return super()._fallback_separation(audio_data, sample_rate, voice_bands)

class MusicalInstrumentSeparator(BaseSeparator):
    def __init__(self):
        super().__init__("Musical Instruments")
        self.slider_labels = ["Drums", "Bass", "Melody", "Vocals"]
        self.load_model()
    
    def load_model(self):
        """Load Librosa for advanced audio analysis"""
        try:
            import librosa
            self.librosa = librosa
            self.is_loaded = True
            print("Librosa loaded successfully")
        except ImportError:
            print("Librosa not available, using fallback methods")
            self.librosa = None
            self.is_loaded = False
    
    def separate(self, audio_data, sample_rate=44100):
        """Separate instruments using spectral characteristics"""
        if self.librosa is not None:
            return self._separate_with_librosa(audio_data, sample_rate)
        else:
            return self._fallback_separation(audio_data, sample_rate)
    
    def _separate_with_librosa(self, audio_data, sample_rate):
        """Use Librosa for harmonic/percussive separation"""
        try:
            # Harmonic-percussive source separation
            harmonic, percussive = self.librosa.effects.hpss(audio_data)
            
            components = []
            
            # Percussive component (drums)
            components.append(percussive)
            
            # Separate harmonic component further by frequency
            bass_component = bandpass_filter(harmonic, sample_rate, 20, 250)
            components.append(bass_component)
            
            melody_component = bandpass_filter(harmonic, sample_rate, 250, 2000)
            components.append(melody_component)
            
            vocal_component = bandpass_filter(harmonic, sample_rate, 2000, 8000)
            components.append(vocal_component)
            
            return np.array(components)
            
        except Exception as e:
            print(f"Librosa separation failed: {e}, using fallback")
            return self._fallback_separation(audio_data, sample_rate)
    
    def _fallback_separation(self, audio_data, sample_rate):
        """Frequency-based instrument separation fallback"""
        instrument_bands = [
            (20, 100),    # Drums (low frequencies)
            (100, 300),   # Bass 
            (300, 2000),  # Melody instruments
            (2000, 8000)  # Vocals/high frequencies
        ]
        return super()._fallback_separation(audio_data, sample_rate, instrument_bands)
