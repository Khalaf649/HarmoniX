import torch
from demucs import pretrained
from demucs.apply import apply_model
import soundfile as sf
import numpy as np

def rms(x):
    return np.sqrt(np.mean(x**2))

def separate_and_apply_gain():
    YOUR_FILE = "./khalaf.wav"
    print(f"🔊 Processing: {YOUR_FILE}")

    # Load model
    model = pretrained.get_model('htdemucs_6s')
    model.eval()

    # Load audio
    audio, sr = sf.read(YOUR_FILE)
    if audio.ndim == 1:
        audio = np.stack([audio, audio], axis=1)

    audio = audio.astype(np.float32)
    audio = audio / np.max(np.abs(audio))
    audio_tensor = torch.from_numpy(audio.T).float()

    # Separate
    with torch.no_grad():
        sources = apply_model(model, audio_tensor.unsqueeze(0), device='cpu')[0]

    stems = ['drums', 'vocals', 'violin', 'bass_guiter']
    stem_indices = [0, 2, 3, 5]

    # Gain values (volume multipliers)
    gains = {
        'drums': 0,
        'vocals': 1,
        'violin': 0,
        'bass_guiter': 0
    }

    final_mix = np.zeros_like(audio)

    for idx, name in zip(stem_indices, stems):
        mono_audio = sources[idx].mean(dim=0).numpy()

        # ✅ compute volume (RMS) instead of FFT
        volume = rms(mono_audio)
        print(f"🔈 Volume (RMS) for {name}: {volume:.4f}")

        sf.write(f"{name}.wav", mono_audio, sr)
        print(f"✅ Saved {name}.wav")

        gained_audio = mono_audio * gains[name]

        final_mix[:, 0] += gained_audio
        final_mix[:, 1] += gained_audio

    # Normalize mix
    max_val = np.max(np.abs(final_mix))
    if max_val > 0:
        final_mix = final_mix / max_val

    sf.write("final_mix.wav", final_mix, sr)
    print("🎉 Final mixed audio saved as final_mix.wav!")

separate_and_apply_gain()
