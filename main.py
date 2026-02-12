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

def get_whisper():
    global whisper_model
    if whisper_model is None:
        whisper_model = whisper.load_model("tiny")
    return whisper_model

def get_emotion():
    global emotion_model
    if emotion_model is None:
        emotion_model = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            return_all_scores=True
        )
    return emotion_model

@app.get("/")
def home():
    return {"status": "running"}

@app.post("/analyze/")
async def analyze_audio(file: UploadFile = File(...)):
    # Validate
    ext = Path(file.filename).suffix.lower()
    if ext not in (".wav", ".mp3", ".m4a", ".webm", ".ogg"):
        raise HTTPException(400, "Invalid file type")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp_path = tmp.name
        shutil.copyfileobj(file.file, tmp)

    # Transcribe
    model = get_whisper()
    result = model.transcribe(tmp_path, language="en", fp16=False)

    os.unlink(tmp_path)

    segments = []
    emo = get_emotion()

    for s in result.get("segments", []):
        text = s.get("text", "").strip()
        if not text:
            continue

        outputs = emo(text)[0]
        best = max(outputs, key=lambda x: x["score"])

        segments.append({
            "start": round(s["start"], 2),
            "end": round(s["end"], 2),
            "text": text,
            "emotion": best["label"],
            "confidence": round(best["score"], 3)
        })

    return {"segments": segments}
