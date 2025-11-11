# server/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from scipy.io.wavfile import write
import os

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

