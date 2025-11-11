# server/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from scipy.io.wavfile import write
import os
import requests  # <-- make sure to import this
from demucs import pretrained
from demucs.apply import apply_model
import torch

app = FastAPI()

# Allow CORS so client can fetch
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class EQRequest(BaseModel):
    samples: list[float]
    sampleRate: int
    mode: str

class FFTRequest(BaseModel):
    samples: list[float]
    fs: float





def calculate_fft(request: FFTRequest):
    try:
        CXX_FFT_URL = "http://localhost:8080/calculatefft"  # Your C++ server URL
        # Forward request to the C++ endpoint using requests
        response = requests.post(
            CXX_FFT_URL,
            json={"samples": request.samples, "fs": request.fs},
            timeout=10
        )
        
        # Raise exception if C++ server returned error
        response.raise_for_status()
        
        return response.json()  # Return C++ response directly

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"C++ server error: {str(e)}")

@app.post("/saveEQ")
def save_eq(req: EQRequest):
    
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

class AudioRequest(BaseModel):
    samples: list[float]  # Mono audio
    fs: float              # Sampling rate


@app.post("/separate_audio")
def separate_audio(req: AudioRequest):
    try:
        # Load Demucs model
        model = pretrained.get_model('htdemucs_6s')
        model.eval()
        
        # Convert input to NumPy array
        audio = np.array(req.samples, dtype=np.float32)
        
        # Make stereo if necessary
        if audio.ndim == 1:
            audio = np.stack([audio, audio], axis=1)
        
        # Normalize
        audio = audio / np.max(np.abs(audio))
        
        # Convert to tensor [channels, samples]
        audio_tensor = torch.from_numpy(audio.T).float()
        
        # Separate stems
        with torch.no_grad():
            sources = apply_model(model, audio_tensor.unsqueeze(0), device='cpu')[0]
        
        # Define stems and their indices
        stems = ['drums', 'vocals', 'violin', 'bass_guitar']
        stem_indices = [0, 2, 3, 5]
        
        result = []
        for idx, name in zip(stem_indices, stems):
            # Convert to mono
            mono_audio = sources[idx].mean(dim=0).numpy()
            
            # Call your existing FFT method
            fft_data = calculate_fft(FFTRequest(samples=mono_audio.tolist(), fs=req.fs))
            
            # Find dominant frequency (peak)
            magnitudes = np.array(fft_data["magnitudes"])
            frequencies = np.array(fft_data["frequencies"])
            peak_idx = np.argmax(magnitudes)
            dominant_freq = float(frequencies[peak_idx])
            
            result.append({
                "stem": name,
                "dominantFrequency": dominant_freq
            })
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
