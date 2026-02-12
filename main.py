import os
import tempfile
import whisper
import shutil
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from transformers import pipeline

app = FastAPI()

whisper_model = None
emotion_model = None


def get_whisper():
    global whisper_model
    if whisper_model is None:
        print("Loading Whisper model...")
        whisper_model = whisper.load_model("tiny")
        print("Whisper model loaded.")
    return whisper_model


def get_emotion():
    global emotion_model
    if emotion_model is None:
        print("Loading Emotion model...")
        emotion_model = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            return_all_scores=True
        )
        print("Emotion model loaded.")
    return emotion_model


# 🔥 Load models at container startup
@app.on_event("startup")
def load_models():
    print("Container starting... loading models")
    get_whisper()
    get_emotion()
    print("All models loaded successfully")


@app.get("/")
def home():
    return {"status": "running", "message": "AI Voice Sentiment API Ready"}


@app.post("/analyze/")
async def analyze_audio(file: UploadFile = File(...)):

    ext = Path(file.filename).suffix.lower()
    if ext not in (".wav", ".mp3", ".m4a", ".webm", ".ogg"):
        raise HTTPException(status_code=400, detail="Invalid file type")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp_path = tmp.name
        file.file.seek(0)
        shutil.copyfileobj(file.file, tmp)

    try:
        model = get_whisper()

        try:
            result = model.transcribe(tmp_path, language="en", fp16=False)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

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

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return {"segments": segments}
