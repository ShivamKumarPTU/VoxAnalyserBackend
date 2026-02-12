import os
import tempfile
import whisper
import shutil
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException

from transformers import pipeline

app = FastAPI()

# Globals
whisper_model = None
emotion_model = None

# It's good practice to load models once globally.
# For Cloud Run, these will be loaded when the container starts.
# If loading takes too long, consider increasing the startup timeout for the Cloud Run service.
def get_whisper():
    global whisper_model
    if whisper_model is None:
        print("Loading Whisper model...") # Add logging to see when models are loaded
        whisper_model = whisper.load_model("tiny")
        print("Whisper model loaded.")
    return whisper_model

def get_emotion():
    global emotion_model
    if emotion_model is None:
        print("Loading emotion model...") # Add logging
        emotion_model = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            return_all_scores=True
        )
        print("Emotion model loaded.")
    return emotion_model

@app.get("/")
def home():
    # Trigger model loading on first request if not already loaded,
    # or ensure they are loaded during container startup if accessed here.
    # A simple health check might not need to load models, but if it's
    # part of the startup probe, it will ensure models are ready.
    get_whisper()
    get_emotion()
    return {"status": "running", "message": "Models are loaded and ready."}

@app.post("/analyze/")
async def analyze_audio(file: UploadFile = File(...)):
    # Validate
    ext = Path(file.filename).suffix.lower()
    if ext not in (".wav", ".mp3", ".m4a", ".webm", ".ogg"):
        raise HTTPException(400, "Invalid file type")

    # Use tempfile.NamedTemporaryFile for secure temporary file creation
    # and ensure it's cleaned up.
    # Cloud Run's /tmp directory is an in-memory filesystem.
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp_path = tmp.name
        # Ensure file pointer is at the beginning before copying
        file.file.seek(0)
        shutil.copyfileobj(file.file, tmp)

    try:
        # Transcribe
        model = get_whisper()
        # fp16=False is crucial for CPU-only environments like default Cloud Run
        result = model.transcribe(tmp_path, language="en", fp16=False)

        segments = []
        emo = get_emotion()

        for s in result.get("segments", []):
            text = s.get("text", "").strip()
            if not text:
                continue

            # Hugging Face pipeline returns a list of lists, take the first inner list
            outputs = emo(text)[0]
            best = max(outputs, key=lambda x: x["score"])

            segments.append({
                "start": round(s["start"], 2),
                "end": round(s["end"], 2),
                "text": text,
                "emotion": best["label"],
                "confidence": round(best["score"], 3)
            })
    finally:
        # Ensure the temporary file is deleted even if an error occurs
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return {"segments": segments}

# No if __name__ == "__main__": block needed here, as Uvicorn will be started by the Dockerfile CMD.
