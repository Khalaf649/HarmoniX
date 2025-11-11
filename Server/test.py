import torch
from demucs import pretrained
from demucs.apply import apply_model
import soundfile as sf
import numpy as np

def quick_separate():
    """Quick separation of your audio file and find peak frequencies"""
    
    YOUR_FILE = "./mixed_audio.wav"
    
    print(f"🔊 Processing: {YOUR_FILE}")
    
    # Load model
    model = pretrained.get_model('htdemucs_6s')
    model.eval()
    
    # Load audio
    audio, sr = sf.read(YOUR_FILE)
    
    # Ensure stereo
    if audio.ndim == 1:
        audio = np.stack([audio, audio], axis=1)
    
    # Normalize
    audio = audio.astype(np.float32)
    audio = audio / np.max(np.abs(audio))
    
    # Convert to tensor
    audio_tensor = torch.from_numpy(audio.T).float()
    
    # Separate
    with torch.no_grad():
        sources = apply_model(model, audio_tensor.unsqueeze(0), device='cpu')[0]
    
    # Define stems (ignore "other")
    stems = ['drums', 'vocals', 'violin', 'bass_guiter']
    stem_indices = [0, 2, 3, 5]  # corresponding indices in Demucs output
    
    for idx, name in zip(stem_indices, stems):
        # Convert to mono
        mono_audio = sources[idx].mean(dim=0).numpy()
        
        # Save audio
        sf.write(f"{name}.wav", mono_audio, sr)
        print(f"✅ Saved {name}.wav")
        
        # Compute FFT
        N = len(mono_audio)
        fft_vals = np.fft.fft(mono_audio)
        fft_freqs = np.fft.fftfreq(N, 1/sr)
        
        # Consider only positive frequencies
        positive_freqs = fft_freqs[:N//2]
        positive_magnitude = np.abs(fft_vals[:N//2])
        
        # Find peak frequency
        peak_idx = np.argmax(positive_magnitude)
        peak_freq = positive_freqs[peak_idx]
        print(f"🎵 Peak frequency for {name}: {peak_freq:.2f} Hz\n")

    print("🎉 All stems separated and peak frequencies calculated!")

# Run it
quick_separate()
