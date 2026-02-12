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


@app.on_event("startup")
def load_models():
    get_whisper()
    get_emotion()


@app.get("/")
def home():
    return {"status": "running"}


@app.post("/analyze/")
async def analyze_audio(file: UploadFile = File(...)):

    # 🔍 DEBUG START (ADD HERE)
    print("Received filename:", file.filename)
    print("Content type:", file.content_type)
    # 🔍 DEBUG END

    allowed_extensions = (".wav", ".mp3", ".m4a", ".3gp")

    filename = file.filename.lower() if file.filename else ""
    content_type = file.content_type or ""


    if not filename.endswith(allowed_extensions):
      raise HTTPException(status_code=400, detail="Invalid file type")


    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
        file.file.seek(0)
        shutil.copyfileobj(file.file, tmp)

    try:
        model = get_whisper()
        result = model.transcribe(tmp_path, language="en", fp16=False)

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
