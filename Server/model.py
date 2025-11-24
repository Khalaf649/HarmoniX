# server/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from scipy.io.wavfile import write
import os
import requests  # <-- make sure to import this
import httpx
from demucs import pretrained
from demucs.apply import apply_model
import torch
from typing import List

app = FastAPI()

# Allow CORS so client can fetch
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class EQRequestSave(BaseModel):
    samples: list[float]
    sampleRate: int
    mode: str

# ---------- Request Models ----------
class FFTRequest(BaseModel):
    samples: List[float]
    fs: float


class EQSlider(BaseModel):
    low: float
    high: float
    value: float


class EQRequest(BaseModel):
    samples: List[float]
    fs: float
    sliders: List[EQSlider]


class SpectrogramRequest(BaseModel):
    samples: List[float]
    fs: float


# ---------- Utils ----------
def next_power_of_2(n):
    return 1 << (n - 1).bit_length()


# ===============================================================
#   1️⃣ /calculatefft
# ===============================================================
@app.post("/calculatefft")
def calculate_fft(req: FFTRequest):

    samples = np.array(req.samples, dtype=float)
    fs = req.fs

    n_original = len(samples)
    n = next_power_of_2(n_original)

    # Zero-pad
    data = np.zeros(n, dtype=complex)
    data[:n_original] = samples

    # FFT
    fft_data = np.fft.fft(data)

    # Frequencies & magnitudes
    freqs = np.fft.fftfreq(n, d=1/fs)[: n//2 + 1]
    mags = np.abs(fft_data[: n//2 + 1])

    return {
        "frequencies": freqs.tolist(),
        "magnitudes": mags.tolist()
    }


# ===============================================================
#   2️⃣ /applyEqualizer
# ===============================================================
@app.post("/applyEqualizer")
def apply_equalizer(req: EQRequest):
    samples = np.array(req.samples, dtype=float)
    fs = req.fs

    n_original = len(samples)
    n = next_power_of_2(n_original)

    # Zero-pad
    data = np.zeros(n)
    data[:n_original] = samples

    # FFT
    fft_data = np.fft.fft(data)

    # Frequency array
    freqs = np.fft.fftfreq(n, 1/fs)

    # Apply gain to selected bands
    for band in req.sliders:
        # Positive frequency mask
        mask = (freqs >= band.low) & (freqs <= band.high)
        fft_data[mask] *= band.value

        # Negative frequency mask (mirrored)
        neg_mask = (freqs <= -band.low) & (freqs >= -band.high)
        fft_data[neg_mask] *= band.value

    # BEFORE inverse FFT → for visualization
    vis_freqs = freqs[: n//2 + 1]
    vis_mags = np.abs(fft_data[: n//2 + 1])

    # Inverse FFT → time domain
    output = np.fft.ifft(fft_data).real[:n_original]

    return {
        "samples": output.tolist(),
        "frequencies": vis_freqs.tolist(),
        "magnitudes": vis_mags.tolist()
    }


# ===============================================================
#   3️⃣ /spectrogram
# ===============================================================
@app.post("/spectrogram")
def spectrogram(req: SpectrogramRequest):

    samples = np.array(req.samples)
    fs = req.fs

    window_size = 2048
    hop_size = window_size // 4

    nfft = window_size
    num_freq_bins = nfft // 2 + 1

    # Window function
    window = np.hanning(window_size)

    frames = []
    pos = 0

    # Sliding window
    while pos + window_size <= len(samples):
        frame = samples[pos : pos + window_size] * window
        fft_vals = np.fft.rfft(frame)
        frames.append(np.abs(fft_vals))
        pos += hop_size

    magnitude_frames = np.array(frames)  # shape: [time][freq]

    # Axes
    num_frames = magnitude_frames.shape[0]

    x = np.arange(num_frames) * hop_size / fs                # time
    y = np.arange(num_freq_bins) * fs / nfft                # freq
    z = magnitude_frames.T                                  # freq × time

    return {
        "x": x.tolist(),
        "y": y.tolist(),
        "z": z.tolist()
    }




@app.post("/saveEQ")
def save_eq(req: EQRequestSave):
    
    try:
        samples = np.array(req.samples, dtype=np.float32)
        sample_rate = req.sampleRate
        mode = req.mode

        # Scale to int16 for WAV
        samples_int16 = np.int16(np.clip(samples, -1, 1) * 32767)

        # Prepare output path
        public_dir = os.path.abspath(os.path.join(os.getcwd(), "..", "client", "public"))
        os.makedirs(public_dir, exist_ok=True)
        output_filename = f"{mode}_output.wav"
        output_path = os.path.join(public_dir, output_filename)

        # Save WAV
        write(output_path, sample_rate, samples_int16)

        # Return relative path from project root
        relative_path = os.path.join("public", output_filename).replace("\\", "/")
        return {"url": relative_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
















# class AudioRequest(BaseModel):
#     samples: list[float]  # Mono audio
#     fs: float              # Sampling rate

# model = pretrained.get_model('htdemucs_6s')
# model.eval()

# # Define stems and their indices in the Demucs output
# stems = ['drums', 'vocals', 'violin', 'bass_guiter']
# stem_indices = [0, 2, 3, 5]

# # URL of your C++ FFT server
# FFT_SERVER_URL = "http://localhost:8080/calculatefft"  # replace with your server URL
# @app.post("/separate_audio")
# async def separate_audio(audio: AudioRequest):
#     try:
#         samples = np.array(audio.samples, dtype=np.float32)
#         sr = audio.fs
        
#         if samples.ndim == 1:
#             samples = np.stack([samples, samples], axis=1)
        
#         samples = samples / np.max(np.abs(samples))
#         audio_tensor = torch.from_numpy(samples.T).float()
        
#         # Separate stems
#         with torch.no_grad():
#             sources = apply_model(model, audio_tensor.unsqueeze(0), device='cpu')[0]
        
#         result = {}
        
#         async with httpx.AsyncClient() as client:
#             for idx, name in zip(stem_indices, stems):
#                 mono_audio = sources[idx].mean(dim=0).numpy()
                
#                 fft_payload = {"samples": mono_audio.tolist(), "fs": sr}
#                 response = await client.post(FFT_SERVER_URL, json=fft_payload)
                
#                 if response.status_code == 200:
#                     fft_data = response.json()
#                     frequencies = np.array(fft_data.get("frequencies", []))
#                     magnitudes = np.array(fft_data.get("magnitudes", []))
#                     peak_freq = float(frequencies[np.argmax(magnitudes)]) if len(frequencies) > 0 else None
#                 else:
#                     peak_freq = None
                
#                 result[name] = peak_freq
        
#         return result

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))